#!/usr/bin/env python3
"""
Easydict Alfred Workflow - Audio Playback

Usage: python3 play_audio.py {word_or_text}

Plays word pronunciation using Youdao audio or macOS TTS.
"""

import sys
import os
import urllib.request
import subprocess
import tempfile
from pathlib import Path

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.detect_lang import detect_language_simple


def play_youdao_audio(word: str, voice_type: int = 2) -> bool:
    """
    Download and play Youdao word audio.
    
    Args:
        word: English word
        voice_type: 1 = UK, 2 = US
        
    Returns:
        True if successful
    """
    url = f"https://dict.youdao.com/dictvoice?type={voice_type}&audio={word}"
    
    try:
        # Create cache directory
        cache_dir = Path.home() / ".cache" / "easydict" / "audio"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Check cache
        audio_path = cache_dir / f"{word}.mp3"
        
        if not audio_path.exists():
            # Download audio
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                audio_data = response.read()
            
            # Check if valid audio (not empty HTML error)
            if len(audio_data) < 1000 or b"<!DOCTYPE" in audio_data:
                return False
            
            with open(audio_path, "wb") as f:
                f.write(audio_data)
        
        # Play with afplay
        subprocess.run(
            ["afplay", str(audio_path)],
            check=True,
            capture_output=True,
        )
        return True
        
    except Exception as e:
        return False


def play_tts(text: str, lang: str = "en") -> bool:
    """
    Play text using macOS TTS (say command).
    
    Args:
        text: Text to speak
        lang: Language code
        
    Returns:
        True if successful
    """
    # Map language to voice
    voices = {
        "en": "Samantha",
        "zh-CHS": "Ting-Ting",
        "zh-CHT": "Mei-Jia",
        "ja": "Kyoko",
        "ko": "Yuna",
        "fr": "Thomas",
        "de": "Anna",
        "es": "Monica",
        "it": "Alice",
        "ru": "Milena",
    }
    
    voice = voices.get(lang, "Samantha")
    
    try:
        subprocess.run(
            ["say", "-v", voice, text],
            check=True,
            capture_output=True,
        )
        return True
    except Exception:
        # Fallback to default voice
        try:
            subprocess.run(
                ["say", text],
                check=True,
                capture_output=True,
            )
            return True
        except Exception:
            return False


def main():
    if len(sys.argv) < 2:
        print("Usage: play_audio.py {word_or_command}")
        sys.exit(1)
    
    arg = " ".join(sys.argv[1:])
    
    # Handle special commands
    if arg.startswith("PLAY:"):
        # Play word pronunciation
        word = arg[5:].strip()
        lang = detect_language_simple(word)
        
        # Try Youdao for English words
        if lang == "en" and len(word.split()) <= 3:
            if play_youdao_audio(word):
                return
        
        # Fallback to TTS
        play_tts(word, lang)
        
    elif arg.startswith("SPEAK:"):
        # Speak text with TTS
        text = arg[6:].strip()
        lang = detect_language_simple(text)
        play_tts(text, lang)
        
    else:
        # Default: try Youdao then TTS
        word = arg.strip()
        lang = detect_language_simple(word)
        
        if lang == "en":
            if play_youdao_audio(word):
                return
        
        play_tts(word, lang)


if __name__ == "__main__":
    main()
