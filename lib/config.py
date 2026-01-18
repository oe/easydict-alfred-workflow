"""
Easydict Alfred Workflow - Configuration Module

Reads configuration from Alfred Workflow Environment Variables.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Workflow configuration from Alfred environment variables."""
    
    # Languages
    first_language: str = "zh-CHS"
    second_language: str = "en"
    
    # Service toggles
    enable_deeplx: bool = True
    enable_bing: bool = True
    enable_google: bool = False
    enable_youdao: bool = False  # Disabled by default
    enable_deepl: bool = False
    enable_openai: bool = False
    
    # API Keys & Endpoints
    deeplx_endpoint: str = "https://api.deeplx.org/translate" # Configurable endpoint
    deepl_api_key: str = ""
    openai_api_key: str = ""
    openai_endpoint: str = "https://api.openai.com/v1/chat/completions"
    openai_model: str = "gpt-4o-mini"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        def get_bool(key: str, default: bool = False) -> bool:
            val = os.environ.get(key, "").lower()
            if val in ("1", "true", "yes", "on"):
                return True
            elif val in ("0", "false", "no", "off"):
                return False
            return default
        
        return cls(
            first_language=os.environ.get("first_language", "zh-CHS"),
            second_language=os.environ.get("second_language", "en"),
            enable_deeplx=get_bool("enable_deeplx", True),
            enable_bing=get_bool("enable_bing", True),
            enable_google=get_bool("enable_google", False),
            enable_youdao=get_bool("enable_youdao", False),
            enable_deepl=get_bool("enable_deepl", False),
            enable_openai=get_bool("enable_openai", False),
            deeplx_endpoint=os.environ.get("deeplx_endpoint", "https://api.deeplx.org/translate"),
            deepl_api_key=os.environ.get("deepl_api_key", ""),
            openai_api_key=os.environ.get("openai_api_key", ""),
            openai_endpoint=os.environ.get("openai_endpoint", "https://api.openai.com/v1/chat/completions"),
            openai_model=os.environ.get("openai_model", "gpt-4o-mini"),
        )


# Global config instance
config = Config.from_env()
