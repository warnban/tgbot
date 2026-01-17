"""Калькулятор снаряжения."""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import (
    BACK_KB,
    MAIN_MENU,
    calc_type_kb,
    gender_kb,
    level_kb,
    ski_style_kb,
    snowboard_style_kb,
)
from services.equipment import calculate_ski_length, calculate_snowboard_length
from states import SkiCalcStates, SnowboardCalcStates

from .common import ensure_user, set_state

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🏂 Калькулятор")
async def calc_menu(message: Message, state: FSMContext, db: Database) -> None:
    """Меню калькулятора."""
    await ensure_user(db, message)
    await set_state(db, state, message.from_user.id, None)
    await message.answer(
        "🧮 <b>Калькулятор снаряжения</b>\n\nВыбери тип:",
        reply_markup=calc_type_kb(),
    )


# ═══════════════════════════════════════════════════════════════════
# СНОУБОРД
# ═══════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "calc:snowboard")
async def calc_snowboard_start(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Начало расчёта сноуборда."""
    await set_state(db, state, query.from_user.id, SnowboardCalcStates.waiting_height)
    await query.message.answer("📏 Введи свой <b>рост</b> в см (например, 175):", reply_markup=BACK_KB)
    await query.answer()


@router.message(SnowboardCalcStates.waiting_height)
async def calc_sb_height(message: Message, state: FSMContext, db: Database) -> None:
    """Ввод роста для сноуборда."""
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
    """Ввод веса для сноуборда."""
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
    """Выбор пола для сноуборда."""
    gender = query.data.split(":")[1]
    await state.update_data(gender=gender)
    await set_state(db, state, query.from_user.id, SnowboardCalcStates.waiting_shoe_size)
    await query.message.answer("👟 Введи <b>размер обуви</b> (EU, например 42):", reply_markup=BACK_KB)
    await query.answer()


@router.message(SnowboardCalcStates.waiting_shoe_size)
async def calc_sb_shoe_size(message: Message, state: FSMContext, db: Database) -> None:
    """Ввод размера обуви."""
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
    """Результат расчёта сноуборда."""
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
    logger.info(f"User {query.from_user.id} calculated snowboard: {size_str}")


# ═══════════════════════════════════════════════════════════════════
# ЛЫЖИ
# ═══════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "calc:ski")
async def calc_ski_start(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Начало расчёта лыж."""
    await set_state(db, state, query.from_user.id, SkiCalcStates.waiting_height)
    await query.message.answer("📏 Введи свой <b>рост</b> в см (например, 175):", reply_markup=BACK_KB)
    await query.answer()


@router.message(SkiCalcStates.waiting_height)
async def calc_ski_height(message: Message, state: FSMContext, db: Database) -> None:
    """Ввод роста для лыж."""
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
    """Ввод веса для лыж."""
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
    """Выбор уровня для лыж."""
    level = query.data.split(":")[1]
    await state.update_data(level=level)
    await set_state(db, state, query.from_user.id, SkiCalcStates.waiting_style)
    await query.message.answer("🏔️ Выбери <b>стиль катания</b>:", reply_markup=ski_style_kb())
    await query.answer()


@router.callback_query(SkiCalcStates.waiting_style, F.data.startswith("style:"))
async def calc_ski_style(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Результат расчёта лыж."""
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
    logger.info(f"User {query.from_user.id} calculated ski: {result.min_length}-{result.max_length}")
