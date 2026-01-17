"""SOS — экстренная помощь."""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import sos_back_kb
from services.resorts import haversine_km

from .common import ensure_user

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🆘 SOS")
async def sos_menu(message: Message, state: FSMContext, db: Database) -> None:
    """SOS — телефоны спасателей."""
    user_id = await ensure_user(db, message)
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
    
    geo_hint = ""
    if not user_lat:
        geo_hint = "\n💡 <i>Обнови геолокацию в профиле для показа ближайших курортов.</i>"
    
    lines.append(f"\n⚠️ Нажми на номер, чтобы скопировать.{geo_hint}")
    
    await message.answer("\n".join(lines), reply_markup=sos_back_kb())


@router.callback_query(F.data == "nav:sos")
async def cb_sos(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """SOS через inline."""
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
