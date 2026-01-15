import asyncio
import json
from typing import List, Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaPhoto

from config import Config, load_config
from db import Database
from keyboards import (
    BACK_KB,
    LOCATION_KB,
    MAIN_MENU,
    back_to_menu_kb,
    buddy_actions_kb,
    calc_type_kb,
    cities_list_kb,
    city_resorts_kb,
    contacts_kb,
    donate_kb,
    event_confirm_kb,
    event_level_kb,
    event_photo_kb,
    event_resorts_kb,
    event_view_kb,
    events_calendar_kb,
    events_list_kb,
    gender_kb,
    instructor_cities_kb,
    level_kb,
    my_event_actions_kb,
    my_events_kb,
    profile_actions_kb,
    profile_gender_kb,
    profile_level_kb,
    profile_more_photos_kb,
    profile_photo_kb,
    resort_back_kb,
    resorts_list_kb,
    ride_type_kb,
    ski_style_kb,
    snowboard_style_kb,
    sos_back_kb,
)
from services.equipment import calculate_ski_length, calculate_snowboard_length
from services.resorts import haversine_km, sort_by_distance
from services.weather import get_weather, format_weather
from states import (
    AddInstructorStates,
    BuddySearchStates,
    EditDescriptionStates,
    EventStates,
    ProfileStates,
    ResortStates,
    SkiCalcStates,
    SnowboardCalcStates,
)

router = Router()
config = load_config()


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def format_profile(profile: dict, user_lat: Optional[float] = None, user_lon: Optional[float] = None) -> str:
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
    user = msg_or_cb.from_user
    return await db.upsert_user(
        telegram_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
    )


async def set_state(db: Database, fsm: FSMContext, telegram_id: int, state) -> None:
    if state:
        await fsm.set_state(state)
        state_value = state.state if hasattr(state, "state") else str(state)
    else:
        await fsm.clear()
        state_value = None
    await db.update_user_state(telegram_id, state_value)


async def send_main_menu(message: Message, text: str = "Выбери действие:") -> None:
    await message.answer(text, reply_markup=MAIN_MENU)


async def send_profile_with_photos(message: Message, profile: dict, text: str, reply_markup=None) -> None:
    """Отправить профиль с фотографиями."""
    photos = get_photos(profile)
    
    if not photos:
        await message.answer(text, reply_markup=reply_markup)
        return
    
    if len(photos) == 1:
        await message.answer_photo(photos[0], caption=text, reply_markup=reply_markup)
    else:
        # Несколько фото — отправляем альбомом, потом текст
        media = [InputMediaPhoto(media=photo_id) for photo_id in photos[:10]]  # max 10
        await message.answer_media_group(media)
        await message.answer(text, reply_markup=reply_markup)


# ═══════════════════════════════════════════════════════════════════
# /start И НАВИГАЦИЯ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    await set_state(db, state, message.from_user.id, None)
    
    if profile:
        await message.answer(
            "Привет! Я помогу подобрать снаряжение, найти склоны и компанию.",
            reply_markup=MAIN_MENU,
        )
        return
    
    # Нет профиля — начинаем регистрацию
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_photos)
    await state.update_data(photos=[])
    await message.answer(
        "Привет! Давай создадим профиль.\n\n"
        "📸 Пришли фото для профиля (можно несколько) или пропусти.",
        reply_markup=BACK_KB,
    )
    await message.answer("👇", reply_markup=profile_photo_kb())


@router.message(F.text.in_(["◀️ Назад", "🏠 Меню"]))
async def cmd_back(message: Message, state: FSMContext, db: Database) -> None:
    await set_state(db, state, message.from_user.id, None)
    await send_main_menu(message, "Главное меню")


@router.callback_query(F.data == "nav:menu")
async def cb_nav_menu(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer("Главное меню", reply_markup=MAIN_MENU)
    await query.answer()


# ═══════════════════════════════════════════════════════════════════
# СТАТИСТИКА (АДМИН)
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "/stats")
async def cmd_stats(message: Message, db: Database) -> None:
    if message.from_user.id not in config.admin_ids:
        return
    
    stats = await db.get_stats()
    await message.answer(
        "📊 <b>Статистика Snow Crew</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"👤 Профилей: <b>{stats['profiles']}</b>\n"
        f"❤️ Лайков: <b>{stats['likes']}</b>\n"
        f"🤝 Мэтчей: <b>{stats['matches']}</b>\n"
        f"📅 Событий: <b>{stats['events']}</b>",
        reply_markup=MAIN_MENU,
    )


# ═══════════════════════════════════════════════════════════════════
# КАЛЬКУЛЯТОР СНАРЯЖЕНИЯ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🏂 Калькулятор")
async def calc_menu(message: Message, state: FSMContext, db: Database) -> None:
    await ensure_user(db, message)
    await set_state(db, state, message.from_user.id, None)
    await message.answer(
        "🧮 <b>Калькулятор снаряжения</b>\n\nВыбери тип:",
        reply_markup=calc_type_kb(),
    )


