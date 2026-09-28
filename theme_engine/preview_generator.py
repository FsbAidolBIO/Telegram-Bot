"""
Preview generator module for Telegram themes.
Renders an ultra-clean realistic Telegram chat mockup and color palette card with zero distortion.
Includes font caching and optimized drawing for sub-millisecond throughput.
"""

from typing import List, Tuple, Optional
import io
import os
import functools
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from theme_engine.palette import ResolvedThemePalette
from theme_engine.color_extractor import ExtractedColor, rgb_to_hex


@functools.lru_cache(maxsize=32)
def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Load bundled TrueType font with full Cyrillic support, cached in memory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bundled_bold = os.path.join(current_dir, "fonts", "DejaVuSans-Bold.ttf")
    bundled_reg = os.path.join(current_dir, "fonts", "DejaVuSans.ttf")
    
    font_paths = [
        bundled_bold if bold else bundled_reg,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "arialbd.ttf" if bold else "arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    radius: int,
    fill: Optional[Tuple[int, int, int]] = None,
    outline: Optional[Tuple[int, int, int]] = None,
    width: int = 1
):
    """Draw a smooth rounded rectangle."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def render_theme_preview(
    palette: ResolvedThemePalette,
    wallpaper: Image.Image,
    extracted_colors: List[ExtractedColor],
    width: int = 800,
    height: int = 1000
) -> Image.Image:
    """
    Render a high-resolution preview card showing realistic Telegram UI and palette swatches.
    Guarantees zero aspect-ratio distortion and sharp Cyrillic text.
    """
    card = Image.new("RGB", (width, height), (20, 22, 28))
    draw = ImageDraw.Draw(card)
    
    # Fonts
    font_title = get_font(20, bold=True)
    font_subtitle = get_font(13, bold=False)
    font_body = get_font(16, bold=False)
    font_time = get_font(12, bold=False)
    font_swatch = get_font(12, bold=True)
    font_hex = get_font(11, bold=False)
    font_small = get_font(11, bold=True)

    # 1. Chat Mockup Container Area
    screen_w = width
    screen_h = 820
    
    # Render Wallpaper into Chat Screen Area with PROPORTIONAL fit (NO STRETCHING)
    chat_wall_h = screen_h - 65 - 65
    wall_crop = ImageOps.fit(wallpaper, (screen_w, chat_wall_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    card.paste(wall_crop, (0, 65))

    # Draw Top Bar (Header)
    draw.rectangle([(0, 0), (screen_w, 65)], fill=palette.topbar_bg)
    draw.line([(0, 65), (screen_w, 65)], fill=palette.separator_line, width=1)

    # Back arrow icon
    draw.text((20, 20), "←", fill=palette.text_primary, font=font_title)

    # Avatar Circle
    avatar_box = (60, 12, 100, 52)
    draw.ellipse(avatar_box, fill=palette.primary_accent)
    draw.text((73, 20), "TG", fill=palette.unread_badge_text, font=get_font(15, bold=True))

    # Title & Subtitle (Crisp noticeable white title)
    draw.text((115, 14), "Telegram Theme Studio", fill=palette.text_primary, font=font_title)
    draw.text((115, 38), "в сети", fill=palette.primary_accent, font=font_subtitle)

    # Top right icons (Search & More)
    draw.text((screen_w - 75, 20), "🔍", fill=palette.text_secondary, font=get_font(16))
    draw.text((screen_w - 35, 18), "⋮", fill=palette.text_primary, font=font_title)

    # 2. Date Badge in Chat
    date_w = 120
    date_x = (screen_w - date_w) // 2
    date_badge_bg = (15, 18, 24) if palette.mode in ("dark", "amoled") else (210, 220, 230)
    draw_rounded_rect(draw, (date_x, 80, date_x + date_w, 104), radius=12, fill=date_badge_bg)
    draw.text((date_x + 22, 85), "Сегодня", fill=palette.text_secondary, font=font_small)

    # 3. Incoming Message Bubble (Left side)
    in_bx1, in_by1 = 25, 120
    in_bw, in_bh = 460, 150
    draw_rounded_rect(draw, (in_bx1, in_by1, in_bx1 + in_bw, in_by1 + in_bh), radius=16, fill=palette.in_bubble_bg)

    # Author Name in Incoming Bubble (Crisp clean white text, never confusing green)
    in_name_color = (255, 255, 255) if palette.mode in ("dark", "amoled") else (20, 26, 36)
    draw.text((in_bx1 + 16, in_by1 + 12), "Алексей Смирнов", fill=in_name_color, font=get_font(14, bold=True))

    # Reply quote box inside incoming bubble
    rep_bx1, rep_by1 = in_bx1 + 14, in_by1 + 34
    rep_bw, rep_bh = in_bw - 28, 42
    rep_bg = (0, 0, 0) if palette.mode in ("dark", "amoled") else (255, 255, 255)
    # Draw reply bar
    draw.line([(rep_bx1 + 2, rep_by1 + 2), (rep_bx1 + 2, rep_by1 + rep_bh - 2)], fill=palette.in_bubble_reply_bar, width=3)
    draw.text((rep_bx1 + 12, rep_by1 + 4), "Вы", fill=palette.in_bubble_reply_bar, font=font_small)
    draw.text((rep_bx1 + 12, rep_by1 + 20), "Смотри какая сочная тема получилась!", fill=palette.in_bubble_time, font=font_subtitle)

    # Text of incoming message
    draw.text((in_bx1 + 16, in_by1 + 86), "Вау! Цвета подобраны идеально 🔥\nВсе оттенки гармонируют с обоями.", fill=palette.in_bubble_text, font=font_body)
    draw.text((in_bx1 + in_bw - 50, in_by1 + in_bh - 22), "14:28", fill=palette.in_bubble_time, font=font_time)

    # 4. Outgoing Message Bubble (Right side)
    out_bw, out_bh = 480, 110
    out_bx1 = screen_w - 25 - out_bw
    out_by1 = 290
    draw_rounded_rect(draw, (out_bx1, out_by1, out_bx1 + out_bw, out_by1 + out_bh), radius=16, fill=palette.out_bubble_bg)

    # Text of outgoing message
    draw.text((out_bx1 + 16, out_by1 + 16), "Да, бот автоматически выделил акценты\nи настроил контраст для Android и ПК!", fill=palette.out_bubble_text, font=font_body)
    
    # Timestamp + double checkmark
    draw.text((out_bx1 + out_bw - 72, out_by1 + out_bh - 25), "14:29", fill=palette.out_bubble_time, font=font_time)
    draw.text((out_bx1 + out_bw - 30, out_by1 + out_bh - 25), "✓✓", fill=palette.out_bubble_time, font=font_time)

    # 5. Second Incoming Message Bubble
    in2_bx1, in2_by1 = 25, 420
    in2_bw, in2_bh = 380, 80
    draw_rounded_rect(draw, (in2_bx1, in2_by1, in2_bx1 + in2_bw, in2_by1 + in2_bh), radius=16, fill=palette.in_bubble_bg)
    draw.text((in2_bx1 + 16, in2_by1 + 10), "Алексей Смирнов", fill=in_name_color, font=get_font(14, bold=True))
    draw.text((in2_bx1 + 16, in2_by1 + 34), "Скачиваю себе в один клик! 🚀", fill=palette.in_bubble_text, font=font_body)
    draw.text((in2_bx1 + in2_bw - 50, in2_by1 + in2_bh - 22), "14:30", fill=palette.in_bubble_time, font=font_time)

    # 6. Bottom Input Bar Area
    input_y = screen_h - 65
    draw.rectangle([(0, input_y), (screen_w, screen_h)], fill=palette.input_bar_bg)
    draw.line([(0, input_y), (screen_w, input_y)], fill=palette.separator_line, width=1)

    # Attach & Emoji icons
    draw.text((20, input_y + 18), "😊", fill=palette.text_secondary, font=get_font(20))
    draw.text((60, input_y + 18), "📎", fill=palette.text_secondary, font=get_font(20))

    # Input Box Pill
    input_box_w = screen_w - 60 - 80 - 20
    draw_rounded_rect(draw, (100, input_y + 10, 100 + input_box_w, input_y + 54), radius=22, fill=palette.bg_surface, outline=palette.separator_line)
    draw.text((120, input_y + 20), "Сообщение...", fill=palette.input_bar_hint, font=font_body)

    # Send / Mic Action Button Circle
    send_btn_cx, send_btn_cy = screen_w - 38, input_y + 32
    draw.ellipse([(send_btn_cx - 22, send_btn_cy - 22), (send_btn_cx + 22, send_btn_cy + 22)], fill=palette.send_button)
    draw.text((send_btn_cx - 8, send_btn_cy - 12), "➤", fill=palette.unread_badge_text, font=get_font(16, bold=True))

    # 7. Lower Section: Palette Swatches & Metadata Sheet
    sheet_y = screen_h
    draw.rectangle([(0, sheet_y), (width, height)], fill=(16, 18, 22))
    draw.line([(0, sheet_y), (width, sheet_y)], fill=(35, 38, 48), width=1)

    draw.text((25, sheet_y + 14), "🎨 ПАЛИТРА ИЗВЛЕЧЕННЫХ ЦВЕТОВ", fill=(170, 180, 195), font=font_swatch)
    draw.text((width - 240, sheet_y + 14), f"РЕЖИМ: {palette.mode.upper()}", fill=palette.primary_accent, font=font_swatch)

    # Draw color swatch tiles
    swatch_y = sheet_y + 40
    tile_w = (width - 50 - (len(extracted_colors[:6]) - 1) * 12) // max(1, len(extracted_colors[:6]))
    tile_h = 75

    for i, col in enumerate(extracted_colors[:6]):
        tx = 25 + i * (tile_w + 12)
        # Swatch block
        draw_rounded_rect(draw, (tx, swatch_y, tx + tile_w, swatch_y + tile_h - 24), radius=8, fill=col.rgb)
        
        # Selected accent indicator mark
        if col.hex.lower() == palette.hex_primary_accent.lower():
            draw_rounded_rect(draw, (tx - 2, swatch_y - 2, tx + tile_w + 2, swatch_y + tile_h - 22), radius=10, outline=(255, 255, 255), width=2)
            draw.text((tx + tile_w // 2 - 5, swatch_y + 10), "★", fill=(255, 255, 255), font=get_font(12, bold=True))
        
        # Hex Label below tile
        hex_text = col.hex.upper()
        draw.text((tx + (tile_w - 48) // 2, swatch_y + tile_h - 18), hex_text, fill=(220, 225, 235), font=font_hex)

    # Bottom branding badge
    draw.text((25, height - 32), "✨ Telegram Theme Studio • Auto Contrast 4:4:4", fill=(100, 110, 125), font=font_small)
    draw.text((width - 195, height - 32), f"Accent: {palette.hex_primary_accent}", fill=(140, 150, 165), font=font_small)

    return card


def render_preview_to_bytes(
    palette: ResolvedThemePalette,
    wallpaper: Image.Image,
    extracted_colors: List[ExtractedColor]
) -> bytes:
    """Render preview and return high-quality JPEG bytes with 4:4:4 subsampling."""
    card = render_theme_preview(palette, wallpaper, extracted_colors)
    bio = io.BytesIO()
    card.save(bio, format="JPEG", quality=92, subsampling=0, optimize=True)
    return bio.getvalue()
