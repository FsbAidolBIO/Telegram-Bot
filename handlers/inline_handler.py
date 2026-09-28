"""
Inline Query Handler: enables @ThemeBot search in any chat.
"""

from aiogram import Router, F
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from theme_engine.presets import PRESETS_LIBRARY
from theme_engine.color_extractor import is_valid_hex, hex_to_rgb, get_color_emoji
import hashlib

router = Router(name="inline_router")


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery):
    query = inline_query.query.strip().lower()
    results = []

    # 1. If user typed a HEX color code (e.g. #3A86FF)
    if is_valid_hex(query):
        clean_hex = "#" + query.lstrip("#").upper()
        rgb = hex_to_rgb(clean_hex)
        emoji = get_color_emoji(rgb)
        
        content = (
            f"🎨 <b>Тема оформления Telegram</b>\n\n"
            f"• <b>Акцент:</b> {emoji} <code>{clean_hex}</code>\n"
            f"• <b>Режим:</b> Dark & AMOLED\n\n"
            "✨ <i>Создайте полноценную тему с обоями в боте!</i>"
        )
        res_id = hashlib.md5(clean_hex.encode()).hexdigest()
        results.append(
            InlineQueryResultArticle(
                id=res_id,
                title=f"{emoji} Тема с цветом {clean_hex}",
                description=f"Нажмите, чтобы отправить палитру {clean_hex}",
                input_message_content=InputTextMessageContent(
                    message_text=content,
                    parse_mode="HTML"
                )
            )
        )

    # 2. Offer curated presets
    for key, preset in PRESETS_LIBRARY.items():
        if not query or query in preset.title.lower() or query in preset.description.lower() or query == "random":
            content = (
                f"{preset.emoji} <b>Тема: {preset.title}</b>\n"
                f"<i>{preset.description}</i>\n\n"
                f"• <b>Режим:</b> {preset.mode.upper()}\n"
                f"• <b>Акцент:</b> <code>{preset.accent_hex}</code>\n"
                f"• <b>Второй цвет:</b> <code>{preset.secondary_hex}</code>\n"
                f"• <b>Фон:</b> <code>{preset.bg_hex}</code>"
            )
            res_id = hashlib.md5(f"preset_{key}".encode()).hexdigest()
            results.append(
                InlineQueryResultArticle(
                    id=res_id,
                    title=f"{preset.emoji} {preset.title}",
                    description=preset.description,
                    input_message_content=InputTextMessageContent(
                        message_text=content,
                        parse_mode="HTML"
                    )
                )
            )

    await inline_query.answer(results[:15], cache_time=300, is_personal=False)
