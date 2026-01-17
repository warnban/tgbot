"""Обработчики /start и навигации."""
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import BACK_KB, MAIN_MENU, profile_photo_kb
from states import ProfileStates

from .common import ensure_user, send_main_menu, set_state

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database) -> None:
    """Команда /start — приветствие или регистрация."""
    logger.info(f"cmd_start called for user {message.from_user.id}")
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    await set_state(db, state, message.from_user.id, None)
    
    logger.info(f"User {message.from_user.id} started bot, has_profile={profile is not None}")
    
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
    """Возврат в главное меню."""
    await set_state(db, state, message.from_user.id, None)
    await send_main_menu(message, "Главное меню")


@router.callback_query(F.data == "nav:menu")
async def cb_nav_menu(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Inline-кнопка возврата в меню."""
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer("Главное меню", reply_markup=MAIN_MENU)
    await query.answer()


@router.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message) -> None:
    """Информация о боте."""
    await message.answer(
        "Твой помощник для катания:\n\n"
        "• Калькулятор размера сноуборда\n"
        "• Поиск ближайших склонов (32+ курорта)\n"
        "• Поиск компании для катания\n"
        "• Создание и календарь событий\n"
        "• База инструкторов\n"
        "• SOS — телефоны спасателей\n"
        "• Анонимный чат до мэтча\n"
        "• Отзывы на курорты\n"
        "• Напоминания о событиях\n"
        "• Личный профиль райдера",
        reply_markup=MAIN_MENU,
    )


@router.message(F.text.in_(["💝 Поддержать разработчика", "💝 Поддержать"]))
async def donate(message: Message) -> None:
    """Поддержка разработчика."""
    from keyboards import donate_kb
    await message.answer(
        "Привет! 👋\n\n"
        "Меня зовут <b>Александр</b>! Я разработал этот бот для того, "
        "чтобы вы смогли найти новых друзей по хобби, делиться опытом "
        "и планировать совместные путешествия!\n\n"
        "Буду очень рад получить вашу поддержку 💸",
        reply_markup=donate_kb(),
    )


