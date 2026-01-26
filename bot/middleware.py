"""Middleware for database session injection."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from db.database import async_session_maker


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject database session into handlers."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Inject database session into handler data."""
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)
