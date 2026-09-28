"""
Theme engine package for Telegram theme generation.
"""

from theme_engine.color_extractor import (
    extract_palette_from_image,
    detect_image_brightness,
    ExtractedColor,
    rgb_to_hex,
    hex_to_rgb
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

__all__ = [
    "extract_palette_from_image",
    "detect_image_brightness",
    "ExtractedColor",
    "rgb_to_hex",
    "hex_to_rgb",
    "ThemeConfig",
    "ResolvedThemePalette",
    "build_palette",
    "generate_wallpaper",
    "get_wallpaper_jpeg_bytes",
    "generate_android_theme",
    "generate_desktop_theme",
    "generate_desktop_palette_text",
    "render_theme_preview",
    "render_preview_to_bytes"
]
