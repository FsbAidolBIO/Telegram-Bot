"""
Callback query handlers for interactive theme customizer and file downloads.
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, BufferedInputFile, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
import io
import zipfile
import logging
from handlers.session_manager import session_manager
from handlers.keyboards import (
    get_theme_editor_keyboard,
    get_color_picker_keyboard,
    get_quick_download_keyboard
)
from theme_engine.preview_generator import render_preview_to_bytes
from theme_engine.android_generator import generate_android_theme
from theme_engine.desktop_generator import generate_desktop_theme, generate_desktop_palette_text
from theme_engine.wallpaper_generator import get_wallpaper_jpeg_bytes

logger = logging.getLogger(__name__)
router = Router(name="callbacks_router")


async def update_theme_view(query: CallbackQuery, session):
    """Re-renders the preview card and updates the Telegram message."""
    palette = session.get_palette()
    wallpaper = session.get_wallpaper(width=800, height=820)
    
    preview_bytes = render_preview_to_bytes(palette, wallpaper, session.extracted_colors)
    photo_file = BufferedInputFile(preview_bytes, filename="theme_preview.jpg")
    
    tint_labels = {
        "rich": "Глубокая (22%)",
        "medium": "Умеренная (14%)",
        "subtle": "Мягкая (6%)",
        "clean": "Чистая (0%)"
    }
    tint_name = tint_labels.get(session.config.chat_tint, "Обычная")

    caption = (
        "✨ <b>Настройка темы обновлена!</b>\n\n"
        f"• <b>Режим:</b> {session.config.mode.upper()}\n"
        f"• <b>Основной акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
        f"• <b>Второй цвет:</b> <code>{palette.hex_secondary_accent.upper()}</code>\n"
        f"• <b>Фон чата:</b> <code>{palette.hex_bg.upper()}</code>\n"
        f"• <b>Обои:</b> {session.config.wallpaper_mode}\n"
        f"• <b>Стиль сообщений:</b> {session.config.bubble_style}\n"
        f"• <b>Атмосфера чата:</b> {tint_name}\n\n"
        "🎛 <i>Выберите цвет или параметр на кнопках ниже:</i>"
    )
    
    kb = get_theme_editor_keyboard(session.config, palette, session.extracted_colors)
    media = InputMediaPhoto(media=photo_file, caption=caption, parse_mode="HTML")
    
    try:
        await query.message.edit_media(media=media, reply_markup=kb)
    except TelegramBadRequest as e:
        if "not modified" not in str(e).lower():
            logger.warning("TelegramBadRequest in edit_media: %s", e)
    except Exception as e:
        logger.warning("Failed to edit media: %s", e)
    finally:
        try:
            await query.answer()
        except Exception:
            pass


@router.callback_query(F.data.startswith("set_accent_"))
async def cb_set_accent_index(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла. Отправьте скриншот заново.", show_alert=True)
        return
    idx_str = query.data.split("_")[-1]
    if idx_str.isdigit():
        session.config.set_accent_index(int(idx_str))
    await update_theme_view(query, session)


@router.callback_query(F.data == "open_palette_picker")
async def cb_open_palette_picker(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла. Отправьте скриншот заново.", show_alert=True)
        return
    
    kb = get_color_picker_keyboard(session.extracted_colors, session.config.accent_idx)
    caption = (
        "🎨 <b>Палитра цветов из вашего изображения:</b>\n\n"
        "Нажмите на любой цвет ниже, чтобы мгновенно сделать его основным акцентом чата и интерфейса:\n"
        "💡 <i>(Или отправьте свой HEX-код сообщением в чат, например <code>#FF4500</code>)</i>"
    )
    try:
        await query.message.edit_caption(caption=caption, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logger.warning("Failed to edit caption for color picker: %s", e)
    await query.answer()


@router.callback_query(F.data == "cycle_chat_tint")
async def cb_cycle_chat_tint(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла.", show_alert=True)
        return
    session.config.cycle_chat_tint()
    await update_theme_view(query, session)


@router.callback_query(F.data == "toggle_mode")
async def cb_toggle_mode(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла. Пожалуйста, отправьте скриншот заново.", show_alert=True)
        return
    session.config.cycle_mode()
    await update_theme_view(query, session)


@router.callback_query(F.data == "cycle_wallpaper")
async def cb_cycle_wallpaper(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла. Отправьте фото заново.", show_alert=True)
        return
    session.config.cycle_wallpaper()
    await update_theme_view(query, session)


@router.callback_query(F.data == "cycle_bubble")
async def cb_cycle_bubble(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла. Отправьте фото заново.", show_alert=True)
        return
    session.config.cycle_bubble()
    await update_theme_view(query, session)


@router.callback_query(F.data == "brightness_plus")
async def cb_brightness_plus(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла.", show_alert=True)
        return
    if session.config.brightness_offset < 30:
        session.config.brightness_offset += 10
    await update_theme_view(query, session)


@router.callback_query(F.data == "brightness_minus")
async def cb_brightness_minus(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла.", show_alert=True)
        return
    if session.config.brightness_offset > -30:
        session.config.brightness_offset -= 10
    await update_theme_view(query, session)


@router.callback_query(F.data == "reset_settings")
async def cb_reset_settings(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла.", show_alert=True)
        return
    session.config.mode = "light" if session.is_image_light else "dark"
    session.config.accent_idx = 0
    session.config.bubble_style = "vibrant"
    session.config.chat_tint = "rich"
    session.config.wallpaper_mode = "blurred"
    session.config.brightness_offset = 0
    session.config.custom_accent_hex = None
    await update_theme_view(query, session)


# --- DOWNLOAD HANDLERS ---

@router.callback_query(F.data == "download_android")
async def cb_download_android(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла. Отправьте скриншот заново.", show_alert=True)
        return
    
    await query.answer("⏳ Генерирую тему для Android...")
    
    palette = session.get_palette()
    wallpaper = session.get_wallpaper(width=1080, height=1920)
    attheme_bytes = generate_android_theme(palette, wallpaper, theme_name="Custom Android Theme")
    
    doc = BufferedInputFile(attheme_bytes, filename="Telegram_Android_Theme.attheme")
    
    caption = (
        "🤖 <b>Тема для Telegram Android готова!</b>\n\n"
        "📥 <b>Как применить тему на Android:</b>\n"
        "1. Нажмите на прикрепленный файл <code>.attheme</code> выше.\n"
        "2. В появившемся окне нажмите <b>«Применить тему»</b>.\n"
        "3. Готово! Все цвета и обои установлены автоматически."
    )
    
    await query.message.answer_document(doc, caption=caption, parse_mode="HTML", reply_markup=get_quick_download_keyboard())


@router.callback_query(F.data == "download_desktop")
async def cb_download_desktop(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла. Отправьте скриншот заново.", show_alert=True)
        return
    
    await query.answer("⏳ Генерирую тему для Telegram Desktop...")
    
    palette = session.get_palette()
    wallpaper = session.get_wallpaper(width=1920, height=1080)
    tdesktop_bytes = generate_desktop_theme(palette, wallpaper, theme_name="Custom Desktop Theme")
    
    doc = BufferedInputFile(tdesktop_bytes, filename="Telegram_PC_Theme.tdesktop-theme")
    
    caption = (
        "💻 <b>Тема для Telegram Desktop (ПК) готова!</b>\n\n"
        "📥 <b>Как применить тему на ПК (Windows / macOS / Linux):</b>\n"
        "1. Кликните по файлу <code>.tdesktop-theme</code> в чате.\n"
        "2. В открывшемся окне предпросмотра нажмите <b>«Применить эту тему»</b>.\n"
        "3. Нажмите <b>«Сохранить изменения»</b>."
    )
    
    await query.message.answer_document(doc, caption=caption, parse_mode="HTML", reply_markup=get_quick_download_keyboard())


@router.callback_query(F.data == "download_all_zip")
async def cb_download_all_zip(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла. Отправьте скриншот заново.", show_alert=True)
        return
    
    await query.answer("📦 Собираю полный ZIP-архив...")
    
    palette = session.get_palette()
    wallpaper_phone = session.get_wallpaper(width=1080, height=1920)
    wallpaper_desktop = session.get_wallpaper(width=1920, height=1080)
    
    attheme_bytes = generate_android_theme(palette, wallpaper_phone)
    tdesktop_bytes = generate_desktop_theme(palette, wallpaper_desktop)
    palette_text = generate_desktop_palette_text(palette)
    preview_bytes = render_preview_to_bytes(palette, wallpaper_phone, session.extracted_colors)
    phone_wall_bytes = get_wallpaper_jpeg_bytes(wallpaper_phone, quality=95)
    desk_wall_bytes = get_wallpaper_jpeg_bytes(wallpaper_desktop, quality=95)
    
    readme_text = (
        "===============================================\n"
        "       TELEGRAM THEME PACK - BY THEME BOT      \n"
        "===============================================\n\n"
        f"Mode: {palette.mode.upper()}\n"
        f"Primary Accent Hex: {palette.hex_primary_accent}\n"
        f"Secondary Accent Hex: {palette.hex_secondary_accent}\n"
        f"Background Hex: {palette.hex_bg}\n\n"
        "FILES IN THIS PACK:\n"
        "1. Telegram_Android.attheme - Theme for Android with wallpaper embedded.\n"
        "2. Telegram_Desktop.tdesktop-theme - Theme for Telegram Desktop (PC/Mac/Linux).\n"
        "3. colors.tdesktop-palette - Raw desktop color palette definition.\n"
        "4. wallpaper_mobile.jpg - Full resolution mobile wallpaper.\n"
        "5. wallpaper_desktop.jpg - Full resolution desktop wallpaper.\n"
        "6. theme_preview.jpg - Visual theme preview and color swatches.\n\n"
        "INSTALLATION:\n"
        "- On Android: Send Telegram_Android.attheme to Saved Messages and click on it.\n"
        "- On PC: Send Telegram_Desktop.tdesktop-theme to Saved Messages and click on it.\n"
    )
    
    zip_bio = io.BytesIO()
    with zipfile.ZipFile(zip_bio, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Telegram_Android.attheme", attheme_bytes)
        zf.writestr("Telegram_Desktop.tdesktop-theme", tdesktop_bytes)
        zf.writestr("colors.tdesktop-palette", palette_text.encode("utf-8"))
        zf.writestr("wallpaper_mobile.jpg", phone_wall_bytes)
        zf.writestr("wallpaper_desktop.jpg", desk_wall_bytes)
        zf.writestr("theme_preview.jpg", preview_bytes)
        zf.writestr("README.txt", readme_text.encode("utf-8"))
        
    zip_bytes = zip_bio.getvalue()
    doc = BufferedInputFile(zip_bytes, filename="Telegram_Theme_Pack.zip")
    
    caption = (
        "📦 <b>Полный пакет темы готов!</b>\n\n"
        "В архиве:\n"
        "• 📱 Тема для Android (<code>.attheme</code>)\n"
        "• 💻 Тема для ПК (<code>.tdesktop-theme</code>)\n"
        "• 📄 Цветовая палитра (<code>.tdesktop-palette</code>)\n"
        "• 🖼 HD Обои для телефона и ПК\n"
        "• 🎨 Карточка предпросмотра с HEX-кодами"
    )
    
    await query.message.answer_document(doc, caption=caption, parse_mode="HTML", reply_markup=get_quick_download_keyboard())


@router.callback_query(F.data == "open_editor")
async def cb_open_editor(query: CallbackQuery):
    session = session_manager.get_session(query.from_user.id)
    if not session:
        await query.answer("⚠️ Сессия истекла. Отправьте фото заново.", show_alert=True)
        return
    await update_theme_view(query, session)
