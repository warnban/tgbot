"""Отзывы на курорты."""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import BACK_KB, MAIN_MENU, back_to_menu_kb, review_rating_kb
from states import ReviewStates

from .common import ensure_user, set_state, truncate

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("review:"))
async def start_review(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Начать оставлять отзыв."""
    resort_id = int(query.data.split(":")[1])
    resort = await db.get_resort(resort_id)
    
    if not resort:
        await query.answer("Курорт не найден", show_alert=True)
        return
    
    user_id = await ensure_user(db, query)
    
    # Проверяем, не оставлял ли уже отзыв
    existing = await db.get_user_resort_review(user_id, resort_id)
    if existing:
        await query.answer("Ты уже оставлял отзыв на этот курорт", show_alert=True)
        return
    
    await state.update_data(review_resort_id=resort_id, review_resort_name=resort["name"])
    await set_state(db, state, query.from_user.id, ReviewStates.waiting_rating)
    await query.message.answer(
        f"⭐ <b>Отзыв на {resort['name']}</b>\n\n"
        "Выбери оценку:",
        reply_markup=review_rating_kb(),
    )
    await query.answer()


@router.callback_query(ReviewStates.waiting_rating, F.data.startswith("rating:"))
async def review_rating(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Получена оценка."""
    rating = int(query.data.split(":")[1])
    await state.update_data(review_rating=rating)
    await set_state(db, state, query.from_user.id, ReviewStates.waiting_text)
    await query.message.answer(
        f"⭐ Оценка: <b>{rating}/5</b>\n\n"
        "Напиши комментарий (или /skip чтобы пропустить):",
        reply_markup=BACK_KB,
    )
    await query.answer()


@router.message(ReviewStates.waiting_text, F.text == "/skip")
async def review_skip_text(message: Message, state: FSMContext, db: Database) -> None:
    """Пропустить текст отзыва."""
    await save_review(message, state, db, None)


@router.message(ReviewStates.waiting_text)
async def review_text(message: Message, state: FSMContext, db: Database) -> None:
    """Получен текст отзыва."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    await save_review(message, state, db, truncate(message.text.strip(), 500))


async def save_review(message: Message, state: FSMContext, db: Database, text: str | None) -> None:
    """Сохранить отзыв."""
    data = await state.get_data()
    user_id = await ensure_user(db, message)
    
    await db.add_review(
        user_id=user_id,
        resort_id=data["review_resort_id"],
        rating=data["review_rating"],
        text=text,
    )
    
    await set_state(db, state, message.from_user.id, None)
    await message.answer(
        f"✅ Спасибо за отзыв на <b>{data['review_resort_name']}</b>!",
        reply_markup=MAIN_MENU,
    )
    logger.info(f"User {message.from_user.id} reviewed resort {data['review_resort_id']}")


@router.callback_query(F.data.startswith("reviews:"))
async def show_reviews(query: CallbackQuery, db: Database) -> None:
    """Показать отзывы на курорт."""
    resort_id = int(query.data.split(":")[1])
    resort = await db.get_resort(resort_id)
    
    if not resort:
        await query.answer("Курорт не найден", show_alert=True)
        return
    
    reviews = await db.get_resort_reviews(resort_id, limit=10)
    reviews_list = list(reviews)
    
    if not reviews_list:
        await query.message.answer(
            f"😔 На <b>{resort['name']}</b> пока нет отзывов.\n\n"
            "Будь первым!",
            reply_markup=back_to_menu_kb(),
        )
        await query.answer()
        return
    
    rating = await db.get_resort_rating(resort_id)
    
    lines = [
        f"⭐ <b>Отзывы на {resort['name']}</b>",
        f"Средняя оценка: <b>{rating['avg']:.1f}/5</b> ({rating['count']} отзывов)\n",
    ]
    
    for review in reviews_list:
        stars = "⭐" * review["rating"]
        name = review["first_name"] or "Райдер"
        lines.append(f"<b>{name}</b> {stars}")
        if review.get("text"):
            lines.append(f"<i>{review['text']}</i>")
        lines.append("")
    
    await query.message.answer("\n".join(lines), reply_markup=back_to_menu_kb())
    await query.answer()
