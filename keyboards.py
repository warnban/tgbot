"""Клавиатуры бота."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


# ═══════════════════════════════════════════════════════════════════
# REPLY KEYBOARDS (постоянное меню внизу)
# ═══════════════════════════════════════════════════════════════════

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Меню")],
        [KeyboardButton(text="🏂 Калькулятор"), KeyboardButton(text="🏔️ Склоны")],
        [KeyboardButton(text="🔍 Искать компанию"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="📅 Создать событие"), KeyboardButton(text="🗓️ Мои события")],
        [KeyboardButton(text="🎓 Инструкторы"), KeyboardButton(text="🆘 SOS")],
        [KeyboardButton(text="🤝 Контакты"), KeyboardButton(text="🎿 Где катаюсь")],
        [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="💝 Поддержать")],
    ],
    resize_keyboard=True,
)

LOCATION_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
        [KeyboardButton(text="◀️ Назад")],
    ],
    resize_keyboard=True,
)

BACK_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="◀️ Назад")]],
    resize_keyboard=True,
)


# ═══════════════════════════════════════════════════════════════════
# INLINE KEYBOARDS
# ═══════════════════════════════════════════════════════════════════

# --- Калькулятор ---
def calc_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏂 Сноуборд", callback_data="calc:snowboard"),
                InlineKeyboardButton(text="🎿 Лыжи", callback_data="calc:ski"),
            ],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")],
        ]
    )


def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Мужской", callback_data="gender:м"),
                InlineKeyboardButton(text="👩 Женский", callback_data="gender:ж"),
            ]
        ]
    )


def level_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Новичок", callback_data="level:Новичок")],
            [InlineKeyboardButton(text="🔵 Средний", callback_data="level:Средний")],
            [InlineKeyboardButton(text="🔴 Продвинутый", callback_data="level:Продвинутый")],
        ]
    )


def snowboard_style_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Универсал", callback_data="style:Универсал")],
            [InlineKeyboardButton(text="🎪 Фристайл", callback_data="style:Фристайл")],
            [InlineKeyboardButton(text="🏔️ Фрирайд", callback_data="style:Фрирайд")],
        ]
    )


def ski_style_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⛷️ Трасса", callback_data="style:Трасса")],
            [InlineKeyboardButton(text="🎯 Универсал", callback_data="style:Универсал")],
            [InlineKeyboardButton(text="🏔️ Фрирайд", callback_data="style:Фрирайд")],
        ]
    )


# --- Профиль ---
def profile_photo_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить фото", callback_data="profile:skip_photo")],
        ]
    )


def profile_more_photos_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить ещё фото", callback_data="profile:more_photos")],
            [InlineKeyboardButton(text="✅ Готово", callback_data="profile:photos_done")],
        ]
    )


def profile_gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Мужчина", callback_data="pgender:м"),
                InlineKeyboardButton(text="👩 Женщина", callback_data="pgender:ж"),
            ],
        ]
    )


def ride_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏂 Сноуборд", callback_data="ride:🏂 Сноуборд"),
                InlineKeyboardButton(text="🎿 Лыжи", callback_data="ride:🎿 Лыжи"),
            ],
        ]
    )


def profile_level_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Новичок", callback_data="plevel:Новичок")],
            [InlineKeyboardButton(text="🔵 Средний", callback_data="plevel:Средний")],
            [InlineKeyboardButton(text="🔴 Продвинутый", callback_data="plevel:Продвинутый")],
        ]
    )


def profile_actions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Редактировать", callback_data="profile:edit"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data="profile:delete"),
            ],
        ]
    )


def profile_edit_kb() -> InlineKeyboardMarkup:
    """Меню редактирования профиля."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Фото", callback_data="profile:edit_photos")],
            [InlineKeyboardButton(text="📍 Город", callback_data="profile:edit_city")],
            [InlineKeyboardButton(text="💬 Описание", callback_data="profile:edit_about")],
            [InlineKeyboardButton(text="📊 Уровень", callback_data="profile:edit_level")],
            [InlineKeyboardButton(text="🎿 Тип катания", callback_data="profile:edit_ride")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="nav:menu")],
        ]
    )


