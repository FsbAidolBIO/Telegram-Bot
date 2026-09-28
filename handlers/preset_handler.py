"""
Preset theme catalog handlers and inline browsing.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import io
from theme_engine.presets import PRESETS_LIBRARY
from handlers.session_manager import session_manager
from theme_engine.preview_generator import render_preview_to_bytes
from handlers.keyboards import get_theme_editor_keyboard

router = Router(name="presets_router")


def get_presets_menu_keyboard() -> InlineKeyboardMarkup:
    """Construct inline catalog of aesthetic presets."""
    buttons = []
    row = []
    for key, preset in PRESETS_LIBRARY.items():
        btn_text = f"{preset.emoji} {preset.title}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"apply_preset_{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="🎲 Случайная тема", callback_data="demo_random"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="show_help")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("presets"))
async def handle_presets_command(message: Message):
    text = (
        "📚 <b>Каталог готовых дизайнерских тем:</b>\n\n"
        "Выберите любую тему из нашей коллекции ниже, чтобы мгновенно применить её, "
        "посмотреть превью и скачать для Android или ПК:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_presets_menu_keyboard())


@router.callback_query(F.data == "open_presets_catalog")
async def cb_open_presets(query: CallbackQuery):
    text = (
        "📚 <b>Каталог готовых дизайнерских тем:</b>\n\n"
        "Выберите понравившийся стиль для предпросмотра и скачивания:"
    )
    await query.message.answer(text, parse_mode="HTML", reply_markup=get_presets_menu_keyboard())
    await query.answer()


@router.callback_query(F.data.startswith("apply_preset_"))
async def cb_apply_preset(query: CallbackQuery):
    preset_key = query.data.replace("apply_preset_", "")
    preset = PRESETS_LIBRARY.get(preset_key)
    if not preset:
        await query.answer("⚠️ Пресет не найден.", show_alert=True)
        return

    await query.answer(f"✨ Загружаю пресет: {preset.title}...")

    # Generate preset procedural artwork
    preset_img = preset.generate_preset_image(width=1080, height=2400)
    bio = io.BytesIO()
    preset_img.save(bio, format="PNG")
    raw_bytes = bio.getvalue()

    user_id = query.from_user.id
    session = session_manager.create_session(user_id, raw_bytes)
    
    # Override config & extracted colors with preset specifics
    session.config = preset.get_config()
    session.extracted_colors = preset.get_extracted_colors()

    palette = session.get_palette()
    wallpaper = session.get_wallpaper(width=800, height=820)
    
    preview_bytes = render_preview_to_bytes(palette, wallpaper, session.extracted_colors)
    photo_file = BufferedInputFile(preview_bytes, filename="preset_preview.jpg")

    caption = (
        f"{preset.emoji} <b>Пресет: {preset.title}</b>\n"
        f"<i>{preset.description}</i>\n\n"
        f"• <b>Режим:</b> {preset.mode.upper()}\n"
        f"• <b>Основной акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
        f"• <b>Второй цвет:</b> <code>{palette.hex_secondary_accent.upper()}</code>\n"
        f"• <b>Фон:</b> <code>{palette.hex_bg.upper()}</code>\n\n"
        "🎛 <i>Вы можете настроить эту тему под себя или сразу скачать:</i>"
    )

    kb = get_theme_editor_keyboard(session.config, palette, session.extracted_colors)
    await query.message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
