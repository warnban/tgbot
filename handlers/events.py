"""Обработчики событий."""
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import (
    BACK_KB,
    MAIN_MENU,
    event_confirm_kb,
    event_level_kb,
    event_photo_kb,
    event_resorts_kb,
    event_view_kb,
    events_calendar_kb,
    events_list_kb,
    my_event_actions_kb,
    my_events_kb,
)
from states import EventStates

from .common import ensure_user, set_state, truncate

logger = logging.getLogger(__name__)
router = Router()


# ═══════════════════════════════════════════════════════════════════
# СОЗДАНИЕ СОБЫТИЯ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "📅 Создать событие")
async def event_create_start(message: Message, state: FSMContext, db: Database) -> None:
    """Начало создания события."""
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    if not profile:
        await message.answer(
            "❌ Сначала создай профиль в разделе «👤 Профиль»",
            reply_markup=MAIN_MENU,
        )
        return
    
    await set_state(db, state, message.from_user.id, EventStates.waiting_group_link)
    await message.answer(
        "📅 <b>Создание события</b>\n\n"
        "Событие — это групповой выезд на курорт.\n\n"
        "<b>Инструкция:</b>\n"
        "1️⃣ Создай группу в Telegram для участников\n"
        "2️⃣ Сделай её публичной или получи ссылку-приглашение\n"
        "3️⃣ Скопируй ссылку на группу (например: https://t.me/+ABC123)\n\n"
        "📎 <b>Пришли ссылку на группу:</b>",
        reply_markup=BACK_KB,
    )


@router.message(EventStates.waiting_group_link)
async def event_got_group_link(message: Message, state: FSMContext, db: Database) -> None:
    """Получена ссылка на группу."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    link = message.text.strip()
    if not (link.startswith("https://t.me/") or link.startswith("t.me/")):
        await message.answer("❌ Пришли корректную ссылку на Telegram-группу (начинается с https://t.me/)")
        return
    
    await state.update_data(telegram_group_link=link)
    await set_state(db, state, message.from_user.id, EventStates.waiting_photo)
    await message.answer(
        "📸 Пришли фото/обложку события (необязательно):",
        reply_markup=event_photo_kb(),
    )


@router.callback_query(EventStates.waiting_photo, F.data == "event:skip_photo")
async def event_skip_photo(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Пропустить фото события."""
    await state.update_data(photo_file_id=None)
    await set_state(db, state, query.from_user.id, EventStates.waiting_resort)
    
    resorts = await db.list_resorts()
    await query.message.answer(
        "🏔️ Выбери курорт:",
        reply_markup=event_resorts_kb(list(resorts)),
    )
    await query.answer()


@router.message(EventStates.waiting_photo, F.photo)
async def event_got_photo(message: Message, state: FSMContext, db: Database) -> None:
    """Получено фото события."""
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await set_state(db, state, message.from_user.id, EventStates.waiting_resort)
    
    resorts = await db.list_resorts()
    await message.answer(
        "🏔️ Выбери курорт:",
        reply_markup=event_resorts_kb(list(resorts)),
    )


@router.message(EventStates.waiting_photo)
async def event_photo_invalid(message: Message) -> None:
    """Неверный формат — ожидалось фото."""
    await message.answer("📸 Пришли фото или нажми «Пропустить».")


