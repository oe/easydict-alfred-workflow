"""
Easydict Alfred Workflow - Youdao Dictionary Service

Free Youdao web dictionary API.
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from .base import TranslationService, TranslationResult, ServiceType


@dataclass
class DictionaryEntry:
    """Dictionary lookup result."""
    word: str
    phonetic_us: str = ""
    phonetic_uk: str = ""
    definitions: List[str] = field(default_factory=list)
    web_translations: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    forms: Dict[str, str] = field(default_factory=dict)
    is_word: bool = False


class YoudaoDictService(TranslationService):
    """Youdao web dictionary service."""
    
    name = "Youdao Dictionary"
    service_type = ServiceType.YOUDAO_DICT
    icon = "icons/youdao.png"
    requires_api_key = False
    
    # Supported language pairs: zh <-> en, ja, ko, fr
    SUPPORTED_LANGS = {"en", "ja", "ko", "fr", "zh-CHS"}
    
    def _get_dict_lang_code(self, from_lang: str, to_lang: str) -> Optional[str]:
        """Get Youdao dictionary language identifier."""
        # Dictionary query language format
        if from_lang == "en" or to_lang == "en":
            return "en"
        elif from_lang == "ja" or to_lang == "ja":
            return "ja"
        elif from_lang == "ko" or to_lang == "ko":
            return "ko"
        elif from_lang == "fr" or to_lang == "fr":
            return "fr"
        return None
    
    def lookup(self, word: str, from_lang: str = "auto", to_lang: str = "zh-CHS") -> Optional[DictionaryEntry]:
        """
        Look up a word in Youdao dictionary.
        
        Returns DictionaryEntry or None if not found.
        """
        lang_code = self._get_dict_lang_code(from_lang, to_lang)
        if not lang_code:
            lang_code = "en"  # Default to English
        
        try:
            # Build URL
            dicts = [["web_trans", "ec", "ce", "newhh", "baike", "wikipedia_digest"]]
            params = urllib.parse.urlencode({
                "q": word,
                "le": lang_code,
                "dicts": json.dumps({"count": 99, "dicts": dicts}),
            })
            url = f"https://dict.youdao.com/jsonapi?{params}"
            
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            return self._parse_response(word, data)
            
        except Exception as e:
            return None
    
    def _parse_response(self, word: str, data: Dict[str, Any]) -> Optional[DictionaryEntry]:
        """Parse Youdao dictionary API response."""
        entry = DictionaryEntry(word=word)
        
        # Parse EC (English-Chinese) dictionary
        ec = data.get("ec", {})
        if ec:
            word_data = ec.get("word", [{}])
            if word_data:
                word_info = word_data[0] if isinstance(word_data, list) else word_data
                
                # Phonetic
                entry.phonetic_us = word_info.get("usphone", "")
                entry.phonetic_uk = word_info.get("ukphone", "")
                
                # Translations
                trs = word_info.get("trs", [])
                for tr in trs:
                    if "tr" in tr:
                        for t in tr["tr"]:
                            if "l" in t and "i" in t["l"]:
                                entry.definitions.append(t["l"]["i"][0])
                
                # Word forms
                wfs = word_info.get("wfs", [])
                for wf in wfs:
                    if "wf" in wf:
                        name = wf["wf"].get("name", "")
                        value = wf["wf"].get("value", "")
                        if name and value:
                            entry.forms[name] = value
                
                if entry.definitions:
                    entry.is_word = True
        
        # Parse CE (Chinese-English) dictionary
        ce = data.get("ce", {})
        if ce and not entry.definitions:
            word_data = ce.get("word", [{}])
            if word_data:
                word_info = word_data[0] if isinstance(word_data, list) else word_data
                
                # Phonetic
                if not entry.phonetic_us and not entry.phonetic_uk:
                     entry.phonetic_us = word_info.get("phone", "")
                
                trs = word_info.get("trs", [])
                for tr in trs:
                    # Parse confusing structure: tr -> l -> i -> [str, dict]
                    items = tr.get("tr", [{}])[0].get("l", {}).get("i", [])
                    tran = tr.get("tr", [{}])[0].get("l", {}).get("#tran", "")
                    
                    definition = ""
                    if isinstance(items, list):
                        # Join all text parts in the list to form the full phrase/sentence
                        for item in items:
                            if isinstance(item, dict) and "#text" in item:
                                definition += item["#text"]
                            elif isinstance(item, str):
                                definition += item
                    elif isinstance(items, dict) and "#text" in items:
                         definition = items["#text"]
                    
                    if definition.strip():
                        def_str = definition.strip()
                        if tran:
                            # Append translation explanation if available
                            def_str += f"  {tran}"
                        entry.definitions.append(def_str)

        # Parse Baike (Encyclopedia)
        baike = data.get("baike", {})
        if baike:
            summarys = baike.get("summarys", [])
            if summarys:
                 summary = summarys[0].get("summary", "")
                 if summary:
                     # Calculate snippet safely
                     snippet = (summary[:50] + '...') if len(summary) > 50 else summary
                     entry.examples.append(f"[Baike] {snippet}")
        
        # Parse web translations
        web_trans = data.get("web_trans", {})
        if web_trans:
            web_items = web_trans.get("web-translation", [])
            for item in web_items[:3]:  # Limit to 3
                trans = item.get("trans", [])
                for t in trans:
                    value = t.get("value", "")
                    if value and value not in entry.web_translations:
                        entry.web_translations.append(value)
        
        # Parse simple translation (fallback)
        simple = data.get("simple", {})
        if simple and not entry.definitions:
            word_data = simple.get("word", [{}])
            if word_data:
                word_info = word_data[0] if isinstance(word_data, list) else word_data
                if "return-phrase" in word_info:
                    entry.definitions.append(word_info["return-phrase"])
        
        return entry if (entry.definitions or entry.web_translations) else None
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """Translate using dictionary lookup."""
        entry = self.lookup(text, source_lang, target_lang)
        
        if entry:
            # Combine definitions
            translation = "; ".join(entry.definitions) if entry.definitions else ""
            if not translation and entry.web_translations:
                translation = entry.web_translations[0]
            
            result = TranslationResult(
                service=self.service_type,
                text=translation,
                source_lang=source_lang,
                target_lang=target_lang,
                phonetic=entry.phonetic_us or entry.phonetic_uk,
                definitions=entry.definitions,
                examples=entry.examples,
            )
            return result
        
        return TranslationResult.error_result(
            self.service_type,
            "Word not found in dictionary",
        )

    def get_web_url(self, text: str, source_lang: str, target_lang: str) -> str:
        """Get Youdao Dictionary web URL."""
        return f"https://dict.youdao.com/search?q={urllib.parse.quote(text)}"


def get_word_audio_url(word: str, voice_type: int = 2) -> str:
    """
    Get Youdao word audio URL.
    
    Args:
        word: English word
        voice_type: 1 = UK, 2 = US
    """
    return f"https://dict.youdao.com/dictvoice?type={voice_type}&audio={urllib.parse.quote(word)}"
