"""Инструкторы."""
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import back_to_menu_kb, instructor_cities_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🎓 Инструкторы")
async def instructors_menu(message: Message, db: Database) -> None:
    """Меню инструкторов."""
    cities = await db.get_instructor_cities()
    
    await message.answer(
        "🎓 <b>Инструкторы</b>\n\n"
        "Выбери город:",
        reply_markup=instructor_cities_kb(cities),
    )


@router.callback_query(F.data.startswith("instcity:"))
async def instructors_by_city(query: CallbackQuery, db: Database) -> None:
    """Инструкторы в городе."""
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
