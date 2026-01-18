"""
Easydict Alfred Workflow - Bing Translation Service

Free Bing translation using web API with token.
"""

import json
import re
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Tuple, Dict, Any

from .base import TranslationService, TranslationResult, ServiceType, get_bing_lang_code


class BingService(TranslationService):
    """Bing web translation service."""
    
    name = "Bing"
    service_type = ServiceType.BING
    icon = "icons/bing.png"
    requires_api_key = False
    
    # Bing hosts
    DEFAULT_HOST = "www.bing.com"
    CN_HOST = "cn.bing.com"
    
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Cache token
    _token_cache: Dict[str, Any] = {}
    
    def __init__(self, host: Optional[str] = None):
        self.host = host or self.DEFAULT_HOST
    
    def _get_config(self) -> Optional[Dict[str, str]]:
        """Get Bing translation config (IG, IID, token, key) from web page."""
        try:
            url = f"https://{self.host}/translator"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Referer": "https://www.bing.com/translator",
                    "Origin": "https://www.bing.com",
                },
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                # Update host if redirected (e.g. www.bing.com -> cn.bing.com)
                final_url = response.geturl()
                if "://" in final_url:
                    new_host = final_url.split("://")[1].split("/")[0]
                    if new_host != self.host:
                        self.host = new_host
                
                html = response.read().decode("utf-8")
            
            # Parse config
            ig_match = re.search(r'IG:"([^"]+)"', html)
            iid_match = re.search(r'data-iid="([^"]+)"', html)
            params_match = re.search(r'var params_AbusePreventionHelper = (\[.*?\]);', html)
            
            if ig_match and params_match:
                ig = ig_match.group(1)
                iid = iid_match.group(1) if iid_match else "translator.5023"
                
                params = json.loads(params_match.group(1))
                key = params[0]
                token = params[1]
                
                return {
                    "IG": ig,
                    "IID": iid,
                    "key": str(key),
                    "token": token,
                }
        except Exception as e:
            # Try alternate host
            if self.host == self.DEFAULT_HOST:
                self.host = self.CN_HOST
                return self._get_config()
            return None
        
        return None
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """Translate using Bing web API."""
        
        # Convert language codes
        from_lang = get_bing_lang_code(source_lang)
        to_lang = get_bing_lang_code(target_lang)
        
        # Get config (with caching)
        config = self._token_cache.get("config")
        if not config:
            config = self._get_config()
            if config:
                self._token_cache["config"] = config
        
        if not config:
            return TranslationResult.error_result(
                self.service_type,
                "Failed to get Bing config",
            )
        
        try:
            # Build URL
            count = self._token_cache.get("count", 1)
            self._token_cache["count"] = count + 1
            
            iid = f"{config['IID']}.{count}"
            url = f"https://{self.host}/ttranslatev3?isVertical=1&IG={config['IG']}&IID={iid}"
            
            # Build request data
            data = urllib.parse.urlencode({
                "text": text,
                "fromLang": from_lang if from_lang != "auto" else "auto-detect",
                "to": to_lang,
                "token": config["token"],
                "key": config["key"],
            }).encode("utf-8")
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "https://www.bing.com/translator",
                    "Origin": "https://www.bing.com",
                },
                method="POST",
            )
            
            # Make request
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    response_data = response.read()
                    if not response_data:
                        return TranslationResult.error_result(
                            self.service_type,
                            "Empty response from Bing"
                        )
                    result = json.loads(response_data.decode("utf-8"))
            except json.JSONDecodeError:
                 return TranslationResult.error_result(
                    self.service_type,
                    f"Invalid JSON from Bing. Response length: {len(response_data)}"
                )
            except Exception as e:
                 return TranslationResult.error_result(
                    self.service_type,
                    f"Bing Request Error: {str(e)}"
                )
            
            # Parse response
            if result and len(result) > 0:
                translations = result[0].get("translations", [])
                if translations:
                    translated_text = translations[0].get("text", "")
                    detected_lang = result[0].get("detectedLanguage", {}).get("language", source_lang)
                    
                    return TranslationResult(
                        service=self.service_type,
                        text=translated_text,
                        source_lang=detected_lang,
                        target_lang=target_lang,
                    )
            
            return TranslationResult.error_result(
                self.service_type,
                "Empty response",
            )
            
        except urllib.error.URLError as e:
            # Clear token cache on error
            self._token_cache.clear()
            return TranslationResult.error_result(
                self.service_type,
                f"Network error: {str(e)}",
            )
            return TranslationResult.error_result(
                self.service_type,
                str(e),
            )
            
    def get_web_url(self, text: str, source_lang: str, target_lang: str) -> str:
        """Get Bing Translate web URL."""
        from_lang = get_bing_lang_code(source_lang)
        to_lang = get_bing_lang_code(target_lang)
        return f"https://www.bing.com/translator?from={from_lang}&to={to_lang}&text={urllib.parse.quote(text)}"


# Synchronous wrapper
def translate_bing(text: str, source_lang: str, target_lang: str) -> TranslationResult:
    """Synchronous Bing translation."""
    import asyncio
    service = BingService()
    return asyncio.run(service.translate(text, source_lang, target_lang))
