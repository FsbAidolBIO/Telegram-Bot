"""
Handlers package for Telegram bot.
"""

from handlers.start import router as start_router
from handlers.image_handler import router as image_router
from handlers.callbacks import router as callbacks_router

__all__ = ["start_router", "image_router", "callbacks_router"]
