#!/usr/bin/env python3
"""
Easydict Alfred Workflow - Dictionary Entry

Usage: python3 di.py {query}
Keyword: di
"""

import sys
import os
from concurrent.futures import ThreadPoolExecutor

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.config import config
from lib.alfred import AlfredOutput, AlfredItem
from lib.services.youdao_dict import YoudaoDictService
from lib.services.base import ServiceType
from lib.detect_lang import detect_language_simple, get_target_language


def main():
    # Get query from argument
    query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    
    output = AlfredOutput()
    
    if not query:
        output.add_item(AlfredItem(
            title="Type a word to look up...",
            subtitle="Powered by Youdao Dictionary & Translation Services",
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
    
    # Initialize Dictionary Service
    dict_service = YoudaoDictService()
    
    # Run Dictionary and Translation in parallel
    # We use ThreadPoolExecutor to run them concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        # 1. Dictionary Lookup
        dict_future = executor.submit(dict_service.lookup, query, source_lang, target_lang)
        
        # 2. Translation Services
        # Import dynamically to ensure environment is ready and avoid issues
        try:
            from tr import get_enabled_services, translate_with_service, get_service_icon, get_service_web_url
            
            # Get enabled translation services
            tr_services_list = get_enabled_services()
            
            # Submit translation tasks
            tr_futures = {}
            for svc_name in tr_services_list:
                # We skip Youdao Translate if user wants (optional), but let's keep it 
                # to ensure "Different Providers" are visible.
                tr_futures[executor.submit(translate_with_service, svc_name, query, source_lang, target_lang)] = svc_name
                
        except ImportError:
            tr_futures = {}
            # Fallback if tr.py cannot be imported? Should not happen.

        # Collect Dictionary Result
        try:
            entry = dict_future.result(timeout=10)
        except Exception:
            entry = None

        # Collect Translation Results
        tr_results = []
        for future, svc_name in tr_futures.items():
            try:
                res = future.result(timeout=10)
                if res and res.success and res.text:
                   tr_results.append(res)
            except Exception:
                pass

    # --- Construct Output ---
    
    has_results = False

    # 1. Dictionary Items
    if entry and (entry.definitions or entry.web_translations):
        has_results = True
        
        # Phonetic subtitle
        phonetic_parts = []
        if entry.phonetic_us:
            phonetic_parts.append(f"🇺🇸 /{entry.phonetic_us}/")
        if entry.phonetic_uk:
            phonetic_parts.append(f"🇬🇧 /{entry.phonetic_uk}/")
        phonetic = "  ".join(phonetic_parts)
        
        # Add definitions
        is_chinese_query = (source_lang == "zh-CHS" or source_lang == "zh-CHT")
        
        for i, definition in enumerate(entry.definitions[:10]):
            if is_chinese_query:
                # Format: Title = Result Word, Subtitle = Explanation
                parts = definition.split("  ", 1)
                title_text = parts[0]
                subtitle_text = parts[1] if len(parts) > 1 else ""
                # Provide Pinyin in Largetype for reference? Or just omit.
            else:
                # Format: Title = Query + Phonetic, Subtitle = Definition
                title_text = f"{query}  {phonetic}"
                subtitle_text = definition
            
            item = AlfredItem.create(
                title=title_text,
                subtitle=subtitle_text,
                arg=definition,
                copy_text=title_text if is_chinese_query else definition,
                largetype=f"{query}\n\n{definition}",
                alt_subtitle="⌥↩ Play pronunciation",
                alt_arg=f"PLAY:{title_text if is_chinese_query else query}", # Play the result word for Chinese queries?? Actually 'say' might guesslang.
                # User wants English phonetic. If I play "hello", it speaks English. 
                # If I play "你好", it speaks Chinese.
                # If Query=Zh, Result=En. Ideally PLAY should play Result (En).
                cmd_subtitle="⌘↩ Open in Web",
                cmd_arg=dict_service.get_web_url(query, source_lang, target_lang),
                icon_path=dict_service.icon
            )
            output.add_item(item)
        
        # Add web translations if no definitions
        if not entry.definitions:
            for trans in entry.web_translations[:3]:
                # Web translations are usually just the target word/phrase
                output.add_item(AlfredItem.create(
                    title=trans if is_chinese_query else f"{query}  {phonetic}",
                    subtitle=f"{query} translation" if is_chinese_query else trans, # Fallback subtitle
                    arg=trans,
                    copy_text=trans,
                    icon_path=dict_service.icon
                ))
        
        # Add word forms
        if entry.forms:
            forms_text = "  ".join([f"{k}: {v}" for k, v in entry.forms.items()])
            output.add_item(AlfredItem.create(
                title=f"📝 {forms_text}",
                subtitle="Word forms",
                arg=forms_text,
                icon_path=dict_service.icon
            ))



    # 2. Translation Items
    if tr_results:
        has_results = True
        
        # Sort translations
        priority = {
            ServiceType.DEEPLX: 0, 
            ServiceType.YOUDAO_TRANS: 1, 
            ServiceType.GOOGLE: 2,
            ServiceType.BING: 3,
            ServiceType.OPENAI: 4,
            ServiceType.DEEPL: 5,
        }
        tr_results.sort(key=lambda r: priority.get(r.service, 99))
        
        # Add separator if dictionary results exist
        # Alfred doesn't support explicit separators, but we can append them.
        
        for res in tr_results:
            service_name = res.service.value
            # Use icon from tr.py logic
            icon = get_service_icon(res.service)
            
            output.add_item(AlfredItem.create(
                title=res.text,
                subtitle=f"{service_name}  •  Translation",
                arg=res.text,
                icon_path=icon,
                copy_text=res.text,
                largetype=f"{query}\n\n{res.text}",
                alt_subtitle="⌥↩ Play pronunciation",
                alt_arg=f"SPEAK:{res.text}",
                cmd_subtitle="⌘↩ Open in Web",
                cmd_arg=get_service_web_url(res.service, query, source_lang, target_lang),
            ))

    # Fallback if NOTHING found
    if not has_results:
        output.add_item(AlfredItem(
            title=f"No results for '{query}'",
            subtitle="Try checking your network or configuration",
            valid=False
        ))

    output.print()


if __name__ == "__main__":
    main()
