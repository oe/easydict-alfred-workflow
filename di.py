#!/usr/bin/env python3
"""
Easydict Alfred Workflow - Dictionary Entry

Usage: python3 di.py {query}
Keyword: di
"""

import sys
import os

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.config import config
from lib.alfred import AlfredOutput, AlfredItem
from lib.services.youdao_dict import YoudaoDictService, get_word_audio_url
from lib.detect_lang import detect_language_simple, get_target_language


def main():
    # Get query from argument
    query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    
    output = AlfredOutput()
    
    if not query:
        output.add_item(AlfredItem(
            title="Type a word to look up...",
            subtitle="Powered by Youdao Dictionary",
            valid=False,
        ))
        output.print()
        return
    
    # Detect language
    source_lang = detect_language_simple(query)
    target_lang = get_target_language(
        source_lang, 
        config.first_language, 
        config.second_language
    )
    
    # Look up word
    dict_service = YoudaoDictService()
    entry = dict_service.lookup(query, source_lang, target_lang)
    
    if entry and (entry.definitions or entry.web_translations):
        # Phonetic subtitle
        phonetic_parts = []
        if entry.phonetic_us:
            phonetic_parts.append(f"🇺🇸 /{entry.phonetic_us}/")
        if entry.phonetic_uk:
            phonetic_parts.append(f"🇬🇧 /{entry.phonetic_uk}/")
        phonetic = "  ".join(phonetic_parts)
        
        # Add definitions
        for i, definition in enumerate(entry.definitions[:5]):
            item = AlfredItem.create(
                title=definition,
                subtitle=phonetic if i == 0 else "",
                arg=definition,
                copy_text=definition,
                largetype=f"{query}\n\n{definition}",
                alt_subtitle="⌥↩ Play pronunciation",
                alt_arg=f"PLAY:{query}",
                cmd_subtitle="⌘↩ Open in Eudic",
                cmd_arg=f"eudic://dict/{query}",
            )
            output.add_item(item)
        
        # Add web translations if no definitions
        if not entry.definitions:
            for trans in entry.web_translations[:3]:
                output.add_item(AlfredItem.create(
                    title=trans,
                    subtitle="Web translation",
                    arg=trans,
                    copy_text=trans,
                ))
        
        # Add word forms
        if entry.forms:
            forms_text = "  ".join([f"{k}: {v}" for k, v in entry.forms.items()])
            output.add_item(AlfredItem(
                title=f"📝 {forms_text}",
                subtitle="Word forms",
                arg=forms_text,
                valid=True,
            ))
    else:
        # No dictionary result - suggest translation
        output.add_item(AlfredItem(
            title=f"No dictionary entry for '{query}'",
            subtitle="Press Enter to translate instead",
            arg=f"TRANSLATE:{query}",
            valid=True,
        ))
    
    output.print()


if __name__ == "__main__":
    main()
