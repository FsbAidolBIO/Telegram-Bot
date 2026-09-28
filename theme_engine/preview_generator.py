"""
Preview generator module for Telegram themes.
Renders an ultra-clean realistic Telegram chat mockup and color palette card.
"""

from typing import List, Tuple, Optional
import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from theme_engine.palette import ResolvedThemePalette
from theme_engine.color_extractor import ExtractedColor, rgb_to_hex


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Load a system TrueType font or fallback to default."""
    font_paths = [
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
    # (Top 0 to 820 is Phone Mockup Screen, 820 to 1000 is Swatch Bar)
    screen_w = width
    screen_h = 820
    
    # Render Wallpaper into Chat Screen Area
    chat_wall_h = screen_h - 65 - 65 # between top bar (65) and bottom bar (65)
    wall_crop = wallpaper.resize((screen_w, chat_wall_h), Image.Resampling.LANCZOS)
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

    # Title & Subtitle
    draw.text((115, 14), "Telegram Theme Studio", fill=palette.text_primary, font=font_title)
    draw.text((115, 38), "в сети", fill=palette.primary_accent, font=font_subtitle)

    # Top right icons (Search & More)
    draw.text((screen_w - 75, 20), "🔍", fill=palette.text_secondary, font=get_font(16))
    draw.text((screen_w - 35, 18), "⋮", fill=palette.text_primary, font=font_title)

    # 2. Date Badge in Chat
    date_text = "Сегодня"
    date_bbox = font_time.getbbox(date_text)
    dw = date_bbox[2] - date_bbox[0] + 20
    dh = 24
    dx = (screen_w - dw) // 2
    dy = 85
    # Semi-transparent pill
    badge_bg = (30, 30, 35) if palette.mode in ("dark", "amoled") else (220, 225, 230)
    draw_rounded_rect(draw, (dx, dy, dx + dw, dy + dh), radius=12, fill=badge_bg)
    draw.text((dx + 10, dy + 5), date_text, fill=palette.text_secondary, font=font_time)

    # 3. Incoming Message Bubble 1
    # Small avatar for incoming
    in_av_box = (15, 150, 47, 182)
    draw.ellipse(in_av_box, fill=palette.secondary_accent)
    draw.text((24, 157), "AI", fill=(255, 255, 255), font=get_font(12, bold=True))

    in1_x, in1_y = 55, 130
    in1_w, in1_h = 480, 75
    draw_rounded_rect(draw, (in1_x, in1_y, in1_x + in1_w, in1_y + in1_h), radius=16, fill=palette.in_bubble_bg)
    draw.text((in1_x + 16, in1_y + 12), "Привет! Как тебе новая тема?", fill=palette.in_bubble_text, font=font_body)
    draw.text((in1_x + 16, in1_y + 36), "Цветовая палитра взята с твоего фото ✨", fill=palette.in_bubble_text, font=font_body)
    draw.text((in1_x + in1_w - 55, in1_y + in1_h - 22), "14:20", fill=palette.in_bubble_time, font=font_time)

    # 4. Outgoing Message Bubble
    out1_w, out1_h = 490, 75
    out1_x = screen_w - out1_w - 20
    out1_y = 225
    draw_rounded_rect(draw, (out1_x, out1_y, out1_x + out1_w, out1_y + out1_h), radius=16, fill=palette.out_bubble_bg)
    draw.text((out1_x + 16, out1_y + 12), "Выглядит шикарно! Контраст и оттенки", fill=palette.out_bubble_text, font=font_body)
    draw.text((out1_x + 16, out1_y + 36), "подобраны идеально. Уже ставлю себе 🚀", fill=palette.out_bubble_text, font=font_body)
    draw.text((out1_x + out1_w - 70, out1_y + out1_h - 22), "14:21  ✓✓", fill=palette.out_bubble_time, font=font_time)

    # 5. Incoming Message Bubble 2 (Audio / Status / Feature Pill)
    in2_x, in2_y = 55, 320
    in2_w, in2_h = 510, 85
    draw_rounded_rect(draw, (in2_x, in2_y, in2_x + in2_w, in2_y + in2_h), radius=16, fill=palette.in_bubble_bg)
    
    # Reply bar inside bubble
    draw.line([(in2_x + 16, in2_y + 12), (in2_x + 16, in2_y + 40)], fill=palette.primary_accent, width=3)
    draw.text((in2_x + 26, in2_y + 10), "Telegram Theme Engine", fill=palette.primary_accent, font=get_font(13, bold=True))
    draw.text((in2_x + 26, in2_y + 26), "Android (.attheme) + PC (.tdesktop-theme)", fill=palette.text_secondary, font=font_subtitle)
    
    draw.text((in2_x + 16, in2_y + 50), "Готово к установке в 1 клик на любом устройстве!", fill=palette.in_bubble_text, font=font_body)
    draw.text((in2_x + in2_w - 55, in2_y + in2_h - 22), "14:22", fill=palette.in_bubble_time, font=font_time)

    # 6. Bottom Message Input Bar
    input_y = screen_h - 65
    draw.rectangle([(0, input_y), (screen_w, screen_h)], fill=palette.input_bar_bg)
    draw.line([(0, input_y), (screen_w, input_y)], fill=palette.separator_line, width=1)

    # Emoji icon
    draw.text((18, input_y + 18), "😊", fill=palette.text_secondary, font=get_font(18))

    # Placeholder pill
    pill_w = screen_w - 140
    draw_rounded_rect(draw, (55, input_y + 10, 55 + pill_w, input_y + 54), radius=22, fill=palette.bg_surface)
    draw.text((75, input_y + 22), "Сообщение...", fill=palette.input_bar_hint, font=font_body)
    
    # Paperclip attachment icon
    draw.text((55 + pill_w - 38, input_y + 18), "📎", fill=palette.text_secondary, font=get_font(18))

    # Send Circular Button (in accent color)
    send_x = screen_w - 58
    send_y = input_y + 10
    draw.ellipse((send_x, send_y, send_x + 44, send_y + 44), fill=palette.send_button)
    draw.text((send_x + 14, send_y + 10), "➤", fill=palette.unread_badge_text, font=get_font(16, bold=True))

    # 7. Bottom Palette Swatches Section (820px to 1000px)
    swatch_bg = (14, 16, 20) if palette.mode in ("dark", "amoled") else (235, 238, 243)
    draw.rectangle([(0, screen_h), (width, height)], fill=swatch_bg)
    draw.line([(0, screen_h), (width, screen_h)], fill=palette.separator_line, width=1)

    # Title for Palette
    mode_titles = {
        "dark": "🌙 Тёмная тема (Dark)",
        "light": "☀️ Светлая тема (Light)",
        "amoled": "🖤 AMOLED (OLED Black)"
    }
    mode_label = mode_titles.get(palette.mode, "🎨 Пользовательская тема")
    draw.text((25, screen_h + 12), f"Палитра темы — {mode_label}", fill=palette.text_primary, font=get_font(15, bold=True))

    # 6 Swatch tiles
    swatches_data = [
        ("Акцент 1", palette.primary_accent, palette.hex_primary_accent),
        ("Акцент 2", palette.secondary_accent, palette.hex_secondary_accent),
        ("Фон", palette.bg_color, palette.hex_bg),
        ("Входящие", palette.in_bubble_bg, palette.hex_in_bubble),
        ("Исходящие", palette.out_bubble_bg, palette.hex_out_bubble),
        ("Текст", palette.text_primary, palette.hex_text),
    ]

    tile_w = 112
    tile_h = 95
    spacing = 10
    start_x = (width - (len(swatches_data) * tile_w + (len(swatches_data) - 1) * spacing)) // 2
    swatch_y = screen_h + 42

    for i, (label, color_rgb, hex_val) in enumerate(swatches_data):
        tx = start_x + i * (tile_w + spacing)
        # Background card for swatch tile
        draw_rounded_rect(draw, (tx, swatch_y, tx + tile_w, swatch_y + tile_h), radius=10, fill=palette.bg_surface, outline=palette.separator_line)
        
        # Color circle / pill
        draw_rounded_rect(draw, (tx + 12, swatch_y + 10, tx + tile_w - 12, swatch_y + 44), radius=6, fill=color_rgb)
        
        # Label & Hex
        draw.text((tx + 10, swatch_y + 52), label, fill=palette.text_secondary, font=font_small)
        draw.text((tx + 10, swatch_y + 72), hex_val.upper(), fill=palette.text_primary, font=font_hex)

    return card


def render_preview_to_bytes(
    palette: ResolvedThemePalette,
    wallpaper: Image.Image,
    extracted_colors: List[ExtractedColor]
) -> bytes:
    """Render preview card and return as PNG/JPEG bytes."""
    img = render_theme_preview(palette, wallpaper, extracted_colors)
    bio = io.BytesIO()
    img.save(bio, format="JPEG", quality=90, optimize=True)
    return bio.getvalue()
