"""Middleware для восстановления FSM состояния из БД."""
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)


# Маппинг строковых состояний на State объекты
STATE_MAP = {}


def register_states():
    """Регистрация всех состояний для восстановления."""
    try:
        from states import (
            ProfileStates,
            EditProfileStates,
            EditDescriptionStates,
            SnowboardCalcStates,
            ResortStates,
            BuddySearchStates,
            BuddyFilterStates,
            EventStates,
            AddInstructorStates,
            ReviewStates,
            ChatStates,
            BroadcastStates,
        )
        
        state_groups = [
            ProfileStates,
            EditProfileStates,
            EditDescriptionStates,
            SnowboardCalcStates,
            ResortStates,
            BuddySearchStates,
            BuddyFilterStates,
            EventStates,
            AddInstructorStates,
            ReviewStates,
            ChatStates,
            BroadcastStates,
        ]
        
        for group in state_groups:
            for state_name in dir(group):
                state = getattr(group, state_name)
                if isinstance(state, State):
                    STATE_MAP[state.state] = state
        logger.info(f"Registered {len(STATE_MAP)} states for restoration")
    except Exception as e:
        logger.error(f"Failed to register states: {e}")


class StateRestoreMiddleware(BaseMiddleware):
    """Восстановление FSM состояния после перезапуска бота."""

    def __init__(self):
        register_states()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Всегда вызываем handler — middleware не должен блокировать
        if not isinstance(event, Message):
            return await handler(event, data)
        
        user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return await handler(event, data)
        
        state: FSMContext = data.get("state")
        db = data.get("db")
        
        # Если нет state или db — просто пропускаем восстановление, но НЕ блокируем
        if not state or not db:
            logger.debug(f"StateRestoreMiddleware: no state or db for user {user_id}")
            return await handler(event, data)
        
        # Проверяем, есть ли уже состояние в FSM
        try:
            current_state = await state.get_state()
            if current_state:
                return await handler(event, data)
            
            # Пробуем восстановить из БД
            saved_state = await db.get_user_state(user_id)
            if saved_state and saved_state in STATE_MAP:
                await state.set_state(STATE_MAP[saved_state])
                logger.info(f"Restored state {saved_state} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to restore state for user {user_id}: {e}")
        
        return await handler(event, data)
