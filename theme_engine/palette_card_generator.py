"""
Palette Card Generator for Telegram Theme Studio.
Generates a standalone high-resolution color swatch card image (PNG) for sharing.
"""

from typing import List, Tuple
import io
import os
from PIL import Image, ImageDraw, ImageFont
from theme_engine.palette import ResolvedThemePalette
from theme_engine.color_extractor import ExtractedColor, rgb_to_hex
from theme_engine.preview_generator import get_font, draw_rounded_rect


def generate_palette_card(
    palette: ResolvedThemePalette,
    extracted_colors: List[ExtractedColor],
    width: int = 1200,
    height: int = 800
) -> Image.Image:
    """
    Renders a premium designer-grade color palette swatch card with HEX, RGB, and color names.
    """
    is_dark = palette.mode in ("dark", "amoled")
    bg_color = (18, 20, 26) if is_dark else (245, 247, 252)
    card_bg = (26, 30, 38) if is_dark else (255, 255, 255)
    border_color = (45, 52, 65) if is_dark else (225, 230, 240)
    text_main = (255, 255, 255) if is_dark else (20, 24, 32)
    text_sub = (140, 150, 170) if is_dark else (100, 110, 125)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    font_title = get_font(32, bold=True)
    font_sub = get_font(18, bold=False)
    font_chip_title = get_font(17, bold=True)
    font_chip_code = get_font(15, bold=False)
    font_chip_role = get_font(13, bold=True)

    # Header
    draw.text((60, 45), "🎨 Telegram Theme Studio — Цветовая палитра", fill=text_main, font=font_title)
    mode_text = "Тёмная тема (Dark)" if palette.mode == "dark" else ("AMOLED (OLED Black)" if palette.mode == "amoled" else "Светлая тема (Light)")
    draw.text((60, 90), f"Режим: {mode_text}  •  Всего оттенков: {len(extracted_colors)}", fill=text_sub, font=font_sub)

    # Swatch grid (2 rows of 4 columns)
    start_x = 60
    start_y = 150
    cols = 4
    chip_w = (width - 120 - (cols - 1) * 20) // cols
    chip_h = 270

    display_colors = extracted_colors[:8]

    for i, col in enumerate(display_colors):
        r_idx = i // cols
        c_idx = i % cols
        x = start_x + c_idx * (chip_w + 20)
        y = start_y + r_idx * (chip_h + 20)

        # Draw card container
        draw_rounded_rect(draw, (x, y, x + chip_w, y + chip_h), radius=16, fill=card_bg, outline=border_color, width=1)

        # Color Block
        draw_rounded_rect(draw, (x + 12, y + 12, x + chip_w - 12, y + 150), radius=12, fill=col.rgb)

        # Role badge if primary/secondary
        role_text = "Акцент 1" if i == 0 else ("Акцент 2" if i == 1 else f"Оттенок {i+1}")
        draw.text((x + 16, y + 165), role_text.upper(), fill=palette.primary_accent if i < 2 else text_sub, font=font_chip_role)
        
        # Color Name
        draw.text((x + 16, y + 188), col.name, fill=text_main, font=font_chip_title)
        
        # Hex Code
        draw.text((x + 16, y + 215), f"HEX: {col.hex.upper()}", fill=text_main, font=font_chip_code)
        
        # RGB Code
        draw.text((x + 16, y + 238), f"RGB: {col.r}, {col.g}, {col.b}", fill=text_sub, font=font_chip_code)

    # Footer
    draw.text((60, height - 40), "✨ Создано с помощью Telegram Theme Bot", fill=text_sub, font=get_font(14))

    return img


def generate_palette_card_bytes(
    palette: ResolvedThemePalette,
    extracted_colors: List[ExtractedColor]
) -> bytes:
    """Return PNG bytes of the color palette card."""
    img = generate_palette_card(palette, extracted_colors)
    bio = io.BytesIO()
    img.save(bio, format="PNG", optimize=True)
    return bio.getvalue()
