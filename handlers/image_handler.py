"""
Image reception, file processing, and custom hex color handlers.
"""

from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile
import io
import logging
from handlers.session_manager import session_manager
from theme_engine.preview_generator import render_preview_to_bytes
from theme_engine.color_extractor import is_valid_hex
from handlers.keyboards import get_theme_editor_keyboard

logger = logging.getLogger(__name__)
router = Router(name="image_router")


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    """Handles compressed photo messages."""
    user_id = message.from_user.id
    
    # Pick highest resolution
    photo = message.photo[-1]
    
    status_msg = await message.answer("🎨 <i>Анализирую цвета скриншота и создаю тему...</i>", parse_mode="HTML")
    
    try:
        # Download file to memory
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        image_bytes = file_io.getvalue()
        
        # Initialize session
        session = session_manager.create_session(user_id, image_bytes)
        palette = session.get_palette()
        wallpaper = session.get_wallpaper(width=800, height=820)
        
        # Render preview card
        preview_bytes = render_preview_to_bytes(palette, wallpaper, session.extracted_colors)
        photo_file = BufferedInputFile(preview_bytes, filename="theme_preview.jpg")
        
        caption = (
            "✨ <b>Тема успешно сгенерирована!</b>\n\n"
            f"• <b>Режим:</b> {session.config.mode.upper()}\n"
            f"• <b>Акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
            f"• <b>Фон:</b> <code>{palette.hex_bg.upper()}</code>\n"
            f"• <b>Обои:</b> {session.config.wallpaper_mode}\n\n"
            "🎛 <i>Настройте цвета или скачайте тему для вашей платформы:</i>\n"
            "💡 <i>(Вы также можете отправить свой HEX-код, например <code>#FF5500</code>)</i>"
        )
        
        kb = get_theme_editor_keyboard(session.config, palette, len(session.extracted_colors))
        
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
        return  # Ignore non-image documents
        
    if doc.file_size and doc.file_size > 20 * 1024 * 1024:
        await message.answer("⚠️ Файл слишком большой. Пожалуйста, отправьте изображение размером до 20 МБ.")
        return

    user_id = message.from_user.id
    status_msg = await message.answer("🎨 <i>Загружаю файл и извлекаю цветовую палитру...</i>", parse_mode="HTML")

    try:
        file_io = io.BytesIO()
        await bot.download(doc, destination=file_io)
        image_bytes = file_io.getvalue()
        
        session = session_manager.create_session(user_id, image_bytes)
        palette = session.get_palette()
        wallpaper = session.get_wallpaper(width=800, height=820)
        
        preview_bytes = render_preview_to_bytes(palette, wallpaper, session.extracted_colors)
        photo_file = BufferedInputFile(preview_bytes, filename="theme_preview.jpg")
        
        caption = (
            "✨ <b>Тема успешно сгенерирована из файла!</b>\n\n"
            f"• <b>Режим:</b> {session.config.mode.upper()}\n"
            f"• <b>Акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
            f"• <b>Фон:</b> <code>{palette.hex_bg.upper()}</code>\n"
            f"• <b>Обои:</b> {session.config.wallpaper_mode}\n\n"
            "🎛 <i>Настройте цвета или скачайте готовую тему:</i>"
        )
        
        kb = get_theme_editor_keyboard(session.config, palette, len(session.extracted_colors))
        
        await message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
        try:
            await status_msg.delete()
        except Exception:
            pass
        
    except Exception as e:
        logger.exception("Error processing document image: %s", e)
        await status_msg.edit_text(f"❌ Не удалось обработать файл: {str(e)}")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_custom_text(message: Message):
    """Handles custom hex color input (e.g. #FF5500 or FF0055)."""
    text = message.text.strip()
    user_id = message.from_user.id
    
    if is_valid_hex(text):
        session = session_manager.get_session(user_id)
        if not session:
            await message.answer(
                "🎨 Вы отправили HEX-цвет, но сначала отправьте скриншот или фото, чтобы создать тему!\n"
                "Либо введите /random для случайной темы."
            )
            return
            
        success = session.set_custom_accent(text)
        if success:
            palette = session.get_palette()
            wallpaper = session.get_wallpaper(width=800, height=820)
            preview_bytes = render_preview_to_bytes(palette, wallpaper, session.extracted_colors)
            photo_file = BufferedInputFile(preview_bytes, filename="theme_preview.jpg")
            
            caption = (
                f"🎯 <b>Применен пользовательский акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n\n"
                f"• <b>Режим:</b> {session.config.mode.upper()}\n"
                f"• <b>Фон:</b> <code>{palette.hex_bg.upper()}</code>\n"
                f"• <b>Обои:</b> {session.config.wallpaper_mode}\n\n"
                "🎛 <i>Продолжайте настройку или скачайте файл темы:</i>"
            )
            kb = get_theme_editor_keyboard(session.config, palette, len(session.extracted_colors))
            await message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
        else:
            await message.answer("⚠️ Не удалось применить HEX-код. Формат: <code>#RRGGBB</code> (например, <code>#3A86FF</code>).", parse_mode="HTML")
    else:
        await message.answer(
            "📸 <b>Отправьте скриншот или фото</b>, чтобы создать из него тему!\n"
            "Либо используйте команду /random для демонстрации."
        )
