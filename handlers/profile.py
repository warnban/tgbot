"""Обработчики профиля."""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import (
    BACK_KB,
    LOCATION_KB,
    MAIN_MENU,
    profile_actions_kb,
    profile_edit_kb,
    profile_gender_kb,
    profile_level_kb,
    profile_more_photos_kb,
    profile_photo_kb,
    ride_type_kb,
)
from services.resorts import haversine_km
from states import ProfileStates, EditProfileStates, EditDescriptionStates

from .common import (
    ensure_user,
    format_profile,
    send_profile_with_photos,
    set_state,
    truncate,
)

logger = logging.getLogger(__name__)
router = Router()


# ═══════════════════════════════════════════════════════════════════
# ПРОСМОТР ПРОФИЛЯ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "👤 Профиль")
async def profile_menu(message: Message, state: FSMContext, db: Database) -> None:
    """Показать профиль или начать регистрацию."""
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    if profile:
        profile_dict = dict(profile)
        text = format_profile(profile_dict)
        await send_profile_with_photos(message, profile_dict, text, profile_actions_kb())
        return
    
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_photos)
    await state.update_data(photos=[])
    await message.answer(
        "📸 Пришли фото для профиля (можно несколько) или пропусти.",
        reply_markup=BACK_KB,
    )
    await message.answer("👇", reply_markup=profile_photo_kb())


# ═══════════════════════════════════════════════════════════════════
# СОЗДАНИЕ ПРОФИЛЯ
# ═══════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "profile:skip_photo")
async def profile_skip_photo(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Пропустить добавление фото."""
    await state.update_data(photos=[])
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_gender)
    await query.message.answer("👤 Выбери <b>пол</b>:", reply_markup=profile_gender_kb())
    await query.answer()


@router.message(ProfileStates.waiting_photos, F.photo)
async def profile_got_photo(message: Message, state: FSMContext, db: Database) -> None:
    """Получено фото профиля."""
    photo = message.photo[-1]
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(photo.file_id)
    await state.update_data(photos=photos)
    
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_more_photos)
    await message.answer(
        f"✅ Фото добавлено ({len(photos)}/10)\n\nДобавить ещё или продолжить?",
        reply_markup=profile_more_photos_kb(),
    )


@router.message(ProfileStates.waiting_photos)
async def profile_photo_invalid(message: Message) -> None:
    """Неверный формат — ожидалось фото."""
    await message.answer("📸 Пришли фото или нажми «Пропустить».")


@router.message(ProfileStates.waiting_more_photos, F.photo)
async def profile_more_photo(message: Message, state: FSMContext, db: Database) -> None:
    """Добавление дополнительных фото."""
    photo = message.photo[-1]
    data = await state.get_data()
    photos = data.get("photos", [])
    
    if len(photos) >= 10:
        await message.answer("❌ Максимум 10 фото. Нажми «Готово».")
        return
    
    photos.append(photo.file_id)
    await state.update_data(photos=photos)
    
    await message.answer(
        f"✅ Фото добавлено ({len(photos)}/10)\n\nДобавить ещё или продолжить?",
        reply_markup=profile_more_photos_kb(),
    )


@router.callback_query(F.data == "profile:more_photos")
async def profile_want_more(query: CallbackQuery) -> None:
    """Пользователь хочет добавить ещё фото."""
    await query.message.answer("📸 Пришли ещё фото:")
    await query.answer()


@router.callback_query(F.data == "profile:photos_done")
async def profile_photos_done(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Фото добавлены, переход к выбору пола."""
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_gender)
    await query.message.answer("👤 Выбери <b>пол</b>:", reply_markup=profile_gender_kb())
    await query.answer()


