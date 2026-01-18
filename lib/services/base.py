"""
Easydict Alfred Workflow - Translation Service Base

Base class for all translation services.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class ServiceType(Enum):
    """Translation service types."""
    DEEPLX = "DeepLX"
    BING = "Bing"
    GOOGLE = "Google"
    DEEPL = "DeepL"
    OPENAI = "OpenAI"
    GEMINI = "Gemini"
    YOUDAO_DICT = "Youdao Dictionary"
    YOUDAO_TRANS = "Youdao Translate"


@dataclass
class TranslationResult:
    """Translation result from a service."""
    service: ServiceType
    text: str
    source_lang: str = ""
    target_lang: str = ""
    success: bool = True
    error: str = ""
    
    # For dictionary results
    phonetic: str = ""
    definitions: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    forms: List[str] = field(default_factory=list)
    
    @classmethod
    def error_result(cls, service: ServiceType, error: str) -> "TranslationResult":
        """Create an error result."""
        return cls(
            service=service,
            text="",
            success=False,
            error=error,
        )


class TranslationService(ABC):
    """Base class for translation services."""
    
    name: str = ""
    service_type: ServiceType = None
    icon: str = ""
    requires_api_key: bool = False
    
    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """
        Translate text.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            TranslationResult
        """
        pass
        
    def get_web_url(self, text: str, source_lang: str, target_lang: str) -> str:
        """Get the web URL for the translation service."""
        return ""
    
    def is_available(self) -> bool:
        """Check if the service is available (has required config)."""
        return True


# Language code mappings
LANG_CODE_MAP = {
    # Youdao format -> Standard format
    "zh-CHS": "zh-CN",
    "zh-CHT": "zh-TW",
    "en": "en",
    "ja": "ja",
    "ko": "ko",
    "fr": "fr",
    "de": "de",
    "es": "es",
    "pt": "pt",
    "it": "it",
    "ru": "ru",
    "ar": "ar",
}


def get_standard_lang_code(youdao_code: str) -> str:
    """Convert Youdao language code to standard format."""
    return LANG_CODE_MAP.get(youdao_code, youdao_code)


def get_bing_lang_code(youdao_code: str) -> str:
    """Convert Youdao language code to Bing format."""
    mapping = {
        "zh-CHS": "zh-Hans",
        "zh-CHT": "zh-Hant",
        "en": "en",
        "ja": "ja",
        "ko": "ko",
        "fr": "fr",
        "de": "de",
        "es": "es",
        "pt": "pt",
        "it": "it",
        "ru": "ru",
        "ar": "ar",
    }
    return mapping.get(youdao_code, youdao_code)


def get_google_lang_code(youdao_code: str) -> str:
    """Convert Youdao language code to Google format."""
    mapping = {
        "zh-CHS": "zh-CN",
        "zh-CHT": "zh-TW",
        "en": "en",
        "ja": "ja",
        "ko": "ko",
        "fr": "fr",
        "de": "de",
        "es": "es",
        "pt": "pt",
        "it": "it",
        "ru": "ru",
        "ar": "ar",
    }
    return mapping.get(youdao_code, youdao_code)


def get_deepl_lang_code(youdao_code: str) -> Optional[str]:
    """Convert Youdao language code to DeepL format."""
    mapping = {
        "zh-CHS": "ZH",
        "zh-CHT": "ZH",  # DeepL treats as simplified
        "en": "EN",
        "ja": "JA",
        "ko": None,  # Not supported
        "fr": "FR",
        "de": "DE",
        "es": "ES",
        "pt": "PT",
        "it": "IT",
        "ru": "RU",
        "ar": None,  # Not supported
    }
    return mapping.get(youdao_code, None)
