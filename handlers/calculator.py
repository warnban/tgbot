"""Калькулятор размера сноуборда."""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import BACK_KB, MAIN_MENU, level_kb, snowboard_style_kb
from services.equipment import calculate_snowboard_size
from states import SnowboardCalcStates

from .common import ensure_user, set_state

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "📐 Размер сноуборда")
async def calc_start(message: Message, state: FSMContext, db: Database) -> None:
    """Начало расчёта размера сноуборда."""
    await ensure_user(db, message)
    await set_state(db, state, message.from_user.id, SnowboardCalcStates.waiting_height)
    await message.answer("📏 Введи свой <b>рост</b> в см (например, 175):", reply_markup=BACK_KB)


@router.message(SnowboardCalcStates.waiting_height)
async def calc_height(message: Message, state: FSMContext, db: Database) -> None:
    """Ввод роста."""
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
    await set_state(db, state, message.from_user.id, SnowboardCalcStates.waiting_level)
    await message.answer("📊 Выбери <b>уровень катания</b>:", reply_markup=level_kb())


@router.callback_query(SnowboardCalcStates.waiting_level, F.data.startswith("level:"))
async def calc_level(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Выбор уровня."""
    level = query.data.split(":")[1]
    await state.update_data(level=level)
    await set_state(db, state, query.from_user.id, SnowboardCalcStates.waiting_style)
    await query.message.answer("🏔️ Выбери <b>стиль катания</b>:", reply_markup=snowboard_style_kb())
    await query.answer()


@router.callback_query(SnowboardCalcStates.waiting_style, F.data.startswith("style:"))
async def calc_style(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Результат расчёта."""
    style = query.data.split(":")[1]
    data = await state.get_data()
    
    size = calculate_snowboard_size(
        height_cm=data["height"],
        weight_kg=data["weight"],
        level=data["level"],
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