# --- Склоны ---
def resorts_list_kb(resorts: list[tuple[dict, float]]) -> InlineKeyboardMarkup:
    """Список склонов с расстоянием."""
    rows = []
    for resort, dist_km in resorts:
        dist_str = f"{dist_km:.0f} км" if dist_km >= 1 else f"{dist_km * 1000:.0f} м"
        rows.append([
            InlineKeyboardButton(
                text=f"🏔️ {resort['name']} — {dist_str}",
                callback_data=f"resort:{resort['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text="🌍 Склоны в других городах", callback_data="resorts:cities")])
    rows.append([InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cities_list_kb(cities: list[str]) -> InlineKeyboardMarkup:
    """Список городов с курортами."""
    rows = []
    for city in cities:
        rows.append([
            InlineKeyboardButton(text=f"📍 {city}", callback_data=f"city:{city[:30]}")
        ])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="nav:resorts")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def city_resorts_kb(resorts: list, city: str) -> InlineKeyboardMarkup:
    """Список склонов в городе."""
    rows = []
    for resort in resorts:
        rows.append([
            InlineKeyboardButton(
                text=f"🏔️ {resort['name']}",
                callback_data=f"resort:{resort['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text="◀️ К городам", callback_data="resorts:cities")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def resort_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад к списку", callback_data="nav:resorts")]]
    )


def resort_detail_kb(resort_id: int) -> InlineKeyboardMarkup:
    """Детали курорта с действиями."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data=f"review:{resort_id}"),
                InlineKeyboardButton(text="📖 Отзывы", callback_data=f"reviews:{resort_id}"),
            ],
            [InlineKeyboardButton(text="🔔 Подписка на погоду", callback_data=f"weather_sub:{resort_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="nav:resorts")],
        ]
    )


# --- Поиск компании ---
def buddy_filter_kb() -> InlineKeyboardMarkup:
    """Фильтры поиска."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎿 Тип катания", callback_data="buddy:filter_ride")],
            [InlineKeyboardButton(text="📊 Уровень", callback_data="buddy:filter_level")],
            [InlineKeyboardButton(text="🗑️ Сбросить фильтры", callback_data="buddy:filter_clear")],
            [InlineKeyboardButton(text="💖 Кто меня лайкнул", callback_data="buddy:who_liked")],
            [InlineKeyboardButton(text="▶️ Начать просмотр", callback_data="buddy:start")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")],
        ]
    )


def ride_type_filter_kb() -> InlineKeyboardMarkup:
    """Фильтр по типу катания."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏂 Сноуборд", callback_data="fride:🏂 Сноуборд")],
            [InlineKeyboardButton(text="🎿 Лыжи", callback_data="fride:🎿 Лыжи")],
            [InlineKeyboardButton(text="🔄 Любой", callback_data="fride:any")],
        ]
    )


def level_filter_kb() -> InlineKeyboardMarkup:
    """Фильтр по уровню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Новичок", callback_data="flevel:Новичок")],
            [InlineKeyboardButton(text="🔵 Средний", callback_data="flevel:Средний")],
            [InlineKeyboardButton(text="🔴 Продвинутый", callback_data="flevel:Продвинутый")],
            [InlineKeyboardButton(text="🔄 Любой", callback_data="flevel:any")],
        ]
    )


def buddy_actions_kb(is_event: bool = False, event_id: int = None, user_id: int = None) -> InlineKeyboardMarkup:
    """Кнопки действий при просмотре анкеты."""
    if is_event and event_id:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👎 Пропустить", callback_data="buddy:skip"),
                    InlineKeyboardButton(text="👍 Хочу!", callback_data=f"event:join:{event_id}"),
                ],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👎 Пропустить", callback_data="buddy:skip"),
                InlineKeyboardButton(text="👍 Нравится", callback_data=f"buddy:like:{user_id}"),
            ],
            [
                InlineKeyboardButton(text="💬 Написать", callback_data=f"chat:{user_id}"),
                InlineKeyboardButton(text="🚫 Блок", callback_data=f"buddy:block:{user_id}"),
            ],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")],
        ]
    )


