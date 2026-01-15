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
# INLINE KEYBOARDS (кнопки под сообщениями)
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


# --- Поиск компании ---
def buddy_actions_kb(is_event: bool = False, event_id: int = None) -> InlineKeyboardMarkup:
    if is_event and event_id:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👎  Пропустить", callback_data="buddy:skip"),
                    InlineKeyboardButton(text="👍  Хочу!", callback_data=f"event:join:{event_id}"),
                ],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👎  Пропустить", callback_data="buddy:skip"),
                InlineKeyboardButton(text="👍  Нравится", callback_data="buddy:like"),
            ],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="nav:menu")],
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
    """Выбор курорта для события (показываем все)."""
    rows = []
    for resort in resorts[:20]:  # Ограничиваем до 20
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
    """Список событий с возможностью присоединиться."""
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
