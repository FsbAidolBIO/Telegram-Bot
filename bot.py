"""
Main Telegram Bot Entrypoint.
Telegram Theme Generator Bot from Screenshots and Images.
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import config
from handlers import start_router, image_router, callbacks_router

logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ThemeBot")


async def set_bot_commands(bot: Bot):
    """Register bot commands in Telegram interface."""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота и получить инструкцию"),
        BotCommand(command="random", description="🎲 Создать случайную тему"),
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
            "Пожалуйста, укажите токен вашего Telegram-бота в файле .env или переменной окружения BOT_TOKEN.\n"
            "Пример:\n"
            "BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz"
        )
        print("\n" + "=" * 60)
        print("Внимание: Для запуска укажите BOT_TOKEN в .env")
        print("=" * 60 + "\n")
        return

    logger.info("Starting Telegram Theme Generator Bot...")

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register routers
    dp.include_router(start_router)
    dp.include_router(image_router)
    dp.include_router(callbacks_router)

    # Set Telegram bot menu commands
    await set_bot_commands(bot)

    # Delete existing webhook to enable long polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started successfully. Waiting for messages...")

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot execution terminated by user.")
