"""Админские команды."""
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import load_config
from db import Database
from keyboards import BACK_KB, MAIN_MENU
from states import AddInstructorStates, BroadcastStates

from .common import set_state

logger = logging.getLogger(__name__)
router = Router()
config = load_config()


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database) -> None:
    """Статистика бота (только для админов)."""
    if message.from_user.id not in config.admin_ids:
        return
    
    stats = await db.get_stats()
    await message.answer(
        "📊 <b>Статистика Snow Crew</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"👤 Профилей: <b>{stats['profiles']}</b>\n"
        f"❤️ Лайков: <b>{stats['likes']}</b>\n"
        f"🤝 Мэтчей: <b>{stats['matches']}</b>\n"
        f"📅 Событий: <b>{stats['events']}</b>\n"
        f"⭐ Отзывов: <b>{stats['reviews']}</b>\n"
        f"🚫 Блокировок: <b>{stats['blocks']}</b>",
        reply_markup=MAIN_MENU,
    )


@router.message(Command("addinst"))
async def admin_add_instructor(message: Message, state: FSMContext, db: Database) -> None:
    """Добавление инструктора (только для админов)."""
    if message.from_user.id not in config.admin_ids:
        return
    
    await set_state(db, state, message.from_user.id, AddInstructorStates.waiting_name)
    await message.answer(
        "🎓 <b>Добавление инструктора</b>\n\n"
        "Введи <b>имя</b> инструктора:",
        reply_markup=BACK_KB,
    )


@router.message(AddInstructorStates.waiting_name)
async def admin_inst_name(message: Message, state: FSMContext, db: Database) -> None:
    """Имя инструктора."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    await state.update_data(inst_name=message.text.strip())
    await set_state(db, state, message.from_user.id, AddInstructorStates.waiting_telegram)
    await message.answer("Введи <b>ссылку на Telegram</b> (например @username или https://t.me/username):")


@router.message(AddInstructorStates.waiting_telegram)
async def admin_inst_telegram(message: Message, state: FSMContext, db: Database) -> None:
    """Telegram инструктора."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    await state.update_data(inst_telegram=message.text.strip())
    await set_state(db, state, message.from_user.id, AddInstructorStates.waiting_city)
    await message.answer("Введи <b>город</b>:")


@router.message(AddInstructorStates.waiting_city)
async def admin_inst_city(message: Message, state: FSMContext, db: Database) -> None:
    """Город инструктора."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    await state.update_data(inst_city=message.text.strip())
    await set_state(db, state, message.from_user.id, AddInstructorStates.waiting_resorts)
    await message.answer("Введи <b>список склонов</b> через запятую:")


@router.message(AddInstructorStates.waiting_resorts)
async def admin_inst_resorts(message: Message, state: FSMContext, db: Database) -> None:
    """Склоны инструктора."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    data = await state.get_data()
    
    try:
        await db.add_instructor(
            name=data["inst_name"],
            telegram_link=data["inst_telegram"],
            city=data["inst_city"],
            resorts=message.text.strip(),
        )
        await set_state(db, state, message.from_user.id, None)
        await message.answer(
            f"✅ Инструктор добавлен!\n\n"
            f"👤 {data['inst_name']}\n"
            f"📍 {data['inst_city']}\n"
            f"🏔️ {message.text.strip()}",
            reply_markup=MAIN_MENU,
        )
        logger.info(f"Admin {message.from_user.id} added instructor {data['inst_name']}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=MAIN_MENU)


@router.message(Command("broadcast"))
async def admin_broadcast_start(message: Message, state: FSMContext, db: Database) -> None:
    """Рассылка (только для админов)."""
    if message.from_user.id not in config.admin_ids:
        return
    
    await set_state(db, state, message.from_user.id, BroadcastStates.waiting_message)
    await message.answer(
        "📢 <b>Рассылка</b>\n\n"
        "Напиши сообщение для всех пользователей:",
        reply_markup=BACK_KB,
    )


@router.message(BroadcastStates.waiting_message, F.text)
async def admin_broadcast_send(message: Message, state: FSMContext, db: Database) -> None:
    """Отправка рассылки."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    from aiogram import Bot
    bot: Bot = message.bot
    
    users = await db.get_all_users()
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await bot.send_message(user["telegram_id"], message.text)
            sent += 1
        except Exception:
            failed += 1
    
    await set_state(db, state, message.from_user.id, None)
    await message.answer(
        f"📢 Рассылка завершена\n\n"
        f"✅ Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}",
        reply_markup=MAIN_MENU,
    )
    logger.info(f"Admin {message.from_user.id} sent broadcast: {sent} sent, {failed} failed")
