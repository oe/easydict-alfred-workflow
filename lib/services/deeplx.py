"""
Easydict Alfred Workflow - DeepLX Translation Service

Free DeepL translation using unofficial API.
"""

import json
import urllib.request
import urllib.error
from typing import Optional

from .base import TranslationService, TranslationResult, ServiceType, get_deepl_lang_code


class DeepLXService(TranslationService):
    """DeepLX free translation service."""
    
    name = "DeepLX"
    service_type = ServiceType.DEEPLX
    icon = "icons/deeplx.png"
    requires_api_key = False
    
    # DeepLX API endpoint
    @property
    def API_URL(self):
        from ..config import config
        return config.deeplx_endpoint
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """Translate using DeepLX API (with failover)."""
        
        # Convert language codes
        src = get_deepl_lang_code(source_lang)
        tgt = get_deepl_lang_code(target_lang)
        
        if not src or not tgt:
            return TranslationResult.error_result(
                self.service_type,
                f"Language not supported: {source_lang} -> {target_lang}"
            )
        
        # Endpoints to try
        endpoints = [self.API_URL]
        # Fallbacks
        candidates = [
            "http://127.0.0.1:1188/translate", 
            "https://api.deeplx.org/translate",
            "https://deeplx.missuo.ru/translate",
        ]
        for c in candidates:
            if c != self.API_URL and c not in endpoints:
                 endpoints.append(c)
        
        last_error = "Unknown error"
        
        for url in endpoints:
            try:
                # Prepare request
                data = json.dumps({
                    "text": text,
                    "source_lang": src,
                    "target_lang": tgt,
                }).encode("utf-8")
                
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                
                # Make request (shorter timeout for fallbacks?)
                timeout = 5 if url != self.API_URL else 10
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                
                # Check response
                code = result.get("code")
                if code == 200:
                    translated = result.get("data", "")
                    
                    # Check for ad/spam (e.g. linux.do)
                    if not translated or "linux.do" in translated or (translated.startswith("http") and " " not in translated):
                         last_error = f"Endpoint {url} returned spam/busy."
                         continue # Try next endpoint
                    
                    return TranslationResult(
                        service=self.service_type,
                        text=translated,
                        source_lang=source_lang,
                        target_lang=target_lang,
                    )
                else:
                    last_error = result.get("message", f"DeepLX Error: {code}")
                    
            except Exception as e:
                last_error = str(e)
                continue

        return TranslationResult.error_result(
             self.service_type,
             f"All DeepLX endpoints failed. Last error: {last_error}. Please install local DeepLX."
        )
            
    def get_web_url(self, text: str, source_lang: str, target_lang: str) -> str:
        """Get DeepL web URL."""
        import urllib.parse
        src = get_deepl_lang_code(source_lang) or "auto"
        tgt = get_deepl_lang_code(target_lang) or "en"
        return f"https://www.deepl.com/translator#{src}/{tgt}/{urllib.parse.quote(text)}"


# Synchronous wrapper for non-async contexts
def translate_deeplx(text: str, source_lang: str, target_lang: str) -> TranslationResult:
    """Synchronous DeepLX translation."""
    import asyncio
    service = DeepLXService()
    return asyncio.run(service.translate(text, source_lang, target_lang))
