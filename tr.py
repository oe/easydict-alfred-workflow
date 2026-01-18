#!/usr/bin/env python3
"""
Easydict Alfred Workflow - Translation Entry

Usage: python3 tr.py {query}
Keyword: tr
"""

import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.config import config
from lib.alfred import AlfredOutput, AlfredItem
from lib.services.base import TranslationResult, ServiceType
from lib.detect_lang import detect_language_simple, get_target_language


def translate_with_service(service_name: str, text: str, source_lang: str, target_lang: str) -> TranslationResult:
    """Translate using a specific service."""
    try:
        if service_name == "deeplx":
            from lib.services.deeplx import translate_deeplx
            return translate_deeplx(text, source_lang, target_lang)
        elif service_name == "bing":
            from lib.services.bing import translate_bing
            return translate_bing(text, source_lang, target_lang)
        elif service_name == "google":
            from lib.services.google import translate_google
            return translate_google(text, source_lang, target_lang)
        elif service_name == "youdao":
            from lib.services.youdao_trans import translate_youdao
            return translate_youdao(text, source_lang, target_lang)
    except Exception as e:
        return TranslationResult.error_result(
            ServiceType[service_name.upper()] if service_name != "youdao" else ServiceType.YOUDAO_TRANS,
            str(e),
        )
    
    return TranslationResult.error_result(
        ServiceType.BING, # Fallback
        "Unknown service",
    )


def get_enabled_services() -> List[str]:
    """Get list of enabled translation services."""
    services = []
    if config.enable_deeplx:
        services.append("deeplx")
    if config.enable_youdao:
        services.append("youdao")
    if config.enable_bing:
        services.append("bing")
    if config.enable_google:
        services.append("google")
    return services


def get_service_icon(service_type: ServiceType) -> str:
    """Get icon path for a service."""
    icons = {
        ServiceType.DEEPLX: "icons/deeplx.png",
        ServiceType.BING: "icons/bing.png",
        ServiceType.GOOGLE: "icons/google.png",
        ServiceType.DEEPL: "icons/deepl.png",
        ServiceType.OPENAI: "icons/openai.png",
        ServiceType.YOUDAO_TRANS: "icons/youdao.png",
        ServiceType.YOUDAO_DICT: "icons/youdao.png",
    }
    return icons.get(service_type, "icon.png")


def get_service_web_url(service_type: ServiceType, text: str, source_lang: str, target_lang: str) -> str:
    """Get web URL for a service."""
    try:
        if service_type == ServiceType.DEEPLX:
            from lib.services.deeplx import DeepLXService
            return DeepLXService().get_web_url(text, source_lang, target_lang)
        elif service_type == ServiceType.BING:
            from lib.services.bing import BingService
            return BingService().get_web_url(text, source_lang, target_lang)
        elif service_type == ServiceType.GOOGLE:
            from lib.services.google import GoogleService
            return GoogleService().get_web_url(text, source_lang, target_lang)
        elif service_type == ServiceType.YOUDAO_TRANS:
            from lib.services.youdao_trans import YoudaoTranslateService
            return YoudaoTranslateService().get_web_url(text, source_lang, target_lang)
    except Exception:
        pass
    except Exception:
        pass
    return ""


def get_quicklook_url(text: str, service_name: str) -> str:
    """Generate a temporary HTML file for Quick Look."""
    try:
        import tempfile
        filename = f"easydict_ql_{service_name}.html"
        path = os.path.join(tempfile.gettempdir(), filename)
        
        # Simple styled HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, sans-serif; padding: 20px; line-height: 1.6; color: #333; }}
                h2 {{ color: #007AFF; margin-top: 0; }}
                pre {{ white-space: pre-wrap; word-wrap: break-word; background: #f5f5f7; padding: 15px; border-radius: 8px; font-size: 16px; border: 1px solid #e1e1e8; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #888; }}
            </style>
        </head>
        <body>
            <h2>{service_name} Translation</h2>
            <pre>{text}</pre>
            <div class="footer">Press Cmd+C to copy. Esc to close.</div>
        </body>
        </html>
        """
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
            
        return path
    except:
        return ""


def main():
    # Get query from argument
    query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    
    output = AlfredOutput()
    
    if not query:
        output.add_item(AlfredItem(
            title="Type text to translate...",
            subtitle="Powered by DeepLX, Bing, Google, Youdao",
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
    
    # Get enabled services
    services = get_enabled_services()
    
    if not services:
        output.add_error("No translation services enabled", "Enable services in workflow configuration")
        output.print()
        return
    
    # Translate with all enabled services in parallel
    results: List[TranslationResult] = []
    
    with ThreadPoolExecutor(max_workers=len(services)) as executor:
        futures = [
            executor.submit(translate_with_service, svc, query, source_lang, target_lang)
            for svc in services
        ]
        for future in futures:
            try:
                result = future.result(timeout=15)
                if result:
                    results.append(result)
            except Exception as e:
                pass
    
    # Sort by service priority
    priority = {
        ServiceType.DEEPLX: 0, 
        ServiceType.YOUDAO_TRANS: 1, 
        ServiceType.GOOGLE: 2,
        ServiceType.BING: 3,
    }
    results.sort(key=lambda r: priority.get(r.service, 99))
    
    # Add results to output
    if results:
        for result in results:
            if result.success and result.text:
                service_name = result.service.value
                icon = get_service_icon(result.service)
                
                output.add_item(AlfredItem.create(
                    title=result.text,
                    subtitle=f"{service_name}  •  {source_lang} → {target_lang}",
                    arg=result.text,
                    icon_path=icon,
                    copy_text=result.text,
                    largetype=f"{query}\n\n{result.text}",
                    alt_subtitle="⌥↩ Play pronunciation",
                    alt_arg=f"SPEAK:{result.text}",
                    cmd_subtitle="⌘↩ Open in Web",
                    cmd_arg=get_service_web_url(result.service, query, source_lang, target_lang),
                    quicklookurl=get_quicklook_url(result.text, service_name),
                ))
            elif not result.success:
                output.add_item(AlfredItem(
                    title=f"{result.service.value}: {result.error}",
                    subtitle="Translation failed",
                    valid=False,
                    icon={"path": get_service_icon(result.service)},
                ))
    else:
        output.add_error("Translation failed", "All services returned errors")
    
    output.print()


if __name__ == "__main__":
    main()