# --- Сноуборд ---
@router.callback_query(F.data == "calc:snowboard")
async def calc_snowboard_start(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    await set_state(db, state, query.from_user.id, SnowboardCalcStates.waiting_height)
    await query.message.answer("📏 Введи свой <b>рост</b> в см (например, 175):", reply_markup=BACK_KB)
    await query.answer()


@router.message(SnowboardCalcStates.waiting_height)
async def calc_sb_height(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введи рост числом, например: 175")
        return
    height = int(message.text)
    if height < 100 or height > 220:
        await message.answer("❌ Рост должен быть от 100 до 220 см")
        return
    await state.update_data(height=height)
    await set_state(db, state, message.from_user.id, SnowboardCalcStates.waiting_weight)
    await message.answer("⚖️ Введи свой <b>вес</b> в кг (например, 70):")


@router.message(SnowboardCalcStates.waiting_weight)
async def calc_sb_weight(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введи вес числом, например: 70")
        return
    weight = int(message.text)
    if weight < 30 or weight > 200:
        await message.answer("❌ Вес должен быть от 30 до 200 кг")
        return
    await state.update_data(weight=weight)
    await set_state(db, state, message.from_user.id, SnowboardCalcStates.waiting_gender)
    await message.answer("👤 Выбери <b>пол</b>:", reply_markup=gender_kb())


@router.callback_query(SnowboardCalcStates.waiting_gender, F.data.startswith("gender:"))
async def calc_sb_gender(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    gender = query.data.split(":")[1]
    await state.update_data(gender=gender)
    await set_state(db, state, query.from_user.id, SnowboardCalcStates.waiting_shoe_size)
    await query.message.answer("👟 Введи <b>размер обуви</b> (EU, например 42):", reply_markup=BACK_KB)
    await query.answer()


@router.message(SnowboardCalcStates.waiting_shoe_size)
async def calc_sb_shoe_size(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введи размер числом, например: 42")
        return
    shoe_size = int(message.text)
    if shoe_size < 30 or shoe_size > 55:
        await message.answer("❌ Размер должен быть от 30 до 55")
        return
    await state.update_data(shoe_size=shoe_size)
    await set_state(db, state, message.from_user.id, SnowboardCalcStates.waiting_style)
    await message.answer("🏔️ Выбери <b>стиль катания</b>:", reply_markup=snowboard_style_kb())


@router.callback_query(SnowboardCalcStates.waiting_style, F.data.startswith("style:"))
async def calc_sb_style(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    style = query.data.split(":")[1]
    data = await state.get_data()
    result = calculate_snowboard_length(
        height_cm=data["height"],
        weight_kg=data["weight"],
        gender=data["gender"],
        shoe_size=data["shoe_size"],
        style=style,
    )
    await set_state(db, state, query.from_user.id, None)
    
    # Формируем размер с W если нужно
    size_str = f"{result.min_length}–{result.max_length}"
    if result.width:
        size_str += result.width
    
    await query.message.answer(
        f"🏂 <b>Рекомендуемый размер сноуборда:</b>\n\n"
        f"📐 <b>{size_str} см</b>\n\n"
        f"{result.explanation}\n\n"
        f"{result.tips}",
        reply_markup=MAIN_MENU,
    )
    await query.answer()


# --- Лыжи ---
@router.callback_query(F.data == "calc:ski")
async def calc_ski_start(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    await set_state(db, state, query.from_user.id, SkiCalcStates.waiting_height)
    await query.message.answer("📏 Введи свой <b>рост</b> в см (например, 175):", reply_markup=BACK_KB)
    await query.answer()


@router.message(SkiCalcStates.waiting_height)
async def calc_ski_height(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введи рост числом, например: 175")
        return
    height = int(message.text)
    if height < 100 or height > 220:
        await message.answer("❌ Рост должен быть от 100 до 220 см")
        return
    await state.update_data(height=height)
    await set_state(db, state, message.from_user.id, SkiCalcStates.waiting_weight)
    await message.answer("⚖️ Введи свой <b>вес</b> в кг (например, 70):")


@router.message(SkiCalcStates.waiting_weight)
async def calc_ski_weight(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введи вес числом, например: 70")
        return
    weight = int(message.text)
    if weight < 30 or weight > 200:
        await message.answer("❌ Вес должен быть от 30 до 200 кг")
        return
    await state.update_data(weight=weight)
    await set_state(db, state, message.from_user.id, SkiCalcStates.waiting_level)
    await message.answer("🎿 Выбери <b>уровень катания</b>:", reply_markup=level_kb())


@router.callback_query(SkiCalcStates.waiting_level, F.data.startswith("level:"))
async def calc_ski_level(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    level = query.data.split(":")[1]
    await state.update_data(level=level)
    await set_state(db, state, query.from_user.id, SkiCalcStates.waiting_style)
    await query.message.answer("🏔️ Выбери <b>стиль катания</b>:", reply_markup=ski_style_kb())
    await query.answer()


@router.callback_query(SkiCalcStates.waiting_style, F.data.startswith("style:"))
async def calc_ski_style(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    style = query.data.split(":")[1]
    data = await state.get_data()
    result = calculate_ski_length(
        height_cm=data["height"],
        weight_kg=data["weight"],
        level=data["level"],
        style=style,
    )
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer(
        f"⛷️ <b>Рекомендуемый размер лыж:</b>\n\n"
        f"📐 Длина: <b>{result.min_length}–{result.max_length} см</b>\n"
        f"📏 Ширина талии: <b>{result.waist}</b>\n"
        f"🔄 Радиус поворота: <b>{result.radius}</b>\n\n"
        f"💡 {result.explanation}",
        reply_markup=MAIN_MENU,
    )
    await query.answer()


# ═══════════════════════════════════════════════════════════════════
# СКЛОНЫ РЯДОМ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🏔️ Склоны")
async def resorts_menu(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    if profile and profile["location_lat"] is not None and profile["location_lon"] is not None:
        await state.update_data(user_lat=profile["location_lat"], user_lon=profile["location_lon"])
        await show_resorts(message, state, db, profile["location_lat"], profile["location_lon"])
        return
    
    await set_state(db, state, message.from_user.id, ResortStates.waiting_location)
    await message.answer(
        "📍 Отправь свою геолокацию, чтобы найти ближайшие склоны.",
        reply_markup=LOCATION_KB,
    )


@router.message(ResortStates.waiting_location, F.location)
async def resorts_got_location(message: Message, state: FSMContext, db: Database) -> None:
    loc = message.location
    user_id = await ensure_user(db, message)
    
    profile = await db.get_profile(user_id)
    if profile:
        await db.update_profile_location(user_id, loc.latitude, loc.longitude)
    
    await state.update_data(user_lat=loc.latitude, user_lon=loc.longitude)
    await show_resorts(message, state, db, loc.latitude, loc.longitude)


async def show_resorts(message: Message, state: FSMContext, db: Database, lat: float, lon: float) -> None:
    await set_state(db, state, message.from_user.id, None)
    resorts_rows = await db.list_resorts()
    resorts = [dict(row) for row in resorts_rows]
    sorted_resorts = sort_by_distance(lat, lon, resorts)
    top5 = sorted_resorts[:5]
    
    await message.answer(
        "🏔️ <b>Ближайшие склоны:</b>",
        reply_markup=resorts_list_kb(top5),
    )


@router.callback_query(F.data == "nav:resorts")
async def cb_nav_resorts(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    lat = data.get("user_lat")
    lon = data.get("user_lon")
    if lat is None or lon is None:
        await query.message.answer("📍 Отправь геолокацию снова.", reply_markup=LOCATION_KB)
        await set_state(db, state, query.from_user.id, ResortStates.waiting_location)
    else:
        resorts_rows = await db.list_resorts()
        resorts = [dict(row) for row in resorts_rows]
        sorted_resorts = sort_by_distance(lat, lon, resorts)
        top5 = sorted_resorts[:5]
        await query.message.answer("🏔️ <b>Ближайшие склоны:</b>", reply_markup=resorts_list_kb(top5))
    await query.answer()


@router.message(ResortStates.waiting_location)
async def resorts_invalid(message: Message) -> None:
    await message.answer("❌ Отправь геолокацию через кнопку ниже.")


@router.callback_query(F.data == "resorts:cities")
async def cb_resorts_cities(query: CallbackQuery, db: Database) -> None:
    cities = await db.get_resort_cities()
    await query.message.answer(
        "🌍 <b>Выбери регион:</b>",
        reply_markup=cities_list_kb(cities),
    )
    await query.answer()


@router.callback_query(F.data.startswith("city:"))
async def cb_city_resorts(query: CallbackQuery, db: Database) -> None:
    city = query.data.split(":", 1)[1]
    resorts = await db.get_resorts_by_city(city)
    resorts_list = list(resorts)
    
    if not resorts_list:
        await query.answer("Склоны не найдены", show_alert=True)
        return
    
    await query.message.answer(
        f"🏔️ <b>Склоны: {city}</b>",
        reply_markup=city_resorts_kb(resorts_list, city),
    )
    await query.answer()


@router.callback_query(F.data.startswith("resort:"))
async def resort_details(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    resort_id = int(query.data.split(":")[1])
    resort = await db.get_resort(resort_id)
    if not resort:
        await query.answer("Склон не найден", show_alert=True)
        return
    
    data = await state.get_data()
    dist_str = ""
    if data.get("user_lat") and data.get("user_lon"):
        dist = haversine_km(data["user_lat"], data["user_lon"], resort["lat"], resort["lon"])
        dist_str = f"\n📏 <b>{dist:.0f} км</b> от тебя" if dist >= 1 else f"\n📏 <b>{dist * 1000:.0f} м</b> от тебя"
    
    site_str = f'<a href="{resort["site"]}">{resort["site"]}</a>' if resort["site"] else "—"
    
    # Погода
    weather_str = ""
    weather = await get_weather(resort["lat"], resort["lon"], config.weather_api_key)
    if weather:
        weather_str = f"\n\n<b>Погода сейчас:</b>\n{format_weather(weather)}"
    
    text = (
        f"🏔️ <b>{resort['name']}</b>\n\n"
        f"📍 {resort['address'] or '—'}{dist_str}\n"
        f"🎿 Трасс: <b>{resort['trails_count'] or '—'}</b>\n"
        f"🎚️ Уровни: {resort['trail_levels'] or '—'}\n"
        f"🚡 Подъёмников: <b>{resort['lifts_count'] or '—'}</b>\n"
        f"🌐 {site_str}"
        f"{weather_str}"
    )
    await query.message.answer(text, reply_markup=resort_back_kb(), disable_web_page_preview=True)
    await query.answer()


# ═══════════════════════════════════════════════════════════════════
# ПРОФИЛЬ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "👤 Профиль")
async def profile_menu(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    if profile:
        profile_dict = dict(profile)
        text = format_profile(profile_dict)
        await send_profile_with_photos(message, profile_dict, text, profile_actions_kb())
        return
    
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_photos)
    await state.update_data(photos=[])
    await message.answer(
        "📸 Пришли фото для профиля (можно несколько) или пропусти.",
        reply_markup=BACK_KB,
    )
    await message.answer("👇", reply_markup=profile_photo_kb())


@router.callback_query(F.data == "profile:skip_photo")
async def profile_skip_photo(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.update_data(photos=[])
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_gender)
    await query.message.answer("👤 Выбери <b>пол</b>:", reply_markup=profile_gender_kb())
    await query.answer()


@router.message(ProfileStates.waiting_photos, F.photo)
async def profile_got_photo(message: Message, state: FSMContext, db: Database) -> None:
    photo = message.photo[-1]
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(photo.file_id)
    await state.update_data(photos=photos)
    
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_more_photos)
    await message.answer(
        f"✅ Фото добавлено ({len(photos)}/10)\n\nДобавить ещё или продолжить?",
        reply_markup=profile_more_photos_kb(),
    )


@router.message(ProfileStates.waiting_photos)
async def profile_photo_invalid(message: Message) -> None:
    await message.answer("📸 Пришли фото или нажми «Пропустить».")


@router.message(ProfileStates.waiting_more_photos, F.photo)
async def profile_more_photo(message: Message, state: FSMContext, db: Database) -> None:
    photo = message.photo[-1]
    data = await state.get_data()
    photos = data.get("photos", [])
    
    if len(photos) >= 10:
        await message.answer("❌ Максимум 10 фото. Нажми «Готово».")
        return
    
    photos.append(photo.file_id)
    await state.update_data(photos=photos)
    
    await message.answer(
        f"✅ Фото добавлено ({len(photos)}/10)\n\nДобавить ещё или продолжить?",
        reply_markup=profile_more_photos_kb(),
    )


@router.callback_query(F.data == "profile:more_photos")
async def profile_want_more(query: CallbackQuery) -> None:
    await query.message.answer("📸 Пришли ещё фото:")
    await query.answer()


@router.callback_query(F.data == "profile:photos_done")
async def profile_photos_done(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_gender)
    await query.message.answer("👤 Выбери <b>пол</b>:", reply_markup=profile_gender_kb())
    await query.answer()


@router.callback_query(ProfileStates.waiting_gender, F.data.startswith("pgender:"))
async def profile_gender(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    gender = query.data.split(":")[1]
    await state.update_data(gender=gender)
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_ride_type)
    await query.message.answer("🎿 Выбери тип катания:", reply_markup=ride_type_kb())
    await query.answer()


@router.callback_query(ProfileStates.waiting_ride_type, F.data.startswith("ride:"))
async def profile_ride_type(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    ride_type = query.data.split(":", 1)[1]
    await state.update_data(ride_type=ride_type)
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_skill_level)
    await query.message.answer("📊 Выбери уровень:", reply_markup=profile_level_kb())
    await query.answer()


@router.callback_query(ProfileStates.waiting_skill_level, F.data.startswith("plevel:"))
async def profile_skill_level(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    level = query.data.split(":")[1]
    await state.update_data(skill_level=level)
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_age)
    await query.message.answer("🎂 Введи свой возраст:", reply_markup=BACK_KB)
    await query.answer()


@router.message(ProfileStates.waiting_age)
async def profile_age(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введи возраст числом.")
        return
    age = int(message.text)
    if age < 12 or age > 80:
        await message.answer("❌ Возраст должен быть от 12 до 80 лет.")
        return
    await state.update_data(age=age)
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_city)
    await message.answer(
        "📍 Введи <b>город</b> или отправь геолокацию:",
        reply_markup=LOCATION_KB,
    )


@router.message(ProfileStates.waiting_city, F.location)
async def profile_city_location(message: Message, state: FSMContext, db: Database) -> None:
    loc = message.location
    resorts = await db.list_resorts()
    nearest = min(resorts, key=lambda r: haversine_km(loc.latitude, loc.longitude, r["lat"], r["lon"]))
    city = nearest["address"] if nearest else "Неизвестно"
    
    await state.update_data(city=city, location_lat=loc.latitude, location_lon=loc.longitude)
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_about)
    await message.answer(
        f"📍 Определено: <b>{city}</b>\n\n💬 Напиши пару слов о себе:",
        reply_markup=BACK_KB,
    )


@router.message(ProfileStates.waiting_city, F.text)
async def profile_city_text(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        return
    await state.update_data(city=message.text.strip(), location_lat=None, location_lon=None)
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_about)
    await message.answer("💬 Напиши пару слов о себе:", reply_markup=BACK_KB)


@router.message(ProfileStates.waiting_about)
async def profile_about(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        return
    
    data = await state.get_data()
    user_id = await ensure_user(db, message)
    
    await db.upsert_profile(
        user_id=user_id,
        ride_type=data["ride_type"],
        skill_level=data["skill_level"],
        age=data["age"],
        city=data["city"],
        about=message.text.strip(),
        photos=data.get("photos", []),
        gender=data.get("gender", ""),
        location_lat=data.get("location_lat"),
        location_lon=data.get("location_lon"),
    )
    
    await set_state(db, state, message.from_user.id, None)
    
    profile = await db.get_profile(user_id)
    profile_dict = dict(profile)
    text = f"✅ Профиль сохранён!\n\n{format_profile(profile_dict)}"
    
    await send_profile_with_photos(message, profile_dict, text, profile_actions_kb())


@router.callback_query(F.data == "profile:edit")
async def profile_edit(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_photos)
    await state.update_data(photos=[])
    await query.message.answer("📸 Пришли новые фото или пропусти:", reply_markup=BACK_KB)
    await query.message.answer("👇", reply_markup=profile_photo_kb())
    await query.answer()


@router.callback_query(F.data == "profile:delete")
async def profile_delete(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, query)
    await db.delete_profile(user_id)
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer("🗑️ Профиль удалён.", reply_markup=MAIN_MENU)
    await query.answer()


# ═══════════════════════════════════════════════════════════════════
# ИЗМЕНИТЬ ОПИСАНИЕ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🎿 Где катаюсь")
async def edit_riding_plans(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    if not profile:
        await message.answer(
            "❌ Сначала создай профиль в разделе «👤 Профиль»",
            reply_markup=MAIN_MENU,
        )
        return
    
    current_about = profile["about"] if profile["about"] else ""
    await set_state(db, state, message.from_user.id, EditDescriptionStates.waiting_description)
    
    hint = ""
    if current_about:
        hint = f"Сейчас: <i>{current_about}</i>\n\n"
    
    await message.answer(
        f"🎿 <b>Где катаюсь</b>\n\n{hint}"
        "Напиши куда планируешь поехать кататься — курорт, даты, время.\n"
        "Это увидят другие райдеры в поиске компании.\n\n"
        "Например: «Шерегеш, 25-28 января, ищу компанию на фрирайд»",
        reply_markup=BACK_KB,
    )


@router.message(EditDescriptionStates.waiting_description)
async def edit_riding_plans_got(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        return
    
    user_id = await ensure_user(db, message)
    new_about = message.text.strip()
    
    await db.update_about(user_id, new_about)
    await set_state(db, state, message.from_user.id, None)
    await message.answer("✅ Планы сохранены! Теперь их увидят другие райдеры.", reply_markup=MAIN_MENU)


# ═══════════════════════════════════════════════════════════════════
# КОНТАКТЫ (МЭТЧИ)
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🤝 Контакты")
async def contacts_menu(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    matches = await db.get_user_matches(user_id)
    matches_list = list(matches)
    
    if not matches_list:
        await message.answer(
            "📭 У тебя пока нет контактов.\n\n"
            "Лайкай анкеты в разделе «🔍 Искать компанию» — "
            "при взаимном интересе контакт появится здесь!",
            reply_markup=MAIN_MENU,
        )
        return
    
    await message.answer(
        f"🤝 <b>Твои контакты</b> ({len(matches_list)})\n\n"
        "Это райдеры, с которыми у вас взаимный интерес:",
        reply_markup=contacts_kb(matches_list),
    )


# ═══════════════════════════════════════════════════════════════════
# СОЗДАНИЕ СОБЫТИЯ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "📅 Создать событие")
async def event_create_start(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    if not profile:
        await message.answer(
            "❌ Сначала создай профиль в разделе «👤 Профиль»",
            reply_markup=MAIN_MENU,
        )
        return
    
    await set_state(db, state, message.from_user.id, EventStates.waiting_group_link)
    await message.answer(
        "📅 <b>Создание события</b>\n\n"
        "Событие — это групповой выезд на курорт.\n\n"
        "<b>Инструкция:</b>\n"
        "1️⃣ Создай группу в Telegram для участников\n"
        "2️⃣ Сделай её публичной или получи ссылку-приглашение\n"
        "3️⃣ Скопируй ссылку на группу (например: https://t.me/+ABC123)\n\n"
        "📎 <b>Пришли ссылку на группу:</b>",
        reply_markup=BACK_KB,
    )


@router.message(EventStates.waiting_group_link)
async def event_got_group_link(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        return
    
    link = message.text.strip()
    if not (link.startswith("https://t.me/") or link.startswith("t.me/")):
        await message.answer("❌ Пришли корректную ссылку на Telegram-группу (начинается с https://t.me/)")
        return
    
    await state.update_data(telegram_group_link=link)
    await set_state(db, state, message.from_user.id, EventStates.waiting_photo)
    await message.answer(
        "📸 Пришли фото/обложку события (необязательно):",
        reply_markup=event_photo_kb(),
    )


@router.callback_query(EventStates.waiting_photo, F.data == "event:skip_photo")
async def event_skip_photo(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.update_data(photo_file_id=None)
    await set_state(db, state, query.from_user.id, EventStates.waiting_resort)
    
    resorts = await db.list_resorts()
    await query.message.answer(
        "🏔️ Выбери курорт:",
        reply_markup=event_resorts_kb(list(resorts)),
    )
    await query.answer()


@router.message(EventStates.waiting_photo, F.photo)
async def event_got_photo(message: Message, state: FSMContext, db: Database) -> None:
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await set_state(db, state, message.from_user.id, EventStates.waiting_resort)
    
    resorts = await db.list_resorts()
    await message.answer(
        "🏔️ Выбери курорт:",
        reply_markup=event_resorts_kb(list(resorts)),
    )


@router.message(EventStates.waiting_photo)
async def event_photo_invalid(message: Message) -> None:
    await message.answer("📸 Пришли фото или нажми «Пропустить».")


@router.callback_query(EventStates.waiting_resort, F.data.startswith("evresort:"))
async def event_got_resort(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    resort_id = int(query.data.split(":")[1])
    resort = await db.get_resort(resort_id)
    
    await state.update_data(resort_id=resort_id, resort_name=resort["name"])
    await set_state(db, state, query.from_user.id, EventStates.waiting_date)
    await query.message.answer(
        f"📆 Курорт: <b>{resort['name']}</b>\n\n"
        "Введи дату события (например: 25.01.2026 или 25-28 января):",
        reply_markup=BACK_KB,
    )
    await query.answer()


@router.message(EventStates.waiting_date)
async def event_got_date(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        return
    
    await state.update_data(event_date=message.text.strip())
    await set_state(db, state, message.from_user.id, EventStates.waiting_level)
    await message.answer(
        "🎿 Выбери уровень участников:",
        reply_markup=event_level_kb(),
    )


@router.callback_query(EventStates.waiting_level, F.data.startswith("evlevel:"))
async def event_got_level(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    level = query.data.split(":")[1]
    await state.update_data(skill_level=level)
    await set_state(db, state, query.from_user.id, EventStates.waiting_description)
    await query.message.answer(
        "💬 Добавь описание события (необязательно):\n\n"
        "Например: «Фрирайд по целине, нужен свой транспорт»\n\n"
        "Или нажми /skip чтобы пропустить.",
        reply_markup=BACK_KB,
    )
    await query.answer()


@router.message(EventStates.waiting_description, F.text == "/skip")
async def event_skip_description(message: Message, state: FSMContext, db: Database) -> None:
    await state.update_data(description=None)
    await show_event_preview(message, state, db)


@router.message(EventStates.waiting_description)
async def event_got_description(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        return
    
    await state.update_data(description=message.text.strip())
    await show_event_preview(message, state, db)


async def show_event_preview(message: Message, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    
    level_icons = {"Новичок": "🟢", "Средний": "🔵", "Продвинутый": "🔴", "Любой": "⚪"}
    level_icon = level_icons.get(data["skill_level"], "⚪")
    
    text = (
        "📅 <b>Предпросмотр события</b>\n\n"
        f"🏔️ {data['resort_name']}\n"
        f"📆 {data['event_date']}\n"
        f"{level_icon} Уровень: {data['skill_level']}\n"
    )
    if data.get("description"):
        text += f"💬 {data['description']}\n"
    text += f"\n🔗 Группа: {data['telegram_group_link']}"
    
    if data.get("photo_file_id"):
        await message.answer_photo(data["photo_file_id"], caption=text, reply_markup=event_confirm_kb())
    else:
        await message.answer(text, reply_markup=event_confirm_kb())


@router.callback_query(F.data == "event:confirm")
async def event_confirm(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    user_id = await ensure_user(db, query)
    
    event_id = await db.create_event(
        creator_id=user_id,
        resort_id=data["resort_id"],
        event_date=data["event_date"],
        skill_level=data["skill_level"],
        telegram_group_link=data["telegram_group_link"],
        photo_file_id=data.get("photo_file_id"),
        description=data.get("description"),
    )
    
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer(
        f"✅ Событие создано!\n\n"
        f"Теперь оно будет показываться в поиске компании.\n"
        f"Райдеры смогут присоединиться к твоей группе.",
        reply_markup=MAIN_MENU,
    )
    await query.answer()


# ═══════════════════════════════════════════════════════════════════
# ПОИСК КОМПАНИИ (профили + события)
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🔍 Искать компанию")
async def buddy_menu(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    if not profile:
        await message.answer(
            "❌ Сначала создай профиль в разделе «👤 Профиль»",
            reply_markup=MAIN_MENU,
        )
        return
    
    # Сохраняем гео для расчёта расстояний
    if profile["location_lat"] and profile["location_lon"]:
        await state.update_data(user_lat=profile["location_lat"], user_lon=profile["location_lon"])
    
    # Сразу переходим к просмотру анкет
    await set_state(db, state, message.from_user.id, BuddySearchStates.browsing)
    await start_buddy_browsing(message, state, db)


async def start_buddy_browsing(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    
    # Получаем профили (кроме себя)
    profiles = await db.get_all_profiles(user_id)
    # Получаем активные события
    events = await db.get_active_events()
    
    # Убираем уже лайкнутых
    already_liked = await db.get_already_liked(user_id)
    
    # Собираем кандидатов: профили как ("profile", user_id), события как ("event", event_id)
    candidates = []
    for row in profiles:
        if row["user_id"] not in already_liked:
            candidates.append(("profile", row["user_id"]))
    for row in events:
        # События от себя не показываем
        if row["creator_id"] != user_id:
            candidates.append(("event", row["id"]))
    
    await state.update_data(candidates=candidates, candidate_index=0)
    
    if not candidates:
        await set_state(db, state, message.from_user.id, None)
        await message.answer(
            "😔 Пока нет других райдеров и событий.\n\n"
            "Ты уже в поиске — другие увидят тебя!",
            reply_markup=back_to_menu_kb(),
        )
        return
    
    await message.answer(f"🔍 Найдено: {len(candidates)}")
    await show_next_candidate(message, state, db)


async def show_next_candidate(message: Message, state: FSMContext, db: Database) -> None:
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
    profile = await db.get_profile(user_id)
    if not profile:
        await show_next_candidate(message, state, db)
        return
    
    profile_dict = dict(profile)
    data = await state.get_data()
    user_lat = data.get("user_lat")
    user_lon = data.get("user_lon")
    text = format_profile(profile_dict, user_lat, user_lon)
    
    await send_profile_with_photos(message, profile_dict, text, buddy_actions_kb())


async def show_event_candidate(message: Message, state: FSMContext, db: Database, event_id: int) -> None:
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


@router.callback_query(BuddySearchStates.browsing, F.data == "buddy:like")
async def buddy_like(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    candidate_type = data.get("current_candidate_type")
    candidate_id = data.get("current_candidate_id")
    
    if not candidate_id:
        await query.answer("Ошибка", show_alert=True)
        return
    
    user_id = await ensure_user(db, query)
    
    if candidate_type == "profile":
        await db.add_like(user_id, candidate_id)
        
        # Уведомляем о лайке
        await notify_like(db, user_id, candidate_id, query.bot)
        
        # Проверяем взаимность
        if await db.has_like(candidate_id, user_id):
            await db.add_match(user_id, candidate_id)
            await notify_match(db, user_id, candidate_id, query.from_user.id, query.bot)
            await query.message.answer("🎿 <b>Пойдём катать?</b>")
    
    await show_next_candidate(query.message, state, db)
    await query.answer("👍")


@router.callback_query(BuddySearchStates.browsing, F.data.startswith("event:join:"))
async def event_join(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    event_id = int(query.data.split(":")[2])
    event = await db.get_event(event_id)
    
    if not event:
        await query.answer("Событие не найдено", show_alert=True)
        await show_next_candidate(query.message, state, db)
        return
    
    # Показываем ссылку на группу
    await query.message.answer(
        f"🎿 <b>Присоединяйся!</b>\n\n"
        f"🏔️ {event['resort_name']} — {event['event_date']}\n\n"
        f"👥 Вступай в группу: {event['telegram_group_link']}",
    )
    
    await show_next_candidate(query.message, state, db)
    await query.answer("👍")


@router.callback_query(BuddySearchStates.browsing, F.data == "buddy:skip")
async def buddy_skip(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    await show_next_candidate(query.message, state, db)
    await query.answer("👎")


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
            "Загляни в «🔍 Искать компанию», чтобы посмотреть анкету.",
        )
    except Exception:
        pass  # пользователь заблокировал бота


async def notify_match(db: Database, user_id: int, candidate_id: int, telegram_id: int, bot: Bot) -> None:
    """Уведомить обоих о взаимном интересе."""
    target_user = await db.get_user_by_id(candidate_id)
    current_user = await db.get_user_by_id(user_id)
    if not target_user or not current_user:
        return
    
    current_link = f"@{current_user['username']}" if current_user["username"] else f"tg://user?id={current_user['telegram_id']}"
    candidate_link = f"@{target_user['username']}" if target_user["username"] else f"tg://user?id={target_user['telegram_id']}"
    
    await bot.send_message(
        telegram_id,
        f"💬 Напиши: {candidate_link}"
    )
    
    if target_user["telegram_id"] != telegram_id:
        try:
            await bot.send_message(
                target_user["telegram_id"],
                f"🎿 <b>Пойдём катать?</b>\n\n💬 Напиши: {current_link}",
            )
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════
# МОИ СОБЫТИЯ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🗓️ Мои события")
async def my_events_menu(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    events = await db.get_user_events(user_id)
    events_list = list(events)
    
    if not events_list:
        await message.answer(
            "📭 У тебя пока нет созданных событий.\n\n"
            "Создай событие, чтобы собрать компанию на катание!",
            reply_markup=my_events_kb([]),
        )
        return
    
    await message.answer(
        f"🗓️ <b>Твои события</b> ({len(events_list)})",
        reply_markup=my_events_kb(events_list),
    )


@router.callback_query(F.data == "nav:my_events")
async def cb_my_events(query: CallbackQuery, db: Database) -> None:
    user_id = await ensure_user(db, query)
    events = await db.get_user_events(user_id)
    events_list = list(events)
    
    await query.message.answer(
        f"🗓️ <b>Твои события</b> ({len(events_list)})" if events_list else "📭 У тебя пока нет событий.",
        reply_markup=my_events_kb(events_list),
    )
    await query.answer()


@router.callback_query(F.data == "nav:create_event")
async def cb_create_event(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, query)
    profile = await db.get_profile(user_id)
    
    if not profile:
        await query.message.answer("❌ Сначала создай профиль в разделе «👤 Профиль»", reply_markup=MAIN_MENU)
        await query.answer()
        return
    
    await set_state(db, state, query.from_user.id, EventStates.waiting_group_link)
    await query.message.answer(
        "📅 <b>Создание события</b>\n\n"
        "Событие — это групповой выезд на курорт.\n\n"
        "<b>Инструкция:</b>\n"
        "1️⃣ Создай группу в Telegram для участников\n"
        "2️⃣ Сделай её публичной или получи ссылку-приглашение\n"
        "3️⃣ Скопируй ссылку на группу (например: https://t.me/+ABC123)\n\n"
        "📎 <b>Пришли ссылку на группу:</b>",
        reply_markup=BACK_KB,
    )
    await query.answer()


@router.callback_query(F.data.startswith("myevent:"))
async def my_event_details(query: CallbackQuery, db: Database) -> None:
    event_id = int(query.data.split(":")[1])
    event = await db.get_event(event_id)
    
    if not event:
        await query.answer("Событие не найдено", show_alert=True)
        return
    
    level_icons = {"Новичок": "🟢", "Средний": "🔵", "Продвинутый": "🔴", "Любой": "⚪"}
    level_icon = level_icons.get(event["skill_level"], "⚪")
    
    text = (
        f"📅 <b>Твоё событие</b>\n\n"
        f"🏔️ {event['resort_name']}\n"
        f"📆 {event['event_date']}\n"
        f"{level_icon} Уровень: {event['skill_level']}\n"
        f"🔗 {event['telegram_group_link']}"
    )
    if event.get("description"):
        text += f"\n💬 {event['description']}"
    
    await query.message.answer(text, reply_markup=my_event_actions_kb(event_id))
    await query.answer()


@router.callback_query(F.data.startswith("delevent:"))
async def delete_my_event(query: CallbackQuery, db: Database) -> None:
    event_id = int(query.data.split(":")[1])
    await db.deactivate_event(event_id)
    await query.message.answer("🗑️ Событие удалено.", reply_markup=MAIN_MENU)
    await query.answer()


# ═══════════════════════════════════════════════════════════════════
# КАЛЕНДАРЬ СОБЫТИЙ
# ═══════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "nav:calendar")
async def cb_calendar(query: CallbackQuery) -> None:
    await query.message.answer(
        "📆 <b>Календарь событий</b>\n\n"
        "Выбери период:",
        reply_markup=events_calendar_kb(),
    )
    await query.answer()


@router.callback_query(F.data.startswith("calendar:"))
async def cb_calendar_filter(query: CallbackQuery, db: Database) -> None:
    period = query.data.split(":")[1]
    events = await db.get_active_events()
    events_list = list(events)
    
    # Фильтруем по периоду
    from datetime import datetime, timedelta
    today = datetime.now().date()
    
    if period == "week":
        end_date = today + timedelta(days=7)
        title = "на этой неделе"
    elif period == "month":
        end_date = today + timedelta(days=30)
        title = "в этом месяце"
    else:
        end_date = today + timedelta(days=365)
        title = "все"
    
    # Простая фильтрация (даты в произвольном формате, поэтому показываем все)
    filtered = events_list if period == "all" else events_list[:10]
    
    if not filtered:
        await query.message.answer(
            "😔 Событий пока нет.\n\nСоздай своё!",
            reply_markup=events_calendar_kb(),
        )
    else:
        await query.message.answer(
            f"📆 <b>События {title}</b> ({len(filtered)})",
            reply_markup=events_list_kb(filtered),
        )
    await query.answer()


@router.callback_query(F.data.startswith("viewevent:"))
async def view_event(query: CallbackQuery, db: Database) -> None:
    event_id = int(query.data.split(":")[1])
    event = await db.get_event(event_id)
    
    if not event:
        await query.answer("Событие не найдено", show_alert=True)
        return
    
    level_icons = {"Новичок": "🟢", "Средний": "🔵", "Продвинутый": "🔴", "Любой": "⚪"}
    level_icon = level_icons.get(event["skill_level"], "⚪")
    
    text = (
        f"📅 <b>Событие</b>\n\n"
        f"🏔️ {event['resort_name']}\n"
        f"📆 {event['event_date']}\n"
        f"{level_icon} Уровень: {event['skill_level']}\n"
        f"👤 Организатор: {event['creator_name']}"
    )
    if event.get("description"):
        text += f"\n\n💬 {event['description']}"
    
    await query.message.answer(
        text,
        reply_markup=event_view_kb(event_id, event["telegram_group_link"]),
    )
    await query.answer()


@router.callback_query(F.data.startswith("remind:"))
async def set_reminder(query: CallbackQuery, db: Database) -> None:
    event_id = int(query.data.split(":")[1])
    user_id = await ensure_user(db, query)
    event = await db.get_event(event_id)
    
    if not event:
        await query.answer("Событие не найдено", show_alert=True)
        return
    
    # Напоминаем за 24 часа (упрощённо — используем текущую дату как remind_at)
    from datetime import datetime
    remind_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    try:
        await db.add_event_reminder(user_id, event_id, remind_at)
        await query.answer("🔔 Напоминание установлено!", show_alert=True)
    except Exception:
        await query.answer("⚠️ Напоминание уже установлено", show_alert=True)


# ═══════════════════════════════════════════════════════════════════
# SOS
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🆘 SOS")
async def sos_menu(message: Message, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    resorts = await db.list_resorts()
    resorts_list = []
    
    # Если есть геолокация — фильтруем по расстоянию (до 100 км)
    user_lat = profile["location_lat"] if profile and profile["location_lat"] else None
    user_lon = profile["location_lon"] if profile and profile["location_lon"] else None
    
    for r in resorts:
        if not r["rescue_phone"]:
            continue
        resort_dict = dict(r)
        if user_lat and user_lon:
            dist = haversine_km(user_lat, user_lon, r["lat"], r["lon"])
            if dist <= 100:
                resort_dict["distance"] = dist
                resorts_list.append(resort_dict)
        else:
            resorts_list.append(resort_dict)
    
    # Сортируем по расстоянию
    resorts_list.sort(key=lambda x: x.get("distance", 9999))
    
    if not resorts_list and user_lat:
        # Если нет курортов в радиусе 100 км — показываем ближайшие 5
        all_resorts = []
        for r in resorts:
            if r["rescue_phone"]:
                resort_dict = dict(r)
                resort_dict["distance"] = haversine_km(user_lat, user_lon, r["lat"], r["lon"])
                all_resorts.append(resort_dict)
        all_resorts.sort(key=lambda x: x["distance"])
        resorts_list = all_resorts[:5]
    
    # Формируем текст с номерами
    lines = ["🆘 <b>Экстренная помощь</b>\n"]
    lines.append("📞 <b>Единая служба спасения: 112</b>\n")
    
    if resorts_list:
        lines.append("━━━━━━━━━━━━━━━━━━━━\n")
        for resort in resorts_list[:8]:
            dist_str = f" ({resort['distance']:.0f} км)" if resort.get("distance") else ""
            lines.append(f"🏔️ <b>{resort['name']}</b>{dist_str}")
            lines.append(f"📞 <code>{resort['rescue_phone']}</code>\n")
    
    geo_hint = ""
    if not user_lat:
        geo_hint = "\n💡 <i>Обнови геолокацию в профиле для показа ближайших курортов.</i>"
    
    lines.append(f"\n⚠️ Нажми на номер, чтобы скопировать.{geo_hint}")
    
    await message.answer("\n".join(lines), reply_markup=sos_back_kb())


@router.callback_query(F.data == "nav:sos")
async def cb_sos(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    user_id = await ensure_user(db, query)
    profile = await db.get_profile(user_id)
    
    resorts = await db.list_resorts()
    resorts_list = []
    
    user_lat = profile["location_lat"] if profile and profile["location_lat"] else None
    user_lon = profile["location_lon"] if profile and profile["location_lon"] else None
    
    for r in resorts:
        if not r["rescue_phone"]:
            continue
        resort_dict = dict(r)
        if user_lat and user_lon:
            dist = haversine_km(user_lat, user_lon, r["lat"], r["lon"])
            if dist <= 100:
                resort_dict["distance"] = dist
                resorts_list.append(resort_dict)
        else:
            resorts_list.append(resort_dict)
    
    resorts_list.sort(key=lambda x: x.get("distance", 9999))
    
    if not resorts_list and user_lat:
        all_resorts = []
        for r in resorts:
            if r["rescue_phone"]:
                resort_dict = dict(r)
                resort_dict["distance"] = haversine_km(user_lat, user_lon, r["lat"], r["lon"])
                all_resorts.append(resort_dict)
        all_resorts.sort(key=lambda x: x["distance"])
        resorts_list = all_resorts[:5]
    
    lines = ["🆘 <b>Экстренная помощь</b>\n"]
    lines.append("📞 <b>Единая служба спасения: 112</b>\n")
    
    if resorts_list:
        lines.append("━━━━━━━━━━━━━━━━━━━━\n")
        for resort in resorts_list[:8]:
            dist_str = f" ({resort['distance']:.0f} км)" if resort.get("distance") else ""
            lines.append(f"🏔️ <b>{resort['name']}</b>{dist_str}")
            lines.append(f"📞 <code>{resort['rescue_phone']}</code>\n")
    
    lines.append("\n⚠️ Нажми на номер, чтобы скопировать.")
    
    await query.message.answer("\n".join(lines), reply_markup=sos_back_kb())
    await query.answer()


# ═══════════════════════════════════════════════════════════════════
# ИНСТРУКТОРЫ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🎓 Инструкторы")
async def instructors_menu(message: Message, db: Database) -> None:
    cities = await db.get_instructor_cities()
    
    await message.answer(
        "🎓 <b>Инструкторы</b>\n\n"
        "Выбери город:",
        reply_markup=instructor_cities_kb(cities),
    )


@router.callback_query(F.data.startswith("instcity:"))
async def instructors_by_city(query: CallbackQuery, db: Database) -> None:
    city = query.data.split(":", 1)[1]
    instructors = await db.get_instructors_by_city(city)
    instructors_list = list(instructors)
    
    if not instructors_list:
        await query.answer("Инструкторы не найдены", show_alert=True)
        return
    
    lines = [f"🎓 <b>Инструкторы — {city}</b>\n"]
    for inst in instructors_list:
        link = inst["telegram_link"]
        if not link.startswith("@") and not link.startswith("http"):
            link = f"@{link}"
        lines.append(f"👤 <b>{inst['name']}</b> — {link}")
        lines.append(f"    🏔️ {inst['resorts']}\n")
    
    lines.append("\n━━━━━━━━━━━━━━━━━━━━")
    lines.append("🎿 <i>Хочешь попасть в раздел «Инструкторы»?</i>")
    lines.append("📩 Пиши @aleblanche")
    
    await query.message.answer("\n".join(lines), reply_markup=back_to_menu_kb())
    await query.answer()


# ═══════════════════════════════════════════════════════════════════
# АДМИН: ДОБАВЛЕНИЕ ИНСТРУКТОРА
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "/addinst")
async def admin_add_instructor(message: Message, state: FSMContext, db: Database) -> None:
    if message.from_user.id not in config.admin_ids:
        return
    
    await set_state(db, state, message.from_user.id, AddInstructorStates.waiting_name)
    await message.answer(
        "🎓 <b>Добавление инструктора</b>\n\n"
        "Введи <b>имя</b> инструктора:",
        reply_markup=BACK_KB,
    )


@router.message(AddInstructorStates.waiting_name)
async def admin_inst_name(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    await state.update_data(inst_name=message.text.strip())
    await set_state(db, state, message.from_user.id, AddInstructorStates.waiting_telegram)
    await message.answer("Введи <b>ссылку на Telegram</b> (например @username или https://t.me/username):")


@router.message(AddInstructorStates.waiting_telegram)
async def admin_inst_telegram(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    await state.update_data(inst_telegram=message.text.strip())
    await set_state(db, state, message.from_user.id, AddInstructorStates.waiting_city)
    await message.answer("Введи <b>город</b>:")


@router.message(AddInstructorStates.waiting_city)
async def admin_inst_city(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    await state.update_data(inst_city=message.text.strip())
    await set_state(db, state, message.from_user.id, AddInstructorStates.waiting_resorts)
    await message.answer("Введи <b>список склонов</b> через запятую:")


@router.message(AddInstructorStates.waiting_resorts)
async def admin_inst_resorts(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    data = await state.get_data()
    
    try:
        await db.add_instructor(
            name=data["inst_name"],
            telegram_link=data["inst_telegram"],
            city=data["inst_city"],
            resorts=message.text.strip(),
        )
        await set_state(db, state, message.from_user.id, None)
        await message.answer(
            f"✅ Инструктор добавлен!\n\n"
            f"👤 {data['inst_name']}\n"
            f"📍 {data['inst_city']}\n"
            f"🏔️ {message.text.strip()}",
            reply_markup=MAIN_MENU,
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=MAIN_MENU)


# ═══════════════════════════════════════════════════════════════════
# О БОТЕ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message) -> None:
    await message.answer(
        "🏔️ <b>Snow Crew</b>\n\n"
        "Твой помощник для катания:\n"
        "• 🧮 Калькулятор размера сноуборда и лыж\n"
        "• 🏔️ Поиск ближайших склонов (32+ курорта)\n"
        "• 🔍 Поиск компании для катания\n"
        "• 📅 Создание и календарь событий\n"
        "• 🎓 База инструкторов\n"
        "• 🆘 SOS — телефоны спасателей\n"
        "• 🔔 Напоминания о событиях\n"
        "• 👤 Личный профиль райдера\n\n"
        "Версия: 1.2",
        reply_markup=MAIN_MENU,
    )


# ═══════════════════════════════════════════════════════════════════
# ПОДДЕРЖКА РАЗРАБОТЧИКА
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text.in_(["💝 Поддержать разработчика", "💝 Поддержать"]))
async def donate(message: Message) -> None:
    await message.answer(
        "Привет! 👋\n\n"
        "Меня зовут <b>Александр</b>! Я разработал этот бот для того, "
        "чтобы вы смогли найти новых друзей по хобби, делиться опытом "
        "и планировать совместные путешествия!\n\n"
        "Буду очень рад получить вашу поддержку 💸",
        reply_markup=donate_kb(),
    )


# ═══════════════════════════════════════════════════════════════════
# FALLBACK
# ═══════════════════════════════════════════════════════════════════

@router.message()
async def fallback(message: Message) -> None:
    await message.answer("👇 Выбери действие из меню:", reply_markup=MAIN_MENU)


# ═══════════════════════════════════════════════════════════════════
# BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════════

async def reminder_checker(bot: Bot, db: Database) -> None:
    """Background task to check and send reminders."""
    while True:
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            reminders = await db.get_pending_reminders(current_time)
            
            for reminder in reminders:
                try:
                    await bot.send_message(
                        reminder["telegram_id"],
                        f"🔔 <b>Напоминание!</b>\n\n"
                        f"Завтра событие на {reminder['resort_name']}!\n"
                        f"📆 {reminder['event_date']}\n\n"
                        f"👥 Группа: {reminder['telegram_group_link']}",
                    )
                    await db.mark_reminder_sent(reminder["id"])
                except Exception:
                    pass
            
            # Cleanup old events
            cleaned = await db.cleanup_old_events()
            if cleaned > 0:
                print(f"Cleaned up {cleaned} old events")
                
        except Exception as e:
            print(f"Reminder checker error: {e}")
        
        await asyncio.sleep(3600)  # Check every hour


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

async def main() -> None:
    db = Database(config.database_path)
    await db.init()
    
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp["db"] = db
    dp["config"] = config
    dp.include_router(router)
    
    # Start background tasks
    asyncio.create_task(reminder_checker(bot, db))
    
    print("Snow Crew started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
