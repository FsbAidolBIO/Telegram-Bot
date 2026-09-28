"""
Saved Themes & Personal Favorites Library with SQLite persistence.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import os
import json
import time
import logging
from handlers.session_manager import session_manager
from theme_engine.preview_generator import render_preview_to_bytes
from theme_engine.palette import ThemeConfig, build_palette
from theme_engine.color_extractor import ExtractedColor, hex_to_rgb
from handlers.keyboards import get_theme_editor_keyboard, get_quick_download_keyboard

logger = logging.getLogger(__name__)
router = Router(name="library_router")

DB_PATH = "data/user_themes.db"


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                config_json TEXT NOT NULL,
                colors_json TEXT NOT NULL,
                image_blob BLOB,
                created_at REAL NOT NULL
            )
        """)
        conn.commit()


init_db()


def save_user_theme(user_id: int, name: str, session) -> int:
    config_dict = {
        "mode": session.config.mode,
        "accent_idx": session.config.accent_idx,
        "secondary_idx": session.config.secondary_idx,
        "bubble_style": session.config.bubble_style,
        "chat_tint": session.config.chat_tint,
        "wallpaper_mode": session.config.wallpaper_mode,
        "brightness_offset": session.config.brightness_offset,
        "custom_accent_hex": session.config.custom_accent_hex
    }
    colors_list = [c.hex for c in session.extracted_colors]
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO saved_themes (user_id, name, config_json, colors_json, image_blob, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, json.dumps(config_dict), json.dumps(colors_list), session.image_bytes, time.time()))
        conn.commit()
        return cursor.lastrowid


def get_user_themes(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, config_json, colors_json, created_at
            FROM saved_themes
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        return cursor.fetchall()


def get_theme_by_id(theme_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, name, config_json, colors_json, image_blob
            FROM saved_themes
            WHERE id = ?
        """, (theme_id,))
        return cursor.fetchone()


@router.message(Command("save"))
async def handle_save_command(message: Message):
    """Saves the active session theme to user's library."""
    user_id = message.from_user.id
    session = session_manager.get_session(user_id)
    if not session:
        await message.answer("⚠️ У вас нет активной темы для сохранения. Сначала отправьте фото или создайте тему!")
        return

    # Extract optional custom name from message
    parts = message.text.split(maxsplit=1)
    name = parts[1].strip() if len(parts) > 1 else f"Моя тема #{int(time.time()) % 1000}"
    
    theme_id = save_user_theme(user_id, name, session)
    await message.answer(f"💾 <b>Тема «{name}» успешно сохранена в вашей библиотеке!</b>\nПросмотреть: /mythemes", parse_mode="HTML")


@router.message(Command("mythemes"))
async def handle_mythemes_command(message: Message):
    """Displays list of saved themes."""
    user_id = message.from_user.id
    themes = get_user_themes(user_id)
    
    if not themes:
        await message.answer(
            "📂 <b>Ваша библиотека пуста.</b>\n"
            "Чтобы сохранить понравившуюся тему, отправьте команду /save после настройки темы!",
            parse_mode="HTML"
        )
        return

    buttons = []
    for tid, name, cfg_j, cols_j, created in themes:
        cfg = json.loads(cfg_j)
        mode_emoji = "🌙" if cfg.get("mode") == "dark" else ("🖤" if cfg.get("mode") == "amoled" else "☀️")
        btn_text = f"{mode_emoji} {name}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"load_saved_{tid}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("📂 <b>Ваши сохранённые темы:</b>\nНажмите на тему, чтобы загрузить её:", parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("load_saved_"))
async def cb_load_saved_theme(query: CallbackQuery):
    theme_id = int(query.data.replace("load_saved_", ""))
    row = get_theme_by_id(theme_id)
    if not row:
        await query.answer("⚠️ Тема не найдена.", show_alert=True)
        return

    _, uid, name, cfg_json, cols_json, img_blob = row
    cfg_dict = json.loads(cfg_json)
    
    session = session_manager.create_session(query.from_user.id, img_blob)
    session.config = ThemeConfig(**cfg_dict)
    
    palette = session.get_palette()
    wallpaper = session.get_wallpaper(width=800, height=820)
    preview_bytes = render_preview_to_bytes(palette, wallpaper, session.extracted_colors)
    photo_file = BufferedInputFile(preview_bytes, filename="saved_theme_preview.jpg")
    
    caption = f"📂 <b>Загружена сохранённая тема: {name}</b>"
    kb = get_theme_editor_keyboard(session.config, palette, session.extracted_colors)
    await query.message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
    await query.answer()
