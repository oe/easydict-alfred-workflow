"""
Easydict Alfred Workflow - Youdao Translation Service

Free Youdao translation using web API.
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional

from .base import TranslationService, TranslationResult, ServiceType


class YoudaoTranslateService(TranslationService):
    """Youdao web translation service (via dictionary API)."""
    
    name = "Youdao Translate"
    service_type = ServiceType.YOUDAO_TRANS
    icon = "icons/youdao.png"
    requires_api_key = False
    
    def translate_sync(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Sync translation implementation using Dictionary API."""
        try:
            import urllib.request
            import urllib.parse
            import json
            
            # Use Youdao Dict API (jsonapi)
            # Reliable for words and phrases, flaky for sentences
            dicts = [["web_trans", "fanyi"]]
            params = urllib.parse.urlencode({
                "q": text,
                "le": "en" if target_lang == "en" else "auto",
                "dicts": json.dumps({"count": 99, "dicts": dicts}),
            })
            url = f"https://dict.youdao.com/jsonapi?{params}"
            
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                
            # Extract translation
            translation = ""
            
            # 1. Try "web_trans" (Web Translation)
            if not translation:
                web_trans = data.get("web_trans", {})
                if web_trans:
                    web_items = web_trans.get("web-translation", [])
                    for item in web_items:
                        trans_list = item.get("trans", [])
                        for t in trans_list:
                             val = t.get("value", "")
                             if val:
                                 translation = val
                                 break
                        if translation:
                            break

            # 2. Try "fanyi" (Machine Translation - often empty for long text without proper sign)
            if not translation:
                fanyi = data.get("fanyi", {})
                if fanyi:
                    trans = fanyi.get("tran", "")
                    if trans:
                        translation = trans

            if translation:
                return TranslationResult(
                    service=self.service_type,
                    text=translation,
                    source_lang=source_lang,
                    target_lang=target_lang,
                )
            
            # If no translation found, likely due to length or API limit
            msg = "No translation found."
            if len(text) > 20:
                msg = "Youdao Dict API limited for sentences. Use Google/DeepLX."
                
            return TranslationResult.error_result(self.service_type, msg)

        except Exception as e:
            return TranslationResult.error_result(self.service_type, f"Net Error: {str(e)}")

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """Translate using Youdao dictionary API."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.translate_sync, text, source_lang, target_lang)

    def get_web_url(self, text: str, source_lang: str, target_lang: str) -> str:
        """Get Youdao Translate web URL."""
        return "https://fanyi.youdao.com/"


# Synchronous wrapper
def translate_youdao(text: str, source_lang: str, target_lang: str) -> TranslationResult:
    """Synchronous Youdao translation."""
    service = YoudaoTranslateService()
    return service.translate_sync(text, source_lang, target_lang)
