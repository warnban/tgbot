"""Обработчики склонов."""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import load_config
from db import Database
from keyboards import (
    LOCATION_KB,
    MAIN_MENU,
    cities_list_kb,
    city_resorts_kb,
    resort_back_kb,
    resort_detail_kb,
    resorts_list_kb,
)
from services.resorts import haversine_km, sort_by_distance
from services.weather import format_weather, get_weather
from states import ResortStates

from .common import ensure_user, set_state

logger = logging.getLogger(__name__)
router = Router()
config = load_config()


@router.message(F.text == "🏔️ Склоны")
async def resorts_menu(message: Message, state: FSMContext, db: Database) -> None:
    """Меню склонов."""
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
    """Получена геолокация для склонов."""
    loc = message.location
    user_id = await ensure_user(db, message)
    
    profile = await db.get_profile(user_id)
    if profile:
        await db.update_profile_location(user_id, loc.latitude, loc.longitude)
    
    await state.update_data(user_lat=loc.latitude, user_lon=loc.longitude)
    await show_resorts(message, state, db, loc.latitude, loc.longitude)


async def show_resorts(message: Message, state: FSMContext, db: Database, lat: float, lon: float) -> None:
    """Показать ближайшие склоны."""
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
    """Возврат к списку склонов."""
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
    """Неверный формат — ожидалась геолокация."""
    await message.answer("❌ Отправь геолокацию через кнопку ниже.")


@router.callback_query(F.data == "resorts:cities")
async def cb_resorts_cities(query: CallbackQuery, db: Database) -> None:
    """Список городов с курортами."""
    cities = await db.get_resort_cities()
    await query.message.answer(
        "🌍 <b>Выбери регион:</b>",
        reply_markup=cities_list_kb(cities),
    )
    await query.answer()


@router.callback_query(F.data.startswith("city:"))
async def cb_city_resorts(query: CallbackQuery, db: Database) -> None:
    """Склоны в выбранном городе."""
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
    """Детали склона."""
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
    
    # Рейтинг
    rating = await db.get_resort_rating(resort_id)
    rating_str = f"⭐ <b>{rating['avg']:.1f}</b> ({rating['count']} отзывов)" if rating["count"] > 0 else "⭐ Нет отзывов"
    
    text = (
        f"🏔️ <b>{resort['name']}</b>\n\n"
        f"📍 {resort['address'] or '—'}{dist_str}\n"
        f"🎿 Трасс: <b>{resort['trails_count'] or '—'}</b>\n"
        f"🎚️ Уровни: {resort['trail_levels'] or '—'}\n"
        f"🚡 Подъёмников: <b>{resort['lifts_count'] or '—'}</b>\n"
        f"🌐 {site_str}\n"
        f"{rating_str}"
        f"{weather_str}"
    )
    await query.message.answer(text, reply_markup=resort_detail_kb(resort_id), disable_web_page_preview=True)
    await query.answer()
