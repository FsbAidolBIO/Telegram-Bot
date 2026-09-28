"""
Start, help, and general informational handlers.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import io
from PIL import Image, ImageDraw
import random
from handlers.session_manager import session_manager
from theme_engine.preview_generator import render_preview_to_bytes
from handlers.keyboards import get_theme_editor_keyboard

router = Router(name="start_router")


HELP_TEXT = """
🎨 <b>Как создавать и настраивать темы Telegram:</b>

1️⃣ <b>Отправьте скриншот или фото боту:</b>
   • Отправьте любой скриншот (игры, аниме, фото, дизайн).
   • Бот извлечёт палитру цветов и создаст живое превью темы.

2️⃣ <b>Интерактивный выбор цветов и атмосферы:</b>
   • <b>Кнопки цветов:</b> Нажимайте прямо на цветные кнопки (например <code>🔵 #00B4D8</code>), чтобы мгновенно сменить основной акцент!
   • <b>🌌 Атмосфера:</b> Окрашивает фон списков, диалогов и поле ввода в атмосферный оттенок арта.
   • <b>💬 Бабблы:</b>
     - <i>Неон / Акцент</i>: яркий исходящий + атмосферный входящий
     - <i>Двойной цвет</i>: 2 гармоничных акцента из фото
     - <i>Мягкий тинт</i>: эстетичные пастельные тона
     - <i>Стекло</i>: стильные карточки
   • <b>🌓 Режим:</b> Dark, Light (не слепит глаза!), AMOLED.
   • <b>🖼 Обои:</b> Размытие, Вписать (без обрезки), Заполнить, Градиент.

3️⃣ <b>Установка темы:</b>
   • <b>Android:</b> Скачайте <code>.attheme</code> → нажмите на файл в чате → <b>«Применить тему»</b>.
   • <b>ПК (Windows/Mac/Linux):</b> Кликните на <code>.tdesktop-theme</code> → <b>«Применить тему»</b>.

🚀 <i>Отправьте изображение или нажмите /random для проверки!</i>
"""


@router.message(CommandStart())
async def handle_start(message: Message):
    text = (
        "👋 <b>Добро пожаловать в Telegram Theme Bot!</b>\n\n"
        "Я создаю гармоничные дизайнерские темы для Telegram из <b>любых скриншотов и артов</b>!\n\n"
        "✨ <b>Что доступно:</b>\n"
        "• 🎨 <b>Интерактивная сетка цветов</b> (выбор акцентов в 1 клик)\n"
        "• 🌌 <b>Цветовая атмосфера чата</b> (никаких скучных серых и белых фонов)\n"
        "• 📱 Темы для <b>Android</b> (<code>.attheme</code> со встроенными обоями)\n"
        "• 💻 Темы для <b>ПК</b> (<code>.tdesktop-theme</code>)\n"
        "• 🌓 Режимы: <b>Dark</b>, <b>Light</b>, <b>AMOLED</b>\n\n"
        "📸 <b>Отправьте мне скриншот или фото прямо сейчас!</b>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Сгенерировать случайную тему", callback_data="demo_random")],
        [InlineKeyboardButton(text="📖 Подробная инструкция", callback_data="show_help")]
    ])
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.message(Command("help"))
async def handle_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.callback_query(F.data == "show_help")
async def callback_help(query: CallbackQuery):
    await query.message.answer(HELP_TEXT, parse_mode="HTML")
    await query.answer()


@router.message(Command("random"))
@router.callback_query(F.data == "demo_random")
async def handle_random_theme(event):
    """Generates an artistic procedural color image and turns it into a theme demo."""
    msg = event.message if isinstance(event, CallbackQuery) else event
    user_id = event.from_user.id
    
    w, h = 600, 800
    img = Image.new("RGB", (w, h), (random.randint(15, 35), random.randint(20, 45), random.randint(30, 65)))
    draw = ImageDraw.Draw(img)
    
    for _ in range(6):
        c = (random.randint(60, 255), random.randint(60, 255), random.randint(60, 255))
        box = [random.randint(0, w-120), random.randint(0, h-120), random.randint(120, w), random.randint(120, h)]
        draw.rounded_rectangle(box, radius=40, fill=c)
    
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    raw_bytes = bio.getvalue()
    
    session = session_manager.create_session(user_id, raw_bytes)
    palette = session.get_palette()
    wallpaper = session.get_wallpaper(width=800, height=820)
    
    preview_bytes = render_preview_to_bytes(palette, wallpaper, session.extracted_colors)
    kb = get_theme_editor_keyboard(session.config, palette, session.extracted_colors)
    
    caption = (
        "🎲 <b>Случайная тема создана!</b>\n\n"
        f"• <b>Режим:</b> {session.config.mode.upper()}\n"
        f"• <b>Основной акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
        f"• <b>Второй цвет:</b> <code>{palette.hex_secondary_accent.upper()}</code>\n"
        f"• <b>Фон чата:</b> <code>{palette.hex_bg.upper()}</code>\n\n"
        "👇 <i>Выберите цвета или скачайте тему на кнопках ниже:</i>"
    )
    
    photo_file = BufferedInputFile(preview_bytes, filename="preview.jpg")
    
    if isinstance(event, CallbackQuery):
        await event.message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await msg.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
