"""Анонимный чат через бота."""
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import MAIN_MENU, back_to_menu_kb, chat_actions_kb
from states import ChatStates

from .common import ensure_user, set_state

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.regexp(r"^chat:\d+$"))
async def start_chat(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Начать анонимный чат."""
    target_user_id = int(query.data.split(":")[1])
    user_id = await ensure_user(db, query)
    
    if not user_id:
        await query.answer("Ошибка", show_alert=True)
        return
    
    # Проверяем, не заблокированы ли
    if await db.is_blocked(user_id, target_user_id):
        await query.answer("Этот пользователь недоступен", show_alert=True)
        return
    
    # Создаём или получаем чат
    chat_id = await db.get_or_create_chat(user_id, target_user_id)
    
    target_profile = await db.get_profile(target_user_id)
    target_name = target_profile["first_name"] if target_profile else "Райдер"
    
    await state.update_data(
        active_chat_id=chat_id,
        chat_partner_id=target_user_id,
        chat_partner_name=target_name,
    )
    await set_state(db, state, query.from_user.id, ChatStates.chatting)
    
    # Показываем последние сообщения
    messages = await db.get_chat_messages(chat_id, limit=10)
    
    lines = [f"💬 <b>Чат с {target_name}</b>\n"]
    
    if messages:
        for msg in reversed(list(messages)):
            sender = "Ты" if msg["sender_id"] == user_id else target_name
            lines.append(f"<b>{sender}:</b> {msg['text']}")
    else:
        lines.append("<i>Начни диалог первым!</i>")
    
    lines.append("\n📝 Напиши сообщение:")
    
    await query.message.answer("\n".join(lines), reply_markup=chat_actions_kb())
    await query.answer()


@router.message(ChatStates.chatting)
async def chat_message(message: Message, state: FSMContext, db: Database, bot: Bot) -> None:
    """Сообщение в чате."""
    if not message.text:
        return
    
    if message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Чат закрыт.", reply_markup=MAIN_MENU)
        return
    
    data = await state.get_data()
    chat_id = data.get("active_chat_id")
    partner_id = data.get("chat_partner_id")
    partner_name = data.get("chat_partner_name", "Райдер")
    
    if not chat_id or not partner_id:
        await set_state(db, state, message.from_user.id, None)
        await message.answer("❌ Ошибка чата. Попробуй снова.", reply_markup=MAIN_MENU)
        return
    
    user_id = await ensure_user(db, message)
    
    # Ограничиваем длину сообщения
    text = message.text[:1000]
    
    # Сохраняем сообщение
    await db.add_chat_message(chat_id, user_id, text)
    
    # Отправляем партнёру
    partner = await db.get_user_by_id(partner_id)
    if partner:
        my_profile = await db.get_profile(user_id)
        my_name = my_profile["first_name"] if my_profile else "Райдер"
        
        try:
            await bot.send_message(
                partner["telegram_id"],
                f"💬 <b>Сообщение от {my_name}:</b>\n\n{text}",
                reply_markup=back_to_menu_kb(),
            )
        except Exception:
            pass  # Партнёр заблокировал бота
    
    await message.answer(f"✅ Отправлено\n\n📝 Напиши ещё:", reply_markup=chat_actions_kb())


@router.callback_query(F.data == "chat:end")
async def end_chat(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Завершить чат."""
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer("💬 Чат завершён.", reply_markup=MAIN_MENU)
    await query.answer()
