"""Общие хелперы для всех хендлеров."""
import json
import logging
from typing import List, Optional

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaPhoto

from db import Database
from keyboards import MAIN_MENU
from services.resorts import haversine_km

logger = logging.getLogger(__name__)


def format_profile(
    profile: dict,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
) -> str:
    """Форматирует профиль для отображения."""
    gender_icon = "👨" if profile.get("gender") == "м" else "👩" if profile.get("gender") == "ж" else ""
    
    lines = [
        f"<b>{gender_icon} {profile.get('first_name', 'Без имени')}</b>, {profile['age']}",
        f"{profile['ride_type']} • {profile['skill_level']}",
        f"📍 {profile['city']}",
    ]
    
    # Расстояние до человека
    if (
        user_lat is not None
        and user_lon is not None
        and profile.get("location_lat") is not None
        and profile.get("location_lon") is not None
    ):
        dist = haversine_km(user_lat, user_lon, profile["location_lat"], profile["location_lon"])
        dist_str = f"{dist:.0f} км" if dist >= 1 else f"{dist * 1000:.0f} м"
        lines.append(f"📏 {dist_str} от тебя")
    
    if profile.get("about"):
        lines.append(f"\n💬 {profile['about']}")
    
    return "\n".join(lines)


def format_event(event: dict) -> str:
    """Форматирует событие для отображения."""
    level_icons = {
        "Новичок": "🟢",
        "Средний": "🔵",
        "Продвинутый": "🔴",
        "Любой": "⚪",
    }
    level_icon = level_icons.get(event["skill_level"], "⚪")
    
    lines = [
        f"📅 <b>Событие</b>",
        f"🏔️ {event['resort_name']}",
        f"📆 {event['event_date']}",
        f"{level_icon} Уровень: {event['skill_level']}",
        f"👤 Организатор: {event['creator_name']}",
    ]
    
    if event.get("description"):
        lines.append(f"\n💬 {event['description']}")
    
    return "\n".join(lines)


def get_photos(profile: dict) -> List[str]:
    """Получить список фото из профиля."""
    photos_raw = profile.get("photos")
    if not photos_raw:
        return []
    try:
        return json.loads(photos_raw)
    except (json.JSONDecodeError, TypeError):
        return []


async def ensure_user(db: Database, msg_or_cb: Message | CallbackQuery) -> int:
    """Создаёт или обновляет пользователя, возвращает user_id."""
    user = msg_or_cb.from_user
    return await db.upsert_user(
        telegram_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
    )


async def set_state(db: Database, fsm: FSMContext, telegram_id: int, state) -> None:
    """Устанавливает состояние FSM и сохраняет в БД."""
    if state:
        await fsm.set_state(state)
        state_value = state.state if hasattr(state, "state") else str(state)
    else:
        await fsm.clear()
        state_value = None
    await db.update_user_state(telegram_id, state_value)


async def send_main_menu(message: Message, text: str = "Выбери действие:") -> None:
    """Отправляет главное меню."""
    await message.answer(text, reply_markup=MAIN_MENU)


async def send_profile_with_photos(
    message: Message,
    profile: dict,
    text: str,
    reply_markup=None,
) -> None:
    """Отправить профиль с фотографиями."""
    photos = get_photos(profile)
    
    if not photos:
        await message.answer(text, reply_markup=reply_markup)
        return
    
    if len(photos) == 1:
        await message.answer_photo(photos[0], caption=text, reply_markup=reply_markup)
    else:
        # Несколько фото — отправляем альбомом, потом текст
        media = [InputMediaPhoto(media=photo_id) for photo_id in photos[:10]]
        await message.answer_media_group(media)
        await message.answer(text, reply_markup=reply_markup)


def truncate(text: str, max_length: int = 500) -> str:
    """Обрезает текст до максимальной длины."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
