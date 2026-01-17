"""Поиск компании с фильтрами и умным матчингом."""
import logging
from typing import List, Tuple

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import (
    MAIN_MENU,
    back_to_menu_kb,
    buddy_actions_kb,
    buddy_filter_kb,
    who_liked_kb,
)
from states import BuddySearchStates, BuddyFilterStates

from .common import (
    ensure_user,
    format_event,
    format_profile,
    send_profile_with_photos,
    set_state,
)

logger = logging.getLogger(__name__)
router = Router()


def calculate_match_score(
    user_profile: dict,
    candidate_profile: dict,
    user_lat: float = None,
    user_lon: float = None,
) -> int:
    """Расчёт релевантности кандидата (0-100)."""
    from services.resorts import haversine_km
    
    score = 0
    
    # Тот же тип катания (+20)
    if user_profile.get("ride_type") == candidate_profile.get("ride_type"):
        score += 20
    
    # Тот же уровень (+15), соседний уровень (+5)
    levels = ["Новичок", "Средний", "Продвинутый"]
    user_level = user_profile.get("skill_level", "")
    cand_level = candidate_profile.get("skill_level", "")
    if user_level in levels and cand_level in levels:
        level_diff = abs(levels.index(user_level) - levels.index(cand_level))
        if level_diff == 0:
            score += 15
        elif level_diff == 1:
            score += 5
    
    # Тот же город (+20)
    if user_profile.get("city") == candidate_profile.get("city"):
        score += 20
    
    # Близкий возраст (+10 если разница <5 лет)
    user_age = user_profile.get("age", 0)
    cand_age = candidate_profile.get("age", 0)
    if user_age and cand_age:
        age_diff = abs(user_age - cand_age)
        if age_diff <= 5:
            score += 10
        elif age_diff <= 10:
            score += 5
    
    # Близкая геолокация (+20 если <50 км)
    if (
        user_lat and user_lon
        and candidate_profile.get("location_lat")
        and candidate_profile.get("location_lon")
    ):
        dist = haversine_km(
            user_lat, user_lon,
            candidate_profile["location_lat"],
            candidate_profile["location_lon"],
        )
        if dist < 10:
            score += 20
        elif dist < 50:
            score += 10
        elif dist < 100:
            score += 5
    
    # Есть описание (+5)
    if candidate_profile.get("about"):
        score += 5
    
    # Есть фото (+10)
    if candidate_profile.get("photos"):
        score += 10
    
    return score


@router.message(F.text == "🔍 Искать компанию")
async def buddy_menu(message: Message, state: FSMContext, db: Database) -> None:
    """Меню поиска компании."""
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    if not profile:
        await message.answer(
            "❌ Сначала создай профиль в разделе «👤 Профиль»",
            reply_markup=MAIN_MENU,
        )
        return
    
    # Сохраняем данные профиля для матчинга
    profile_dict = dict(profile)
    await state.update_data(
        user_lat=profile_dict.get("location_lat"),
        user_lon=profile_dict.get("location_lon"),
        user_profile=profile_dict,
        filters={},  # Пустые фильтры по умолчанию
    )
    
    await message.answer(
        "🔍 <b>Поиск компании</b>\n\n"
        "Можешь настроить фильтры или сразу начать просмотр:",
        reply_markup=buddy_filter_kb(),
    )


