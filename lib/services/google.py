"""
Easydict Alfred Workflow - Google Translation Service

Free Google translation using mobile web API.
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional

from .base import TranslationService, TranslationResult, ServiceType, get_google_lang_code


class GoogleService(TranslationService):
    """Google web translation service."""
    
    name = "Google"
    service_type = ServiceType.GOOGLE
    icon = "icons/google.png"
    requires_api_key = False
    
    USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """Translate using Google mobile web API."""
        
        # Convert language codes
        src = get_google_lang_code(source_lang) if source_lang != "auto" else "auto"
        tgt = get_google_lang_code(target_lang)
        
        try:
            # Build URL (mobile version for simpler parsing)
            params = urllib.parse.urlencode({
                "sl": src,
                "tl": tgt,
                "hl": tgt,
                "q": text,
            })
            url = f"https://translate.google.com/m?{params}"
            
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self.USER_AGENT},
            )
            
            # Make request
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode("utf-8")
            
            # Parse result - look for result-container div
            import re
            match = re.search(r'class="result-container">([^<]+)<', html)
            
            if match:
                translated_text = match.group(1)
                # Decode HTML entities
                translated_text = urllib.parse.unquote(translated_text)
                
                return TranslationResult(
                    service=self.service_type,
                    text=translated_text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                )
            
            return TranslationResult.error_result(
                self.service_type,
                "Could not parse translation result",
            )
            
        except urllib.error.URLError as e:
            return TranslationResult.error_result(
                self.service_type,
                f"Network error (may need proxy): {str(e)}",
            )
        except Exception as e:
            return TranslationResult.error_result(
                self.service_type,
                str(e),
            )

    def get_web_url(self, text: str, source_lang: str, target_lang: str) -> str:
        """Get Google Translate web URL."""
        sl = get_google_lang_code(source_lang) or "auto"
        tl = get_google_lang_code(target_lang) or "en"
        return f"https://translate.google.com/?sl={sl}&tl={tl}&text={urllib.parse.quote(text)}&op=translate"


# Synchronous wrapper
def translate_google(text: str, source_lang: str, target_lang: str) -> TranslationResult:
    """Synchronous Google translation."""
    import asyncio
    service = GoogleService()
    return asyncio.run(service.translate(text, source_lang, target_lang))
