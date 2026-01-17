"""Fallback обработчик — должен быть зарегистрирован последним."""
from aiogram import Router
from aiogram.types import Message

from keyboards import MAIN_MENU

router = Router()


@router.message()
async def fallback(message: Message) -> None:
    """Обработчик неизвестных сообщений."""
    await message.answer("👇 Выбери действие из меню:", reply_markup=MAIN_MENU)
