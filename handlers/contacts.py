"""Контакты (мэтчи)."""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import MAIN_MENU, contacts_kb

from .common import ensure_user

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🤝 Контакты")
async def contacts_menu(message: Message, state: FSMContext, db: Database) -> None:
    """Список контактов (мэтчей)."""
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