@router.callback_query(ProfileStates.waiting_gender, F.data.startswith("pgender:"))
async def profile_gender(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Выбор пола."""
    gender = query.data.split(":")[1]
    await state.update_data(gender=gender)
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_ride_type)
    await query.message.answer("🎿 Выбери тип катания:", reply_markup=ride_type_kb())
    await query.answer()


@router.callback_query(ProfileStates.waiting_ride_type, F.data.startswith("ride:"))
async def profile_ride_type(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Выбор типа катания."""
    ride_type = query.data.split(":", 1)[1]
    await state.update_data(ride_type=ride_type)
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_skill_level)
    await query.message.answer("📊 Выбери уровень:", reply_markup=profile_level_kb())
    await query.answer()


@router.callback_query(ProfileStates.waiting_skill_level, F.data.startswith("plevel:"))
async def profile_skill_level(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Выбор уровня катания."""
    level = query.data.split(":")[1]
    await state.update_data(skill_level=level)
    await set_state(db, state, query.from_user.id, ProfileStates.waiting_age)
    await query.message.answer("🎂 Введи свой возраст:", reply_markup=BACK_KB)
    await query.answer()


@router.message(ProfileStates.waiting_age)
async def profile_age(message: Message, state: FSMContext, db: Database) -> None:
    """Ввод возраста."""
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введи возраст числом.")
        return
    age = int(message.text)
    if age < 12 or age > 80:
        await message.answer("❌ Возраст должен быть от 12 до 80 лет.")
        return
    await state.update_data(age=age)
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_city)
    await message.answer(
        "📍 Введи <b>город</b> или отправь геолокацию:",
        reply_markup=LOCATION_KB,
    )


@router.message(ProfileStates.waiting_city, F.location)
async def profile_city_location(message: Message, state: FSMContext, db: Database) -> None:
    """Город через геолокацию."""
    loc = message.location
    resorts = await db.list_resorts()
    nearest = min(resorts, key=lambda r: haversine_km(loc.latitude, loc.longitude, r["lat"], r["lon"]))
    city = nearest["address"] if nearest else "Неизвестно"
    
    await state.update_data(city=city, location_lat=loc.latitude, location_lon=loc.longitude)
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_about)
    await message.answer(
        f"📍 Определено: <b>{city}</b>\n\n💬 Напиши пару слов о себе:",
        reply_markup=BACK_KB,
    )


@router.message(ProfileStates.waiting_city, F.text)
async def profile_city_text(message: Message, state: FSMContext, db: Database) -> None:
    """Город текстом."""
    if not message.text or message.text == "◀️ Назад":
        return
    await state.update_data(city=message.text.strip()[:100], location_lat=None, location_lon=None)
    await set_state(db, state, message.from_user.id, ProfileStates.waiting_about)
    await message.answer("💬 Напиши пару слов о себе:", reply_markup=BACK_KB)


@router.message(ProfileStates.waiting_about)
async def profile_about(message: Message, state: FSMContext, db: Database) -> None:
    """Описание профиля — финальный шаг."""
    if not message.text or message.text == "◀️ Назад":
        return
    
    data = await state.get_data()
    user_id = await ensure_user(db, message)
    
    await db.upsert_profile(
        user_id=user_id,
        ride_type=data["ride_type"],
        skill_level=data["skill_level"],
        age=data["age"],
        city=data["city"],
        about=truncate(message.text.strip(), 500),
        photos=data.get("photos", []),
        gender=data.get("gender", ""),
        location_lat=data.get("location_lat"),
        location_lon=data.get("location_lon"),
    )
    
    await set_state(db, state, message.from_user.id, None)
    
    profile = await db.get_profile(user_id)
    profile_dict = dict(profile)
    text = f"✅ Профиль сохранён!\n\n{format_profile(profile_dict)}"
    
    await send_profile_with_photos(message, profile_dict, text, profile_actions_kb())
    logger.info(f"User {message.from_user.id} created profile")


# ═══════════════════════════════════════════════════════════════════
# РЕДАКТИРОВАНИЕ ПРОФИЛЯ
# ═══════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "profile:edit")
async def profile_edit_menu(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Меню редактирования профиля."""
    await query.message.answer(
        "✏️ <b>Что хочешь изменить?</b>",
        reply_markup=profile_edit_kb(),
    )
    await query.answer()


@router.callback_query(F.data == "profile:edit_photos")
async def profile_edit_photos(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Редактирование фото."""
    await set_state(db, state, query.from_user.id, EditProfileStates.waiting_photos)
    await state.update_data(photos=[], edit_mode=True)
    await query.message.answer("📸 Пришли новые фото:", reply_markup=BACK_KB)
    await query.message.answer("👇", reply_markup=profile_photo_kb())
    await query.answer()


@router.callback_query(F.data == "profile:edit_city")
async def profile_edit_city(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Редактирование города."""
    await set_state(db, state, query.from_user.id, EditProfileStates.waiting_city)
    await query.message.answer(
        "📍 Введи новый <b>город</b> или отправь геолокацию:",
        reply_markup=LOCATION_KB,
    )
    await query.answer()


@router.callback_query(F.data == "profile:edit_about")
async def profile_edit_about(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Редактирование описания."""
    await set_state(db, state, query.from_user.id, EditProfileStates.waiting_about)
    await query.message.answer("💬 Напиши новое описание:", reply_markup=BACK_KB)
    await query.answer()


@router.callback_query(F.data == "profile:edit_level")
async def profile_edit_level(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Редактирование уровня."""
    await set_state(db, state, query.from_user.id, EditProfileStates.waiting_level)
    await query.message.answer("📊 Выбери новый уровень:", reply_markup=profile_level_kb())
    await query.answer()


@router.callback_query(F.data == "profile:edit_ride")
async def profile_edit_ride(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Редактирование типа катания."""
    await set_state(db, state, query.from_user.id, EditProfileStates.waiting_ride)
    await query.message.answer("🎿 Выбери тип катания:", reply_markup=ride_type_kb())
    await query.answer()


# Обработчики для EditProfileStates
@router.message(EditProfileStates.waiting_photos, F.photo)
async def edit_profile_photo(message: Message, state: FSMContext, db: Database) -> None:
    """Новое фото при редактировании."""
    photo = message.photo[-1]
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(photo.file_id)
    await state.update_data(photos=photos)
    
    await message.answer(
        f"✅ Фото добавлено ({len(photos)}/10)\n\nДобавить ещё или сохранить?",
        reply_markup=profile_more_photos_kb(),
    )


@router.callback_query(EditProfileStates.waiting_photos, F.data == "profile:photos_done")
async def edit_profile_photos_done(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Сохранение новых фото."""
    data = await state.get_data()
    user_id = await ensure_user(db, query)
    
    await db.update_profile_photos(user_id, data.get("photos", []))
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer("✅ Фото обновлены!", reply_markup=MAIN_MENU)
    await query.answer()


@router.message(EditProfileStates.waiting_city, F.location)
async def edit_profile_city_location(message: Message, state: FSMContext, db: Database) -> None:
    """Обновление города через геолокацию."""
    loc = message.location
    resorts = await db.list_resorts()
    nearest = min(resorts, key=lambda r: haversine_km(loc.latitude, loc.longitude, r["lat"], r["lon"]))
    city = nearest["address"] if nearest else "Неизвестно"
    
    user_id = await ensure_user(db, message)
    await db.update_profile_city(user_id, city, loc.latitude, loc.longitude)
    await set_state(db, state, message.from_user.id, None)
    await message.answer(f"✅ Город обновлён: <b>{city}</b>", reply_markup=MAIN_MENU)


@router.message(EditProfileStates.waiting_city, F.text)
async def edit_profile_city_text(message: Message, state: FSMContext, db: Database) -> None:
    """Обновление города текстом."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    user_id = await ensure_user(db, message)
    await db.update_profile_city(user_id, message.text.strip()[:100], None, None)
    await set_state(db, state, message.from_user.id, None)
    await message.answer("✅ Город обновлён!", reply_markup=MAIN_MENU)


@router.message(EditProfileStates.waiting_about)
async def edit_profile_about(message: Message, state: FSMContext, db: Database) -> None:
    """Обновление описания."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    user_id = await ensure_user(db, message)
    await db.update_about(user_id, truncate(message.text.strip(), 500))
    await set_state(db, state, message.from_user.id, None)
    await message.answer("✅ Описание обновлено!", reply_markup=MAIN_MENU)


@router.callback_query(EditProfileStates.waiting_level, F.data.startswith("plevel:"))
async def edit_profile_level(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Обновление уровня."""
    level = query.data.split(":")[1]
    user_id = await ensure_user(db, query)
    await db.update_profile_level(user_id, level)
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer(f"✅ Уровень обновлён: <b>{level}</b>", reply_markup=MAIN_MENU)
    await query.answer()


@router.callback_query(EditProfileStates.waiting_ride, F.data.startswith("ride:"))
async def edit_profile_ride(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Обновление типа катания."""
    ride_type = query.data.split(":", 1)[1]
    user_id = await ensure_user(db, query)
    await db.update_profile_ride_type(user_id, ride_type)
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer(f"✅ Тип катания обновлён: <b>{ride_type}</b>", reply_markup=MAIN_MENU)
    await query.answer()


# ═══════════════════════════════════════════════════════════════════
# УДАЛЕНИЕ ПРОФИЛЯ
# ═══════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "profile:delete")
async def profile_delete(query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Удаление профиля."""
    user_id = await ensure_user(db, query)
    await db.delete_profile(user_id)
    await set_state(db, state, query.from_user.id, None)
    await query.message.answer("🗑️ Профиль удалён.", reply_markup=MAIN_MENU)
    await query.answer()
    logger.info(f"User {query.from_user.id} deleted profile")


# ═══════════════════════════════════════════════════════════════════
# ГДЕ КАТАЮСЬ
# ═══════════════════════════════════════════════════════════════════

@router.message(F.text == "🎿 Где катаюсь")
async def edit_riding_plans(message: Message, state: FSMContext, db: Database) -> None:
    """Редактирование планов катания."""
    user_id = await ensure_user(db, message)
    profile = await db.get_profile(user_id)
    
    if not profile:
        await message.answer(
            "❌ Сначала создай профиль в разделе «👤 Профиль»",
            reply_markup=MAIN_MENU,
        )
        return
    
    current_about = profile["about"] if profile["about"] else ""
    await set_state(db, state, message.from_user.id, EditDescriptionStates.waiting_description)
    
    hint = ""
    if current_about:
        hint = f"Сейчас: <i>{current_about}</i>\n\n"
    
    await message.answer(
        f"🎿 <b>Где катаюсь</b>\n\n{hint}"
        "Напиши куда планируешь поехать кататься — курорт, даты, время.\n"
        "Это увидят другие райдеры в поиске компании.\n\n"
        "Например: «Шерегеш, 25-28 января, ищу компанию на фрирайд»",
        reply_markup=BACK_KB,
    )


@router.message(EditDescriptionStates.waiting_description, F.text)
async def edit_riding_plans_got(message: Message, state: FSMContext, db: Database) -> None:
    """Сохранение планов катания."""
    if not message.text or message.text == "◀️ Назад":
        await set_state(db, state, message.from_user.id, None)
        await message.answer("Отменено.", reply_markup=MAIN_MENU)
        return
    
    user_id = await ensure_user(db, message)
    new_about = truncate(message.text.strip(), 500)
    
    await db.update_about(user_id, new_about)
    await set_state(db, state, message.from_user.id, None)
    await message.answer("✅ Планы сохранены! Теперь их увидят другие райдеры.", reply_markup=MAIN_MENU)
