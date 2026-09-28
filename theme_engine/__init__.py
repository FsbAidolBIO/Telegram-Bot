"""
Theme engine package for Telegram theme generation.
"""

from theme_engine.color_extractor import (
    extract_palette_from_image,
    detect_image_brightness,
    ExtractedColor,
    rgb_to_hex,
    hex_to_rgb,
    get_color_name,
    get_color_emoji,
    is_valid_hex,
    shift_temperature
)
from theme_engine.palette import (
    ThemeConfig,
    ResolvedThemePalette,
    build_palette
)
from theme_engine.wallpaper_generator import (
    generate_wallpaper,
    get_wallpaper_jpeg_bytes
)
from theme_engine.android_generator import generate_android_theme
from theme_engine.desktop_generator import generate_desktop_theme, generate_desktop_palette_text
from theme_engine.preview_generator import render_theme_preview, render_preview_to_bytes
from theme_engine.palette_card_generator import generate_palette_card, generate_palette_card_bytes
from theme_engine.json_exporter import export_theme_to_json

__all__ = [
    "extract_palette_from_image",
    "detect_image_brightness",
    "ExtractedColor",
    "rgb_to_hex",
    "hex_to_rgb",
    "get_color_name",
    "get_color_emoji",
    "is_valid_hex",
    "shift_temperature",
    "ThemeConfig",
    "ResolvedThemePalette",
    "build_palette",
    "generate_wallpaper",
    "get_wallpaper_jpeg_bytes",
    "generate_android_theme",
    "generate_desktop_theme",
    "generate_desktop_palette_text",
    "render_theme_preview",
    "render_preview_to_bytes",
    "generate_palette_card",
    "generate_palette_card_bytes",
    "export_theme_to_json"
]
