"""
Handlers package for Telegram bot.
"""

from handlers.start import router as start_router
from handlers.image_handler import router as image_router
from handlers.url_handler import router as url_router
from handlers.preset_handler import router as preset_router
from handlers.library_handler import router as library_router
from handlers.callbacks import router as callbacks_router
from handlers.inline_handler import router as inline_router
from handlers.anti_flood import AntiFloodMiddleware

__all__ = [
    "start_router",
    "image_router",
    "url_router",
    "preset_router",
    "library_router",
    "callbacks_router",
    "inline_router",
    "AntiFloodMiddleware"
]
