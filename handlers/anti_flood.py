"""
Anti-flood and rate-limiting middleware for Telegram Bot.
Protects the bot from spam and excessive photo processing.
"""

import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class AntiFloodMiddleware(BaseMiddleware):
    """Simple and efficient in-memory rate limiter per user."""
    def __init__(self, limit_seconds: float = 0.5):
        self.limit_seconds = limit_seconds
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            now = time.time()
            last_time = self.user_timestamps.get(user_id, 0.0)
            
            # If triggered too fast
            if now - last_time < self.limit_seconds:
                if isinstance(event, CallbackQuery):
                    await event.answer("⏳ Не так быстро...", show_alert=False)
                return None
            
            self.user_timestamps[user_id] = now
            
            # Periodic cleanup
            if len(self.user_timestamps) > 5000:
                cutoff = now - 60.0
                self.user_timestamps = {uid: t for uid, t in self.user_timestamps.items() if t > cutoff}

        return await handler(event, data)
