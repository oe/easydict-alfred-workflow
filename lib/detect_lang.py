"""
Easydict Alfred Workflow - Language Detection

Detect input text language using Bing API.
"""

import re
from typing import Optional, Tuple


# Common language patterns
PATTERNS = {
    "zh-CHS": re.compile(r"[\u4e00-\u9fff]"),  # Chinese characters
    "ja": re.compile(r"[\u3040-\u309f\u30a0-\u30ff]"),  # Hiragana, Katakana
    "ko": re.compile(r"[\uac00-\ud7af\u1100-\u11ff]"),  # Korean
    "ar": re.compile(r"[\u0600-\u06ff]"),  # Arabic
    "ru": re.compile(r"[\u0400-\u04ff]"),  # Cyrillic
}


def detect_language_simple(text: str) -> str:
    """
    Simple language detection based on character patterns.
    
    Returns language code (Youdao format).
    """
    if not text:
        return "en"
    
    text = text.strip()
    
    # Count characters of each type
    for lang, pattern in PATTERNS.items():
        if pattern.search(text):
            return lang
    
    # Default to English for Latin characters
    return "en"


def get_target_language(source_lang: str, first_lang: str, second_lang: str) -> str:
    """
    Determine target language based on source language.
    
    If source matches first language, translate to second.
    Otherwise, translate to first.
    """
    if source_lang == first_lang:
        return second_lang
    return first_lang


def is_word(text: str) -> bool:
    """
    Check if text is likely a single word (for dictionary lookup).
    """
    text = text.strip()
    
    # Contains spaces = not a single word (for English)
    if " " in text and not PATTERNS["zh-CHS"].search(text):
        words = text.split()
        # Allow 2-3 word phrases for dictionary
        if len(words) > 3:
            return False
    
    # Very long text = sentence
    if len(text) > 50:
        return False
    
    return True


def detect_with_bing(text: str) -> Optional[str]:
    """
    Detect language using Bing translation API.
    
    Returns language code or None on error.
    """
    # Import here to avoid circular dependency
    from .services.bing import BingService
    import asyncio
    
    try:
        service = BingService()
        # Translate to English and get detected language
        result = asyncio.run(service.translate(text, "auto", "en"))
        if result.success:
            return result.source_lang
    except Exception:
        pass
    
    return None


def detect_language(text: str, use_api: bool = True) -> str:
    """
    Detect language of text.
    
    Args:
        text: Text to detect
        use_api: Whether to use Bing API for detection
        
    Returns:
        Language code (Youdao format)
    """
    # First try simple pattern matching
    lang = detect_language_simple(text)
    
    # For non-obvious cases, try API
    if use_api and lang == "en":
        api_lang = detect_with_bing(text)
        if api_lang:
            return api_lang
    
    return lang
