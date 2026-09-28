"""
Image reception, file processing, and custom hex color handlers.
Optimized with non-blocking async execution and instant rendering.
"""

from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile
import io
import asyncio
import logging
from handlers.session_manager import session_manager
from theme_engine.preview_generator import render_preview_to_bytes
from theme_engine.color_extractor import is_valid_hex, calculate_contrast_ratio, get_wcag_badge
from handlers.keyboards import get_theme_editor_keyboard

logger = logging.getLogger(__name__)
router = Router(name="image_router")


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    """Handles compressed photo messages."""
    user_id = message.from_user.id
    photo = message.photo[-1]
    
    status_msg = await message.answer("🎨 <i>Анализирую цвета скриншота и создаю тему...</i>", parse_mode="HTML")
    
    try:
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        image_bytes = file_io.getvalue()
        
        # Async session creation and color extraction
        session = await asyncio.to_thread(session_manager.create_session, user_id, image_bytes)
        palette = session.get_palette()
        
        # Async preview generation
        preview_bytes = await asyncio.to_thread(session.get_rendered_preview_bytes)
        photo_file = BufferedInputFile(preview_bytes, filename="theme_preview.jpg")
        
        contrast = calculate_contrast_ratio(palette.in_bubble_text, palette.in_bubble_bg)
        wcag_badge = get_wcag_badge(contrast)

        caption = (
            "✨ <b>Тема успешно сгенерирована!</b>\n\n"
            f"• <b>Режим:</b> {session.config.mode.upper()}\n"
            f"• <b>Основной акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
            f"• <b>Второй цвет:</b> <code>{palette.hex_secondary_accent.upper()}</code>\n"
            f"• <b>Фон чата:</b> <code>{palette.hex_bg.upper()}</code>\n"
            f"• <b>Обои:</b> {session.config.wallpaper_mode}\n"
            f"• <b>Читаемость:</b> {wcag_badge}\n\n"
            "🎛 <i>Выберите цвет или настройте тему на кнопках ниже:</i>\n"
            "💡 <i>(Вы также можете отправить свой HEX-код сообщением, например <code>#FF5500</code>)</i>"
        )
        
        kb = get_theme_editor_keyboard(session.config, palette, session.extracted_colors)
        
        await message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
        try:
            await status_msg.delete()
        except Exception:
            pass
        
    except Exception as e:
        logger.exception("Error processing photo: %s", e)
        await status_msg.edit_text(f"❌ Произошла ошибка при обработке изображения: {str(e)}")


@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    """Handles uncompressed image documents (PNG, JPG, WEBP)."""
    doc = message.document
    mime = (doc.mime_type or "").lower()
    fname = (doc.file_name or "").lower()
    
    is_image = mime.startswith("image/") or fname.endswith((".png", ".jpg", ".jpeg", ".webp"))
    if not is_image:
        return
        
    if doc.file_size and doc.file_size > 25 * 1024 * 1024:
        await message.answer("⚠️ Файл слишком большой. Пожалуйста, отправьте изображение размером до 25 МБ.")
        return

    user_id = message.from_user.id
    status_msg = await message.answer("🎨 <i>Загружаю файл и извлекаю цветовую палитру...</i>", parse_mode="HTML")

    try:
        file_io = io.BytesIO()
        await bot.download(doc, destination=file_io)
        image_bytes = file_io.getvalue()
        
        session = await asyncio.to_thread(session_manager.create_session, user_id, image_bytes)
        palette = session.get_palette()
        
        preview_bytes = await asyncio.to_thread(session.get_rendered_preview_bytes)
        photo_file = BufferedInputFile(preview_bytes, filename="theme_preview.jpg")
        
        contrast = calculate_contrast_ratio(palette.in_bubble_text, palette.in_bubble_bg)
        wcag_badge = get_wcag_badge(contrast)

        caption = (
            "✨ <b>Тема успешно сгенерирована из файла!</b>\n\n"
            f"• <b>Режим:</b> {session.config.mode.upper()}\n"
            f"• <b>Основной акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
            f"• <b>Второй цвет:</b> <code>{palette.hex_secondary_accent.upper()}</code>\n"
            f"• <b>Фон чата:</b> <code>{palette.hex_bg.upper()}</code>\n"
            f"• <b>Обои:</b> {session.config.wallpaper_mode}\n"
            f"• <b>Читаемость:</b> {wcag_badge}\n\n"
            "🎛 <i>Выберите цвет или настройте тему:</i>"
        )
        
        kb = get_theme_editor_keyboard(session.config, palette, session.extracted_colors)
        
        await message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
        try:
            await status_msg.delete()
        except Exception:
            pass
            
    except Exception as e:
        logger.exception("Error processing document image: %s", e)
        await status_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")


@router.message(F.text)
async def handle_custom_hex_or_text(message: Message):
    """Handles direct HEX color input (#RRGGBB)."""
    text = (message.text or "").strip()
    user_id = message.from_user.id
    session = session_manager.get_session(user_id)
    
    if not session:
        return
        
    if is_valid_hex(text):
        success = session.set_custom_accent(text)
        if success:
            palette = session.get_palette()
            preview_bytes = await asyncio.to_thread(session.get_rendered_preview_bytes)
            photo_file = BufferedInputFile(preview_bytes, filename="theme_preview.jpg")
            
            contrast = calculate_contrast_ratio(palette.in_bubble_text, palette.in_bubble_bg)
            wcag_badge = get_wcag_badge(contrast)

            caption = (
                f"🎨 <b>Пользовательский акцент установлен:</b> <code>{text.upper()}</code>\n\n"
                f"• <b>Режим:</b> {session.config.mode.upper()}\n"
                f"• <b>Основной акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
                f"• <b>Фон чата:</b> <code>{palette.hex_bg.upper()}</code>\n"
                f"• <b>Читаемость:</b> {wcag_badge}\n\n"
                "🎛 <i>Вы можете продолжить настройку на кнопках:</i>"
            )
            
            kb = get_theme_editor_keyboard(session.config, palette, session.extracted_colors)
            await message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
