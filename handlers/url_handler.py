"""
URL Image Handler: extracts themes from direct image links, Pinterest, Imgur, etc.
"""

from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
import aiohttp
import io
import logging
from handlers.session_manager import session_manager
from theme_engine.preview_generator import render_preview_to_bytes
from handlers.keyboards import get_theme_editor_keyboard

logger = logging.getLogger(__name__)
router = Router(name="url_router")


@router.message(F.text.regexp(r"^https?://[^\s]+\.(jpg|jpeg|png|webp)(\?[^\s]*)?$"))
async def handle_direct_image_url(message: Message):
    """Handles direct image links."""
    url = message.text.strip()
    user_id = message.from_user.id
    
    status_msg = await message.answer("🌐 <i>Скачиваю изображение по ссылке и создаю тему...</i>", parse_mode="HTML")
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as client:
            async with client.get(url) as resp:
                if resp.status != 200:
                    await status_msg.edit_text(f"❌ Не удалось загрузить изображение (HTTP статус: {resp.status}).")
                    return
                
                content_type = resp.headers.get("Content-Type", "")
                if "image" not in content_type and not url.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    await status_msg.edit_text("❌ Ссылка не является прямым изображением.")
                    return
                
                image_bytes = await resp.read()
                if len(image_bytes) > 20 * 1024 * 1024:
                    await status_msg.edit_text("⚠️ Изображение превышает лимит в 20 МБ.")
                    return

        # Process downloaded image
        session = session_manager.create_session(user_id, image_bytes)
        palette = session.get_palette()
        wallpaper = session.get_wallpaper(width=800, height=820)
        
        preview_bytes = render_preview_to_bytes(palette, wallpaper, session.extracted_colors)
        photo_file = BufferedInputFile(preview_bytes, filename="url_theme_preview.jpg")
        
        caption = (
            "✨ <b>Тема успешно создана по вашей ссылке!</b>\n\n"
            f"• <b>Режим:</b> {session.config.mode.upper()}\n"
            f"• <b>Основной акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
            f"• <b>Второй цвет:</b> <code>{palette.hex_secondary_accent.upper()}</code>\n"
            f"• <b>Фон чата:</b> <code>{palette.hex_bg.upper()}</code>\n\n"
            "🎛 <i>Настройте тему или скачайте для вашей платформы:</i>"
        )
        
        kb = get_theme_editor_keyboard(session.config, palette, session.extracted_colors)
        await message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.exception("Error downloading image from URL %s: %s", url, e)
        await status_msg.edit_text(f"❌ Ошибка при загрузке изображения: {str(e)}")
