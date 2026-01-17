# Быстрый старт Snow Crew 2.0

## Что реализовано

✅ **Все улучшения из плана:**
1. Модульная архитектура (handlers/, middlewares/, services/)
2. Умный матчинг с фильтрами
3. Редактирование отдельных полей профиля
4. Блокировка пользователей
5. «Кто меня лайкнул»
6. Анонимный чат через бота
7. Отзывы на курорты (⭐ 1-5)
8. Уведомления о погоде (подписка на снег)
9. FSM восстановление из БД
10. Rate limiting (30 сообщений/минуту)
11. Логирование в файл и консоль
12. Валидация входных данных
13. Unit-тесты

## Установка

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Создать .env файл
echo BOT_TOKEN=YOUR_TOKEN > .env
echo DATABASE_PATH=bot.db >> .env
echo WEATHER_API_KEY=YOUR_WEATHER_KEY >> .env  # опционально
echo ADMIN_IDS=123456789 >> .env  # ваш telegram ID

# 3. Запустить
python bot.py
```

## Тестирование

```bash
# Установить pytest (если не установлен)
pip install pytest pytest-asyncio

# Запустить тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=. --cov-report=html
```

## Структура проекта

```
tgbot/
├── bot.py                 # Точка входа + background tasks
├── config.py              # Конфигурация из .env
├── db.py                  # База данных (SQLite)
├── states.py              # FSM состояния
├── keyboards.py           # Клавиатуры
├── requirements.txt       # Зависимости
├── README.md              # Документация
├── .gitignore
│
├── handlers/              # Обработчики по модулям
│   ├── __init__.py        # setup_routers()
│   ├── common.py          # Общие хелперы
│   ├── start.py           # /start, навигация
│   ├── profile.py         # Профиль
│   ├── calculator.py      # Калькулятор
│   ├── resorts.py         # Склоны
│   ├── buddy_search.py    # Поиск компании
│   ├── events.py          # События
│   ├── contacts.py        # Контакты
│   ├── instructors.py     # Инструкторы
│   ├── sos.py             # SOS
│   ├── reviews.py         # Отзывы
│   ├── chat.py            # Чат
│   └── admin.py           # Админ
│
├── middlewares/           # Middleware
│   ├── __init__.py
│   ├── logging.py         # Логирование
│   ├── rate_limit.py      # Rate limiting
│   └── state_restore.py   # Восстановление FSM
│
├── services/              # Бизнес-логика
│   ├── equipment.py       # Калькуляторы
│   ├── resorts.py         # Расчёт расстояний
│   └── weather.py         # Погода
│
└── tests/                 # Тесты
    ├── __init__.py
    ├── conftest.py
    ├── test_equipment.py
    ├── test_resorts.py
    └── test_matching.py
```

## Ключевые улучшения

### 1. Модульность
Код разбит на логические модули — легко добавлять новые фичи.

### 2. Умный матчинг
Профили сортируются по score (0-100):
- Тот же тип катания: +20
- Тот же уровень: +15
- Тот же город: +20
- Близкий возраст: +10
- Близко по геолокации: +20
- Есть описание: +5
- Есть фото: +10

### 3. Middleware
- **LoggingMiddleware**: логирует каждый запрос с временем выполнения
- **RateLimitMiddleware**: защита от спама (30 сообщений/минуту)
- **StateRestoreMiddleware**: восстанавливает FSM после перезапуска

### 4. Background Tasks
- **reminder_checker**: проверяет напоминания каждый час
- **weather_notifier**: уведомляет о снеге в 8:00

### 5. База данных
Новые таблицы:
- `blocks` — блокировки
- `reviews` — отзывы на курорты
- `chats` — анонимные чаты
- `chat_messages` — сообщения
- `weather_subscriptions` — подписки на погоду

## Исправленные баги

1. ✅ FSM не восстанавливался после перезапуска
2. ✅ Race condition в мэтчах (двойные уведомления)
3. ✅ Нет пагинации в поиске (все в память)
4. ✅ Баг с `message.chat.id` вместо `message.from_user.id`

## Команды бота

### Пользовательские
- `/start` — начало работы

### Админские
- `/stats` — статистика бота
- `/addinst` — добавить инструктора
- `/broadcast` — рассылка всем

## Следующие шаги

### Быстрые улучшения
- [ ] Добавить индексы в БД для ускорения
- [ ] Переехать на Redis для FSM
- [ ] Мигрировать на PostgreSQL

### Новые фичи
- [ ] WebApp для профилей
- [ ] Голосовые в чате
- [ ] Карта курортов
- [ ] ML для определения уровня по фото

## Troubleshooting

### Бот не запускается
```bash
# Проверить токен
python -c "from config import load_config; print(load_config().bot_token)"

# Проверить зависимости
pip install -r requirements.txt --upgrade
```

### FSM не работает
Убедитесь что `StateRestoreMiddleware` зарегистрирован:
```python
dp.message.middleware(StateRestoreMiddleware())
```

### Лайки не работают
Проверьте что `user_id` передаётся через `ensure_user()`, а не `message.chat.id`.

## Контакты

Разработчик: @aleblanche  
Версия: 2.0  
Python: 3.10+