def who_liked_kb(likers: list) -> InlineKeyboardMarkup:
    """Список тех, кто лайкнул."""
    rows = []
    for liker in likers[:10]:
        name = liker["first_name"] if liker.get("first_name") else "Райдер"
        rows.append([
            InlineKeyboardButton(text=f"💖 {name}", callback_data=f"viewliker:{liker['id']}")
        ])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="nav:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def liker_actions_kb(user_id: int) -> InlineKeyboardMarkup:
    """Действия с профилем лайкнувшего."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👍 Лайкнуть в ответ", callback_data=f"likeback:{user_id}"),
                InlineKeyboardButton(text="💬 Написать", callback_data=f"chat:{user_id}"),
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="buddy:who_liked")],
        ]
    )


# --- Навигация ---
def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")]]
    )


# --- Поддержка ---
def donate_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="☕ Дать на чай", url="https://pay.cloudtips.ru/p/30dfc737")],
        ]
    )


# --- События ---
def event_photo_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить фото", callback_data="event:skip_photo")],
        ]
    )


def event_resorts_kb(resorts: list) -> InlineKeyboardMarkup:
    """Выбор курорта для события."""
    rows = []
    for resort in resorts[:20]:
        rows.append([
            InlineKeyboardButton(
                text=f"🏔️ {resort['name']}",
                callback_data=f"evresort:{resort['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text="◀️ Отмена", callback_data="nav:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def event_level_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Новичок", callback_data="evlevel:Новичок")],
            [InlineKeyboardButton(text="🔵 Средний", callback_data="evlevel:Средний")],
            [InlineKeyboardButton(text="🔴 Продвинутый", callback_data="evlevel:Продвинутый")],
            [InlineKeyboardButton(text="⚫ Любой уровень", callback_data="evlevel:Любой")],
        ]
    )


def event_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Создать событие", callback_data="event:confirm")],
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="nav:menu")],
        ]
    )


# --- Контакты ---
def contacts_kb(matches: list) -> InlineKeyboardMarkup:
    """Список контактов (мэтчей)."""
    rows = []
    for match in matches[:10]:
        name = match["first_name"] if match["first_name"] else "Райдер"
        username = match["username"]
        if username:
            rows.append([
                InlineKeyboardButton(text=f"💬 {name}", url=f"https://t.me/{username}")
            ])
        else:
            rows.append([
                InlineKeyboardButton(text=f"💬 {name}", url=f"tg://user?id={match['telegram_id']}")
            ])
    rows.append([InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Мои события ---
def my_events_kb(events: list) -> InlineKeyboardMarkup:
    """Список событий пользователя."""
    rows = []
    for event in events[:10]:
        rows.append([
            InlineKeyboardButton(
                text=f"📅 {event['resort_name']} — {event['event_date']}",
                callback_data=f"myevent:{event['id']}"
            )
        ])
    if not events:
        rows.append([InlineKeyboardButton(text="📅 Создать событие", callback_data="nav:create_event")])
    rows.append([InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_event_actions_kb(event_id: int) -> InlineKeyboardMarkup:
    """Действия с событием."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Удалить событие", callback_data=f"delevent:{event_id}")],
            [InlineKeyboardButton(text="◀️ К списку", callback_data="nav:my_events")],
        ]
    )


# --- Календарь событий ---
def events_calendar_kb() -> InlineKeyboardMarkup:
    """Фильтры календаря событий."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📆 Ближайшая неделя", callback_data="calendar:week")],
            [InlineKeyboardButton(text="📅 Ближайший месяц", callback_data="calendar:month")],
            [InlineKeyboardButton(text="🗓️ Все события", callback_data="calendar:all")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")],
        ]
    )


def events_list_kb(events: list) -> InlineKeyboardMarkup:
    """Список событий."""
    rows = []
    for event in events[:10]:
        rows.append([
            InlineKeyboardButton(
                text=f"📅 {event['resort_name']} — {event['event_date']}",
                callback_data=f"viewevent:{event['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text="◀️ К фильтрам", callback_data="nav:calendar")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def event_view_kb(event_id: int, group_link: str) -> InlineKeyboardMarkup:
    """Просмотр события."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Присоединиться", url=group_link)],
            [InlineKeyboardButton(text="🔔 Напомнить за день", callback_data=f"remind:{event_id}")],
            [InlineKeyboardButton(text="◀️ К списку", callback_data="nav:calendar")],
        ]
    )


# --- SOS ---
def sos_back_kb() -> InlineKeyboardMarkup:
    """Кнопка назад для SOS."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")],
        ]
    )


# --- Инструкторы ---
def instructor_cities_kb(cities: list) -> InlineKeyboardMarkup:
    """Список городов с инструкторами."""
    rows = []
    for city in cities:
        rows.append([
            InlineKeyboardButton(text=f"📍 {city}", callback_data=f"instcity:{city[:25]}")
        ])
    if not cities:
        rows.append([InlineKeyboardButton(text="😔 Пока нет инструкторов", callback_data="nav:menu")])
    rows.append([InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Отзывы ---
def review_rating_kb() -> InlineKeyboardMarkup:
    """Выбор оценки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐", callback_data="rating:1"),
                InlineKeyboardButton(text="⭐⭐", callback_data="rating:2"),
                InlineKeyboardButton(text="⭐⭐⭐", callback_data="rating:3"),
            ],
            [
                InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rating:4"),
                InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rating:5"),
            ],
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="nav:menu")],
        ]
    )


# --- Чат ---
def chat_actions_kb() -> InlineKeyboardMarkup:
    """Действия в чате."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Завершить чат", callback_data="chat:end")],
        ]
    )