@router.callback_query(F.data == "buddy:start")
async def buddy_start_search(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Начать просмотр анкет."""
    await set_state(db, state, query.from_user.id, BuddySearchStates.browsing)
    await start_buddy_browsing(query.message, state, db)
    await query.answer()


@router.callback_query(F.data == "buddy:filter_ride")
async def buddy_filter_ride(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Фильтр по типу катания."""
    from keyboards import ride_type_filter_kb
    await set_state(db, state, query.from_user.id, BuddyFilterStates.waiting_ride)
    await query.message.answer("🎿 Выбери тип катания:", reply_markup=ride_type_filter_kb())
    await query.answer()


@router.callback_query(BuddyFilterStates.waiting_ride, F.data.startswith("fride:"))
async def buddy_filter_ride_got(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Применить фильтр по типу катания."""
    ride_type = query.data.split(":", 1)[1]
    data = await state.get_data()
    filters = data.get("filters", {})
    if ride_type == "any":
        filters.pop("ride_type", None)
    else:
        filters["ride_type"] = ride_type
    await state.update_data(filters=filters)
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer(
        f"✅ Фильтр применён: <b>{ride_type if ride_type != 'any' else 'Любой'}</b>",
        reply_markup=buddy_filter_kb(),
    )
    await query.answer()


@router.callback_query(F.data == "buddy:filter_level")
async def buddy_filter_level(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Фильтр по уровню."""
    from keyboards import level_filter_kb
    await set_state(db, state, query.from_user.id, BuddyFilterStates.waiting_level)
    await query.message.answer("📊 Выбери уровень:", reply_markup=level_filter_kb())
    await query.answer()


@router.callback_query(BuddyFilterStates.waiting_level, F.data.startswith("flevel:"))
async def buddy_filter_level_got(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Применить фильтр по уровню."""
    level = query.data.split(":")[1]
    data = await state.get_data()
    filters = data.get("filters", {})
    if level == "any":
        filters.pop("skill_level", None)
    else:
        filters["skill_level"] = level
    await state.update_data(filters=filters)
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer(
        f"✅ Фильтр применён: <b>{level if level != 'any' else 'Любой'}</b>",
        reply_markup=buddy_filter_kb(),
    )
    await query.answer()


@router.callback_query(F.data == "buddy:filter_clear")
async def buddy_filter_clear(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Сбросить фильтры."""
    await state.update_data(filters={})
    await query.message.answer("🗑️ Фильтры сброшены", reply_markup=buddy_filter_kb())
    await query.answer()


async def start_buddy_browsing(message: Message, state: FSMContext, db: Database) -> None:
    """Начать просмотр анкет с учётом фильтров и умного матчинга."""
    user_id = await ensure_user(db, message)
    if not user_id:
        await message.answer("❌ Ошибка. Попробуй /start", reply_markup=MAIN_MENU)
        return
    
    data = await state.get_data()
    filters = data.get("filters", {})
    user_profile = data.get("user_profile", {})
    user_lat = data.get("user_lat")
    user_lon = data.get("user_lon")
    
    # Получаем профили с фильтрами
    profiles = await db.get_filtered_profiles(
        current_user_id=user_id,
        ride_type=filters.get("ride_type"),
        skill_level=filters.get("skill_level"),
        limit=100,
    )
    
    # Получаем события
    events = await db.get_active_events()
    
    # Убираем заблокированных и уже лайкнутых
    already_liked = await db.get_already_liked(user_id)
    blocked_users = await db.get_blocked_users(user_id)
    
    # Собираем кандидатов с рейтингом
    candidates: List[Tuple[str, int, int]] = []  # (type, id, score)
    
    for row in profiles:
        if row["user_id"] in already_liked or row["user_id"] in blocked_users:
            continue
        profile_dict = dict(row)
        score = calculate_match_score(user_profile, profile_dict, user_lat, user_lon)
        candidates.append(("profile", row["user_id"], score))
    
    for row in events:
        if row["creator_id"] != user_id and row["creator_id"] not in blocked_users:
            candidates.append(("event", row["id"], 50))  # Средний приоритет для событий
    
    # Сортируем по score (убывание)
    candidates.sort(key=lambda x: x[2], reverse=True)
    
    # Убираем score для хранения
    candidates_list = [(c[0], c[1]) for c in candidates]
    
    await state.update_data(candidates=candidates_list, candidate_index=0)
    
    if not candidates_list:
        await set_state(db, state, message.from_user.id, None)
        filter_hint = ""
        if filters:
            filter_hint = "\n\n💡 Попробуй сбросить фильтры."
        await message.answer(
            f"😔 Пока нет райдеров по твоим критериям.{filter_hint}\n\n"
            "Ты уже в поиске — другие увидят тебя!",
            reply_markup=back_to_menu_kb(),
        )
        return
    
    await message.answer(f"🔍 Найдено: {len(candidates_list)}")
    await show_next_candidate(message, state, db)


async def show_next_candidate(message: Message, state: FSMContext, db: Database) -> None:
    """Показать следующего кандидата."""
    data = await state.get_data()
    index = data.get("candidate_index", 0)
    candidates = data.get("candidates", [])
    
    if index >= len(candidates):
        await set_state(db, state, message.from_user.id, None)
        await message.answer("🏁 Анкеты закончились!", reply_markup=back_to_menu_kb())
        return
    
    candidate_type, candidate_id = candidates[index]
    await state.update_data(
        candidate_index=index + 1,
        current_candidate_type=candidate_type,
        current_candidate_id=candidate_id,
    )
    
    if candidate_type == "profile":
        await show_profile_candidate(message, state, db, candidate_id)
    else:
        await show_event_candidate(message, state, db, candidate_id)


async def show_profile_candidate(message: Message, state: FSMContext, db: Database, user_id: int) -> None:
    """Показать профиль кандидата."""
    profile = await db.get_profile(user_id)
    if not profile:
        await show_next_candidate(message, state, db)
        return
    
    profile_dict = dict(profile)
    data = await state.get_data()
    user_lat = data.get("user_lat")
    user_lon = data.get("user_lon")
    text = format_profile(profile_dict, user_lat, user_lon)
    
    await send_profile_with_photos(message, profile_dict, text, buddy_actions_kb(user_id=user_id))


async def show_event_candidate(message: Message, state: FSMContext, db: Database, event_id: int) -> None:
    """Показать событие."""
    event = await db.get_event(event_id)
    if not event:
        await show_next_candidate(message, state, db)
        return
    
    event_dict = dict(event)
    text = format_event(event_dict)
    
    if event_dict.get("photo_file_id"):
        await message.answer_photo(
            event_dict["photo_file_id"],
            caption=text,
            reply_markup=buddy_actions_kb(is_event=True, event_id=event_id),
        )
    else:
        await message.answer(text, reply_markup=buddy_actions_kb(is_event=True, event_id=event_id))


@router.callback_query(BuddySearchStates.browsing, F.data.startswith("buddy:like:"))
async def buddy_like(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Лайк профиля."""
    target_user_id = int(query.data.split(":")[2])
    user_id = await ensure_user(db, query)
    
    if not user_id:
        await query.answer("Ошибка", show_alert=True)
        return
    
    # Проверяем, не лайкали ли уже (race condition fix)
    if await db.has_like(user_id, target_user_id):
        await show_next_candidate(query.message, state, db)
        await query.answer("Уже лайкнуто")
        return
    
    await db.add_like(user_id, target_user_id)
    
    # Уведомляем о лайке
    await notify_like(db, user_id, target_user_id, query.bot)
    
    # Проверяем взаимность
    if await db.has_like(target_user_id, user_id):
        # Проверяем, нет ли уже мэтча (race condition fix)
        if not await db.has_match(user_id, target_user_id):
            await db.add_match(user_id, target_user_id)
            await notify_match(db, user_id, target_user_id, query.from_user.id, query.bot)
            await query.message.answer("🎿 <b>Взаимный интерес!</b>")
    
    await show_next_candidate(query.message, state, db)
    await query.answer("👍")


@router.callback_query(BuddySearchStates.browsing, F.data.startswith("event:join:"))
async def event_join(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Присоединиться к событию."""
    event_id = int(query.data.split(":")[2])
    event = await db.get_event(event_id)
    
    if not event:
        await query.answer("Событие не найдено", show_alert=True)
        await show_next_candidate(query.message, state, db)
        return
    
    await query.message.answer(
        f"🎿 <b>Присоединяйся!</b>\n\n"
        f"🏔️ {event['resort_name']} — {event['event_date']}\n\n"
        f"👥 Вступай в группу: {event['telegram_group_link']}",
    )
    
    await show_next_candidate(query.message, state, db)
    await query.answer("👍")


@router.callback_query(BuddySearchStates.browsing, F.data == "buddy:skip")
async def buddy_skip(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Пропустить анкету."""
    await show_next_candidate(query.message, state, db)
    await query.answer("👎")


@router.callback_query(BuddySearchStates.browsing, F.data.startswith("buddy:block:"))
async def buddy_block(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Заблокировать пользователя."""
    target_user_id = int(query.data.split(":")[2])
    user_id = await ensure_user(db, query)
    
    if user_id:
        await db.block_user(user_id, target_user_id)
        logger.info(f"User {query.from_user.id} blocked user_id {target_user_id}")
    
    await show_next_candidate(query.message, state, db)
    await query.answer("🚫 Заблокировано")


# ═══════════════════════════════════════════════════════════════════
# КТО МЕНЯ ЛАЙКНУЛ / ОТМЕНА ЛАЙКА
# ═══════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "buddy:who_liked")
async def who_liked_me(query: CallbackQuery, db: Database) -> None:
    """Показать кто лайкнул."""
    user_id = await ensure_user(db, query)
    if not user_id:
        await query.answer("Ошибка", show_alert=True)
        return
    
    likers = await db.get_who_liked_me(user_id)
    likers_list = list(likers)
    
    if not likers_list:
        await query.message.answer(
            "😔 Пока никто не лайкнул твой профиль.\n\n"
            "Продолжай активно искать компанию!",
            reply_markup=back_to_menu_kb(),
        )
    else:
        await query.message.answer(
            f"💖 <b>Тебя лайкнули</b> ({len(likers_list)})\n\n"
            "Лайкни в ответ, чтобы получить контакт!",
            reply_markup=who_liked_kb(likers_list),
        )
    await query.answer()


@router.callback_query(F.data.startswith("viewliker:"))
async def view_liker(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Посмотреть профиль лайкнувшего."""
    liker_user_id = int(query.data.split(":")[1])
    profile = await db.get_profile(liker_user_id)
    
    if not profile:
        await query.answer("Профиль не найден", show_alert=True)
        return
    
    profile_dict = dict(profile)
    text = format_profile(profile_dict)
    
    from keyboards import liker_actions_kb
    await send_profile_with_photos(query.message, profile_dict, text, liker_actions_kb(liker_user_id))
    await query.answer()


@router.callback_query(F.data.startswith("likeback:"))
async def like_back(query: CallbackQuery, db: Database) -> None:
    """Лайкнуть в ответ."""
    target_user_id = int(query.data.split(":")[1])
    user_id = await ensure_user(db, query)
    
    if not user_id:
        await query.answer("Ошибка", show_alert=True)
        return
    
    await db.add_like(user_id, target_user_id)
    
    # Это точно мэтч, т.к. тот уже лайкнул нас
    if not await db.has_match(user_id, target_user_id):
        await db.add_match(user_id, target_user_id)
        await notify_match(db, user_id, target_user_id, query.from_user.id, query.bot)
    
    await query.message.answer("🎿 <b>Взаимный интерес!</b>", reply_markup=back_to_menu_kb())
    await query.answer("👍")


async def notify_like(db: Database, from_user_id: int, to_user_id: int, bot: Bot) -> None:
    """Уведомить пользователя что его лайкнули."""
    from_user = await db.get_user_by_id(from_user_id)
    to_user = await db.get_user_by_id(to_user_id)
    if not from_user or not to_user:
        return
    
    from_profile = await db.get_profile(from_user_id)
    if not from_profile:
        return
    
    name = from_user["first_name"] if from_user["first_name"] else "Кто-то"
    try:
        await bot.send_message(
            to_user["telegram_id"],
            f"🏂 <b>{name}</b> предлагает катнуть!\n\n"
            "Загляни в «🔍 Искать компанию» → «Кто меня лайкнул».",
        )
    except Exception:
        pass


async def notify_match(db: Database, user_id: int, candidate_id: int, telegram_id: int, bot: Bot) -> None:
    """Уведомить обоих о взаимном интересе."""
    target_user = await db.get_user_by_id(candidate_id)
    current_user = await db.get_user_by_id(user_id)
    if not target_user or not current_user:
        return
    
    current_link = f"@{current_user['username']}" if current_user["username"] else f"tg://user?id={current_user['telegram_id']}"
    candidate_link = f"@{target_user['username']}" if target_user["username"] else f"tg://user?id={target_user['telegram_id']}"
    
    await bot.send_message(telegram_id, f"💬 Напиши: {candidate_link}")
    
    if target_user["telegram_id"] != telegram_id:
        try:
            await bot.send_message(
                target_user["telegram_id"],
                f"🎿 <b>Пойдём катать?</b>\n\n💬 Напиши: {current_link}",
            )
        except Exception:
            pass
