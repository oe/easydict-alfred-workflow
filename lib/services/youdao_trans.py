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
        """Synchronous translation implementation."""
        # Use Youdao Dictionary API which is more reliable
        try:
            # Import here to reuse logic or just implement similar logic
            import urllib.parse
            import json
            
            # Build URL similar to dictionary service
            dicts = [["web_trans", "fanyi"]]
            params = urllib.parse.urlencode({
                "q": text,
                "le": "en" if target_lang == "en" else "auto",
                "dicts": json.dumps({"count": 99, "dicts": dicts}),
            })
            url = f"https://dict.youdao.com/jsonapi?{params}"
            
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            # Try to get translation from fanyi (best) or web_trans (fallback)
            translation = ""
            
            # Check fanyi
            fanyi = data.get("fanyi", {})
            if fanyi:
                trans = fanyi.get("tran", "")
                if trans:
                    translation = trans
            
            # Check web_trans if no fanyi
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
            
            if translation:
                return TranslationResult(
                    service=self.service_type,
                    text=translation,
                    source_lang=source_lang,
                    target_lang=target_lang,
                )
            
            return TranslationResult.error_result(
                self.service_type,
                "No translation found"
            )
            
        except Exception as e:
            return TranslationResult.error_result(
                self.service_type,
                str(e)
            )

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


# Synchronous wrapper
def translate_youdao(text: str, source_lang: str, target_lang: str) -> TranslationResult:
    """Synchronous Youdao translation."""
    service = YoudaoTranslateService()
    return service.translate_sync(text, source_lang, target_lang)
