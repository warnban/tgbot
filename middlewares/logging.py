"""Middleware для логирования."""
import logging
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Логирование всех входящих апдейтов."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        start_time = time.time()
        
        # Извлекаем информацию о пользователе
        user_id = None
        event_type = "unknown"
        
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id if event.message.from_user else None
                event_type = "message"
                if event.message.text:
                    event_type = f"message:{event.message.text[:30]}"
            elif event.callback_query:
                user_id = event.callback_query.from_user.id if event.callback_query.from_user else None
                event_type = f"callback:{event.callback_query.data}"
        
        try:
            result = await handler(event, data)
            duration = (time.time() - start_time) * 1000
            logger.debug(f"[{user_id}] {event_type} - {duration:.1f}ms")
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"[{user_id}] {event_type} - ERROR: {e} - {duration:.1f}ms")
            raise
