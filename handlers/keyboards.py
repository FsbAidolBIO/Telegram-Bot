"""
Inline keyboards builder for Telegram theme customizer.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from theme_engine.palette import ThemeConfig, ResolvedThemePalette


def get_theme_editor_keyboard(config: ThemeConfig, palette: ResolvedThemePalette, total_colors: int) -> InlineKeyboardMarkup:
    """
    Construct the interactive control panel keyboard for theme customization.
    """
    mode_labels = {
        "dark": "🌙 Тёмная",
        "light": "☀️ Светлая",
        "amoled": "🖤 AMOLED"
    }
    mode_text = mode_labels.get(config.mode, "🌓 Режим")

    wallpaper_labels = {
        "blurred": "✨ Размытие",
        "original": "🖼 Исходник",
        "dimmed": "🌑 Затемнение",
        "gradient": "🌈 Градиент",
        "solid": "🎨 Сплошной"
    }
    wall_text = wallpaper_labels.get(config.wallpaper_mode, "🖼 Обои")

    bubble_labels = {
        "accent": "💬 Акцент",
        "tinted": "🎨 Оттенок",
        "contrast": "⚡ Контраст",
        "minimal": "▫️ Минимал"
    }
    bubble_text = bubble_labels.get(config.bubble_style, "💬 Бабблы")

    accent_text = f"🎨 Акцент ({config.accent_idx + 1}/{total_colors})"

    keyboard = [
        # Row 1: Mode & Accent color
        [
            InlineKeyboardButton(text=f"🌓 {mode_text}", callback_data="toggle_mode"),
            InlineKeyboardButton(text=accent_text, callback_data="cycle_accent")
        ],
        # Row 2: Wallpaper mode & Bubbles style
        [
            InlineKeyboardButton(text=f"🖼 {wall_text}", callback_data="cycle_wallpaper"),
            InlineKeyboardButton(text=f"{bubble_text}", callback_data="cycle_bubble")
        ],
        # Row 3: Brightness fine-tuning
        [
            InlineKeyboardButton(text="➖ Темнее (-10%)", callback_data="brightness_minus"),
            InlineKeyboardButton(text="➕ Светлее (+10%)", callback_data="brightness_plus")
        ],
        # Row 4: Quick color presets
        [
            InlineKeyboardButton(text="⚡ Неон", callback_data="preset_neon"),
            InlineKeyboardButton(text="🌸 Пастель", callback_data="preset_pastel"),
            InlineKeyboardButton(text="💎 Киберпанк", callback_data="preset_cyberpunk")
        ],
        # Row 5: Primary download buttons
        [
            InlineKeyboardButton(text="🤖 Скачать для Android (.attheme)", callback_data="download_android")
        ],
        [
            InlineKeyboardButton(text="💻 Скачать для ПК (.tdesktop-theme)", callback_data="download_desktop")
        ],
        # Row 6: All-in-one pack
        [
            InlineKeyboardButton(text="📦 Скачать полный ZIP-архив", callback_data="download_all_zip"),
            InlineKeyboardButton(text="🔄 Сброс", callback_data="reset_settings")
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_quick_download_keyboard() -> InlineKeyboardMarkup:
    """Keyboard sent along with downloaded files."""
    keyboard = [
        [
            InlineKeyboardButton(text="🎨 Настроить тему заново", callback_data="open_editor"),
            InlineKeyboardButton(text="❓ Как установить тему?", callback_data="show_help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
