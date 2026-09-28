"""
Main Telegram Bot Entrypoint.
Telegram Theme Studio Bot from Screenshots, Images, URLs, and Presets.
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import config
from handlers import (
    start_router,
    image_router,
    url_router,
    preset_router,
    library_router,
    callbacks_router,
    inline_router,
    AntiFloodMiddleware
)

logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ThemeBot")


async def set_bot_commands(bot: Bot):
    """Register bot commands in Telegram menu."""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота и получить инструкцию"),
        BotCommand(command="presets", description="📚 Каталог готовых дизайнерских тем"),
        BotCommand(command="random", description="🎲 Создать случайную тему"),
        BotCommand(command="save", description="💾 Сохранить текущую тему в библиотеку"),
        BotCommand(command="mythemes", description="📂 Мои сохранённые темы"),
        BotCommand(command="help", description="📖 Как установить тему на Android/ПК")
    ]
    try:
        await bot.set_my_commands(commands)
    except Exception as e:
        logger.warning("Could not set bot commands: %s", e)


async def main():
    """Main startup function."""
    if not config.bot_token:
        logger.error(
            "❌ ОШИБКА: BOT_TOKEN не указан!\n"
            "Пожалуйста, укажите токен вашего Telegram-бота в файле .env."
        )
        return

    logger.info("Starting Telegram Theme Studio Bot...")

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register anti-flood middleware
    anti_flood = AntiFloodMiddleware(limit_seconds=0.4)
    dp.message.middleware(anti_flood)
    dp.callback_query.middleware(anti_flood)

    # Register all feature routers
    dp.include_router(start_router)
    dp.include_router(preset_router)
    dp.include_router(library_router)
    dp.include_router(url_router)
    dp.include_router(image_router)
    dp.include_router(callbacks_router)
    dp.include_router(inline_router)

    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started successfully. Listening for updates...")

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "inline_query"])
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot execution terminated.")
