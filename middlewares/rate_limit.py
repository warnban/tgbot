"""Middleware для rate limiting."""
import logging
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """Ограничение частоты запросов."""

    def __init__(self, rate_limit: int = 30, period: int = 60):
        """
        Args:
            rate_limit: Максимум сообщений за период
            period: Период в секундах
        """
        self.rate_limit = rate_limit
        self.period = period
        self.user_requests: Dict[int, list] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        
        user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return await handler(event, data)
        
        current_time = time.time()
        
        # Очищаем старые записи
        self.user_requests[user_id] = [
            t for t in self.user_requests[user_id]
            if current_time - t < self.period
        ]
        
        # Проверяем лимит
        if len(self.user_requests[user_id]) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            await event.answer(
                "⚠️ Слишком много запросов. Подожди немного.",
            )
            return None
        
        # Добавляем текущий запрос
        self.user_requests[user_id].append(current_time)
        
        return await handler(event, data)