@router.callback_query(EventStates.waiting_resort, F.data.startswith("evresort:"))
async def event_got_resort(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Выбран курорт."""
    resort_id = int(query.data.split(":")[1])
    resort = await db.get_resort(resort_id)
    
    await state.update_data(resort_id=resort_id, resort_name=resort["name"])
    await set_state(db, state, query.from_user.id, EventStates.waiting_date)
    await query.message.answer(
        f"📆 Курорт: <b>{resort['name']}</b>\n\n"
        "Введи дату события (например: 25.01.2026 или 25-28 января):",
        reply_markup=BACK_KB,
    )
    await query.answer()


@router.message(EventStates.waiting_date)
async def event_got_date(message: Message, state: FSMContext, db: Database) -> None:
    """Получена дата события."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    await state.update_data(event_date=message.text.strip()[:50])
    await set_state(db, state, message.from_user.id, EventStates.waiting_level)
    await message.answer(
        "🎿 Выбери уровень участников:",
        reply_markup=event_level_kb(),
    )


@router.callback_query(EventStates.waiting_level, F.data.startswith("evlevel:"))
async def event_got_level(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Выбран уровень."""
    level = query.data.split(":")[1]
    await state.update_data(skill_level=level)
    await set_state(db, state, query.from_user.id, EventStates.waiting_description)
    await query.message.answer(
        "💬 Добавь описание события (необязательно):\n\n"
        "Например: «Фрирайд по целине, нужен свой транспорт»\n\n"
        "Или нажми /skip чтобы пропустить.",
        reply_markup=BACK_KB,
    )
    await query.answer()


@router.message(EventStates.waiting_description, F.text == "/skip")
async def event_skip_description(message: Message, state: FSMContext, db: Database) -> None:
    """Пропустить описание."""
    await state.update_data(description=None)
    await show_event_preview(message, state, db)


@router.message(EventStates.waiting_description)
async def event_got_description(message: Message, state: FSMContext, db: Database) -> None:
    """Получено описание события."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    await state.update_data(description=truncate(message.text.strip(), 500))
    await show_event_preview(message, state, db)


async def show_event_preview(message: Message, state: FSMContext, db: Database) -> None:
    """Показать превью события."""
    data = await state.get_data()
    
    level_icons = {"Новичок": "🟢", "Средний": "🔵", "Продвинутый": "🔴", "Любой": "⚪"}
    level_icon = level_icons.get(data["skill_level"], "⚪")
    
    text = (
        "📅 <b>Предпросмотр события</b>\n\n"
        f"🏔️ {data['resort_name']}\n"
        f"📆 {data['event_date']}\n"
        f"{level_icon} Уровень: {data['skill_level']}\n"
    )
    if data.get("description"):
        text += f"💬 {data['description']}\n"
    text += f"\n🔗 Группа: {data['telegram_group_link']}"
    
    if data.get("photo_file_id"):
        await message.answer_photo(data["photo_file_id"], caption=text, reply_markup=event_confirm_kb())
    else:
        await message.answer(text, reply_markup=event_confirm_kb())


@router.callback_query(F.data == "event:confirm")
async def event_confirm(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Подтверждение создания события."""
    data = await state.get_data()
    user_id = await ensure_user(db, query)
    
    event_id = await db.create_event(
        creator_id=user_id,
        resort_id=data["resort_id"],
        event_date=data["event_date"],
        skill_level=data["skill_level"],
        telegram_group_link=data["telegram_group_link"],
        photo_file_id=data.get("photo_file_id"),
        description=data.get("description"),
    )
    
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer(
        f"✅ Событие создано!\n\n"
        f"Теперь оно будет показываться в поиске компании.\n"
        f"Райдеры смогут присоединиться к твоей группе.",
        reply_markup=MAIN_MENU,
    )
    await query.answer()
    logger.info(f"User {query.from_user.id} created event {event_id}")


# ═══════════════════════════════════════════════════════════════════
# МОИ СОБЫТИЯ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🗓️ Мои события")
async def my_events_menu(message: Message, state: FSMContext, db: Database) -> None:
    """Список событий пользователя."""
    user_id = await ensure_user(db, message)
    events = await db.get_user_events(user_id)
    events_list = list(events)
    
    if not events_list:
        await message.answer(
            "📭 У тебя пока нет созданных событий.\n\n"
            "Создай событие, чтобы собрать компанию на катание!",
            reply_markup=my_events_kb([]),
        )
        return
    
    await message.answer(
        f"🗓️ <b>Твои события</b> ({len(events_list)})",
        reply_markup=my_events_kb(events_list),
    )


@router.callback_query(F.data == "nav:my_events")
async def cb_my_events(query: CallbackQuery, db: Database) -> None:
    """Inline-возврат к списку событий."""
    user_id = await ensure_user(db, query)
    events = await db.get_user_events(user_id)
    events_list = list(events)
    
    await query.message.answer(
        f"🗓️ <b>Твои события</b> ({len(events_list)})" if events_list else "📭 У тебя пока нет событий.",
        reply_markup=my_events_kb(events_list),
    )
    await query.answer()


@router.callback_query(F.data == "nav:create_event")
async def cb_create_event(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Создание события через inline."""
    user_id = await ensure_user(db, query)
    profile = await db.get_profile(user_id)
    
    if not profile:
        await query.message.answer("❌ Сначала создай профиль в разделе «👤 Профиль»", reply_markup=MAIN_MENU)
        await query.answer()
        return
    
    await set_state(db, state, query.from_user.id, EventStates.waiting_group_link)
    await query.message.answer(
        "📅 <b>Создание события</b>\n\n"
        "📎 <b>Пришли ссылку на Telegram-группу:</b>",
        reply_markup=BACK_KB,
    )
    await query.answer()


@router.callback_query(F.data.startswith("myevent:"))
async def my_event_details(query: CallbackQuery, db: Database) -> None:
    """Детали события пользователя."""
    event_id = int(query.data.split(":")[1])
    event = await db.get_event(event_id)
    
    if not event:
        await query.answer("Событие не найдено", show_alert=True)
        return
    
    level_icons = {"Новичок": "🟢", "Средний": "🔵", "Продвинутый": "🔴", "Любой": "⚪"}
    level_icon = level_icons.get(event["skill_level"], "⚪")
    
    text = (
        f"📅 <b>Твоё событие</b>\n\n"
        f"🏔️ {event['resort_name']}\n"
        f"📆 {event['event_date']}\n"
        f"{level_icon} Уровень: {event['skill_level']}\n"
        f"🔗 {event['telegram_group_link']}"
    )
    if event.get("description"):
        text += f"\n💬 {event['description']}"
    
    await query.message.answer(text, reply_markup=my_event_actions_kb(event_id))
    await query.answer()


@router.callback_query(F.data.startswith("delevent:"))
async def delete_my_event(query: CallbackQuery, db: Database) -> None:
    """Удаление события."""
    event_id = int(query.data.split(":")[1])
    await db.deactivate_event(event_id)
    await query.message.answer("🗑️ Событие удалено.", reply_markup=MAIN_MENU)
    await query.answer()
    logger.info(f"User {query.from_user.id} deleted event {event_id}")


# ═══════════════════════════════════════════════════════════════════
# КАЛЕНДАРЬ СОБЫТИЙ
# ═══════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "nav:calendar")
async def cb_calendar(query: CallbackQuery) -> None:
    """Календарь событий."""
    await query.message.answer(
        "📆 <b>Календарь событий</b>\n\n"
        "Выбери период:",
        reply_markup=events_calendar_kb(),
    )
    await query.answer()


@router.callback_query(F.data.startswith("calendar:"))
async def cb_calendar_filter(query: CallbackQuery, db: Database) -> None:
    """Фильтр календаря."""
    period = query.data.split(":")[1]
    events = await db.get_active_events()
    events_list = list(events)
    
    if period == "week":
        title = "на этой неделе"
    elif period == "month":
        title = "в этом месяце"
    else:
        title = "все"
    
    filtered = events_list if period == "all" else events_list[:10]
    
    if not filtered:
        await query.message.answer(
            "😔 Событий пока нет.\n\nСоздай своё!",
            reply_markup=events_calendar_kb(),
        )
    else:
        await query.message.answer(
            f"📆 <b>События {title}</b> ({len(filtered)})",
            reply_markup=events_list_kb(filtered),
        )
    await query.answer()


@router.callback_query(F.data.startswith("viewevent:"))
async def view_event(query: CallbackQuery, db: Database) -> None:
    """Просмотр события."""
    event_id = int(query.data.split(":")[1])
    event = await db.get_event(event_id)
    
    if not event:
        await query.answer("Событие не найдено", show_alert=True)
        return
    
    level_icons = {"Новичок": "🟢", "Средний": "🔵", "Продвинутый": "🔴", "Любой": "⚪"}
    level_icon = level_icons.get(event["skill_level"], "⚪")
    
    text = (
        f"📅 <b>Событие</b>\n\n"
        f"🏔️ {event['resort_name']}\n"
        f"📆 {event['event_date']}\n"
        f"{level_icon} Уровень: {event['skill_level']}\n"
        f"👤 Организатор: {event['creator_name']}"
    )
    if event.get("description"):
        text += f"\n\n💬 {event['description']}"
    
    await query.message.answer(
        text,
        reply_markup=event_view_kb(event_id, event["telegram_group_link"]),
    )
    await query.answer()


@router.callback_query(F.data.startswith("remind:"))
async def set_reminder(query: CallbackQuery, db: Database) -> None:
    """Установить напоминание."""
    event_id = int(query.data.split(":")[1])
    user_id = await ensure_user(db, query)
    event = await db.get_event(event_id)
    
    if not event:
        await query.answer("Событие не найдено", show_alert=True)
        return
    
    remind_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    try:
        await db.add_event_reminder(user_id, event_id, remind_at)
        await query.answer("🔔 Напоминание установлено!", show_alert=True)
    except Exception:
        await query.answer("⚠️ Напоминание уже установлено", show_alert=True)
