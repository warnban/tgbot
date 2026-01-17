"""Калькулятор размера сноуборда."""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import BACK_KB, MAIN_MENU, gender_kb, snowboard_style_kb
from services.equipment import calculate_snowboard_size
from states import SnowboardCalcStates

from .common import ensure_user, set_state

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "📐 Размер сноуборда")
async def calc_start(message: Message, state: FSMContext, db: Database) -> None:
    """Начало расчёта размера сноуборда."""
    await ensure_user(db, message)
    await set_state(db, state, message.from_user.id, SnowboardCalcStates.waiting_gender)
    await message.answer("👤 Выбери <b>пол</b>:", reply_markup=gender_kb())


@router.callback_query(SnowboardCalcStates.waiting_gender, F.data.startswith("gender:"))
async def calc_gender(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Выбор пола."""
    gender = query.data.split(":")[1]
    await state.update_data(gender=gender)
    await set_state(db, state, query.from_user.id, SnowboardCalcStates.waiting_weight)
    await query.message.answer("⚖️ Введи свой <b>вес</b> в кг (например, 70):", reply_markup=BACK_KB)
    await query.answer()


@router.message(SnowboardCalcStates.waiting_weight)
async def calc_weight(message: Message, state: FSMContext, db: Database) -> None:
    """Ввод веса."""
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введи вес числом, например: 70")
        return
    weight = int(message.text)
    if weight < 30 or weight > 200:
        await message.answer("❌ Вес должен быть от 30 до 200 кг")
        return
    await state.update_data(weight=weight)
    await set_state(db, state, message.from_user.id, SnowboardCalcStates.waiting_style)
    await message.answer("🏔️ Выбери <b>стиль катания</b>:", reply_markup=snowboard_style_kb())


@router.callback_query(SnowboardCalcStates.waiting_style, F.data.startswith("style:"))
async def calc_style(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Результат расчёта."""
    style = query.data.split(":")[1]
    data = await state.get_data()
    
    size = calculate_snowboard_size(
        gender=data["gender"],
        weight_kg=data["weight"],
        style=style,
    )
    
    await set_state(db, state, query.from_user.id, None)
    
    await query.message.answer(
        f"🏂 <b>Рекомендуемый размер сноуборда:</b>\n\n"
        f"📐 <b>{size} см</b>",
        reply_markup=MAIN_MENU,
    )
    await query.answer()
    logger.info(f"User {query.from_user.id} calculated snowboard: {size} cm")
