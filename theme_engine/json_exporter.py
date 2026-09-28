"""
JSON Palette & Theme Tokens Exporter.
Exports structured palette definitions and CSS variables for designers and developers.
"""

import json
from typing import Dict, Any, List
from theme_engine.palette import ResolvedThemePalette
from theme_engine.color_extractor import ExtractedColor, rgb_to_hex


def export_theme_to_json(
    palette: ResolvedThemePalette,
    extracted_colors: List[ExtractedColor]
) -> str:
    """
    Export comprehensive theme palette data and CSS variables as JSON string.
    """
    data = {
        "metadata": {
            "generator": "Telegram Theme Studio Bot",
            "mode": palette.mode,
            "version": "2.0"
        },
        "theme_colors": {
            "background": {
                "base": palette.hex_bg,
                "surface": palette.hex_surface,
                "elevated": rgb_to_hex(*palette.bg_elevated),
                "topbar": rgb_to_hex(*palette.topbar_bg),
                "dialogs": rgb_to_hex(*palette.dialogs_bg)
            },
            "accents": {
                "primary": palette.hex_primary_accent,
                "secondary": palette.hex_secondary_accent,
                "hover": rgb_to_hex(*palette.accent_hover),
                "send_button": rgb_to_hex(*palette.send_button)
            },
            "bubbles": {
                "incoming_background": palette.hex_in_bubble,
                "incoming_text": rgb_to_hex(*palette.in_bubble_text),
                "incoming_time": rgb_to_hex(*palette.in_bubble_time),
                "outgoing_background": palette.hex_out_bubble,
                "outgoing_text": rgb_to_hex(*palette.out_bubble_text),
                "outgoing_time": rgb_to_hex(*palette.out_bubble_time)
            },
            "typography": {
                "text_primary": palette.hex_text,
                "text_secondary": rgb_to_hex(*palette.text_secondary),
                "link": rgb_to_hex(*palette.text_link)
            },
            "badges": {
                "unread_badge_background": rgb_to_hex(*palette.unread_badge_bg),
                "unread_badge_text": rgb_to_hex(*palette.unread_badge_text)
            }
        },
        "extracted_palette": [
            col.to_dict() for col in extracted_colors
        ],
        "css_variables": {
            "--tg-theme-bg-color": palette.hex_bg,
            "--tg-theme-surface-color": palette.hex_surface,
            "--tg-theme-primary-accent": palette.hex_primary_accent,
            "--tg-theme-secondary-accent": palette.hex_secondary_accent,
            "--tg-theme-text-primary": palette.hex_text,
            "--tg-theme-text-secondary": rgb_to_hex(*palette.text_secondary),
            "--tg-theme-bubble-in-bg": palette.hex_in_bubble,
            "--tg-theme-bubble-in-text": rgb_to_hex(*palette.in_bubble_text),
            "--tg-theme-bubble-out-bg": palette.hex_out_bubble,
            "--tg-theme-bubble-out-text": rgb_to_hex(*palette.out_bubble_text)
        }
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
