"""
Start, help, and general informational handlers.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import io
from PIL import Image, ImageDraw
import random
from handlers.session_manager import session_manager
from theme_engine.preview_generator import render_preview_to_bytes
from handlers.keyboards import get_theme_editor_keyboard

router = Router(name="start_router")


HELP_TEXT = """
🎨 <b>Как создавать и устанавливать темы Telegram:</b>

1️⃣ <b>Отправьте изображение боту:</b>
   • Отправьте любой скриншот, фото, обои или арт (как фото или файл).
   • Бот автоматически извлечёт цвета и сгенерирует превью.

2️⃣ <b>Настройте тему под себя:</b>
   • <b>🌓 Режим:</b> Переключайте между Тёмной, Светлой и AMOLED (True Black).
   • <b>🎨 Акцент:</b> Выбирайте основной цвет акцентов из найденных в скриншоте.
   • <b>🖼 Обои:</b> Размытие (Blur), Исходник, Градиент, Затемнение или Сплошной цвет.
   • <b>💬 Бабблы:</b> Стиль входящих и исходящих сообщений.
   • <b>➖ / ➕ Яркость:</b> Точная подгонка фона под ваши глаза.

3️⃣ <b>Установка темы:</b>
   • <b>🤖 Android:</b> Скачайте файл <code>.attheme</code> → нажмите на него прямо в чате → в открывшемся окне нажмите кнопку <b>«Применить тему»</b>.
   • <b>💻 Telegram Desktop (Windows / macOS / Linux):</b> Скачайте <code>.tdesktop-theme</code> → кликните по файлу в чате → нажмите <b>«Применить тему»</b>.
   • <b>📦 Полный архив:</b> Содержит файлы для всех платформ + обои высокого качества.

🚀 <i>Отправьте скриншот прямо сейчас, чтобы начать!</i>
"""


@router.message(CommandStart())
async def handle_start(message: Message):
    text = (
        "👋 <b>Добро пожаловать в Telegram Theme Bot!</b>\n\n"
        "Я умею превращать <b>любой скриншот, арт или фотографию</b> в готовую гармоничную тему для Telegram!\n\n"
        "✨ <b>Что я умею:</b>\n"
        "• 🤖 Темы для <b>Android</b> (формат <code>.attheme</code> со встроенными обоями)\n"
        "• 💻 Темы для <b>ПК / Desktop</b> (формат <code>.tdesktop-theme</code>)\n"
        "• 🌓 Режимы: <b>Dark</b>, <b>Light</b>, <b>AMOLED</b>\n"
        "• 🖼 Размытые, градиентные или оригинальные обои\n"
        "• 🎛 Гибкая настройка цветов, акцентов и бабблов\n\n"
        "📸 <b>Просто отправьте мне любое фото или скриншот</b>, и я мгновенно создам вашу тему!"
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
    
    # Generate procedural colorful artwork
    w, h = 600, 800
    img = Image.new("RGB", (w, h), (random.randint(10, 40), random.randint(15, 45), random.randint(25, 60)))
    draw = ImageDraw.Draw(img)
    
    # Random vibrant shapes
    for _ in range(6):
        c = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        box = [random.randint(0, w-100), random.randint(0, h-100), random.randint(100, w), random.randint(100, h)]
        draw.rounded_rectangle(box, radius=40, fill=c)
    
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    raw_bytes = bio.getvalue()
    
    # Create session
    session = session_manager.create_session(user_id, raw_bytes)
    palette = session.get_palette()
    wallpaper = session.get_wallpaper(width=800, height=820)
    
    preview_bytes = render_preview_to_bytes(palette, wallpaper, session.extracted_colors)
    kb = get_theme_editor_keyboard(session.config, palette, len(session.extracted_colors))
    
    caption = (
        "🎲 <b>Случайная тема создана!</b>\n\n"
        f"• <b>Режим:</b> {session.config.mode.upper()}\n"
        f"• <b>Основной акцент:</b> <code>{palette.hex_primary_accent.upper()}</code>\n"
        f"• <b>Фон:</b> <code>{palette.hex_bg.upper()}</code>\n\n"
        "👇 <i>Используйте кнопки ниже для настройки и скачивания темы:</i>"
    )
    
    from aiogram.types import BufferedInputFile
    photo_file = BufferedInputFile(preview_bytes, filename="preview.jpg")
    
    if isinstance(event, CallbackQuery):
        await event.message.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await msg.answer_photo(photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
