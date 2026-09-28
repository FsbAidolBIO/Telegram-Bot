"""
Inline keyboards builder for Telegram theme customizer with interactive color grid.
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from theme_engine.palette import ThemeConfig, ResolvedThemePalette
from theme_engine.color_extractor import ExtractedColor


def get_theme_editor_keyboard(
    config: ThemeConfig,
    palette: ResolvedThemePalette,
    extracted_colors: List[ExtractedColor]
) -> InlineKeyboardMarkup:
    """
    Construct the interactive control panel keyboard with direct color swatches.
    """
    mode_labels = {
        "dark": "🌙 Тёмная",
        "light": "☀️ Светлая",
        "amoled": "🖤 AMOLED"
    }
    mode_text = mode_labels.get(config.mode, "🌓 Режим")

    wallpaper_labels = {
        "blurred": "✨ Размытие",
        "fit_blur": "🖼 Вписать (Без обрезки)",
        "cover": "📐 Заполнить (Cover)",
        "dimmed": "🌑 Затемнение",
        "gradient": "🌈 Градиент",
        "solid": "🎨 Сплошной"
    }
    wall_text = wallpaper_labels.get(config.wallpaper_mode, "🖼 Обои")

    bubble_labels = {
        "vibrant": "💬 Неон/Акцент",
        "dual": "🌈 Двойной цвет",
        "soft": "🌸 Мягкий тинт",
        "glass": "💎 Стекло",
        "minimal": "▫️ Минимал"
    }
    bubble_text = bubble_labels.get(config.bubble_style, "💬 Бабблы")

    tint_labels = {
        "rich": "🌌 Атмосфера: Макс",
        "medium": "🌌 Атмосфера: Сред",
        "subtle": "🌌 Атмосфера: Мин",
        "clean": "🌌 Атмосфера: Выкл"
    }
    tint_text = tint_labels.get(config.chat_tint, "🌌 Атмосфера")

    keyboard = [
        # Row 1: Mode & Wallpaper
        [
            InlineKeyboardButton(text=f"🌓 {mode_text}", callback_data="toggle_mode"),
            InlineKeyboardButton(text=f"🖼 {wall_text}", callback_data="cycle_wallpaper")
        ],
        # Row 2: Bubbles style & Chat Tint
        [
            InlineKeyboardButton(text=f"{bubble_text}", callback_data="cycle_bubble"),
            InlineKeyboardButton(text=f"{tint_text}", callback_data="cycle_chat_tint")
        ],
        # Row 3: Brightness fine-tuning
        [
            InlineKeyboardButton(text="➖ Темнее (-10%)", callback_data="brightness_minus"),
            InlineKeyboardButton(text="➕ Светлее (+10%)", callback_data="brightness_plus")
        ],
        # Row 4: Direct Interactive Color Palette Grid (Top 4 vibrant colors)
    ]

    # Add quick color buttons
    color_buttons = []
    for i, col in enumerate(extracted_colors[:4]):
        is_active = (config.custom_accent_hex is None and config.accent_idx == i)
        prefix = "✓ " if is_active else ""
        btn_text = f"{col.emoji} {prefix}{col.hex.upper()}"
        color_buttons.append(InlineKeyboardButton(text=btn_text, callback_data=f"set_accent_{i}"))
    
    if color_buttons:
        # 2 per row
        keyboard.append(color_buttons[:2])
        if len(color_buttons) > 2:
            keyboard.append(color_buttons[2:4])

    # Row 5: Open full color picker
    keyboard.append([
        InlineKeyboardButton(text="🎨 Открыть все цвета палитры", callback_data="open_palette_picker")
    ])

    # Row 6: Primary download buttons
    keyboard.append([
        InlineKeyboardButton(text="🤖 Скачать для Android (.attheme)", callback_data="download_android")
    ])
    keyboard.append([
        InlineKeyboardButton(text="💻 Скачать для ПК (.tdesktop-theme)", callback_data="download_desktop")
    ])
    
    # Row 7: All-in-one pack & Reset
    keyboard.append([
        InlineKeyboardButton(text="📦 Полный ZIP-архив", callback_data="download_all_zip"),
        InlineKeyboardButton(text="🔄 Сброс", callback_data="reset_settings")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_color_picker_keyboard(extracted_colors: List[ExtractedColor], active_idx: int) -> InlineKeyboardMarkup:
    """
    Submenu displaying all extracted colors for 1-tap selection.
    """
    buttons = []
    row = []
    for i, col in enumerate(extracted_colors):
        is_active = (active_idx == i)
        prefix = "🎯 " if is_active else ""
        btn_text = f"{col.emoji} {prefix}{col.hex.upper()}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"set_accent_{i}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="⬅️ Вернуться в редактор", callback_data="open_editor")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quick_download_keyboard() -> InlineKeyboardMarkup:
    """Keyboard sent along with downloaded files."""
    keyboard = [
        [
            InlineKeyboardButton(text="🎨 Настроить тему заново", callback_data="open_editor"),
            InlineKeyboardButton(text="❓ Как установить тему?", callback_data="show_help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
