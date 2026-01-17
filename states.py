"""FSM состояния бота."""
from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """Создание профиля."""
    waiting_photos = State()
    waiting_more_photos = State()
    waiting_gender = State()
    waiting_ride_type = State()
    waiting_skill_level = State()
    waiting_age = State()
    waiting_city = State()
    waiting_about = State()


class EditProfileStates(StatesGroup):
    """Редактирование профиля."""
    waiting_photos = State()
    waiting_city = State()
    waiting_about = State()
    waiting_level = State()
    waiting_ride = State()


class EditDescriptionStates(StatesGroup):
    """Редактирование описания."""
    waiting_description = State()


class SnowboardCalcStates(StatesGroup):
    """Калькулятор сноуборда."""
    waiting_height = State()
    waiting_weight = State()
    waiting_gender = State()
    waiting_shoe_size = State()
    waiting_style = State()


class SkiCalcStates(StatesGroup):
    """Калькулятор лыж."""
    waiting_height = State()
    waiting_weight = State()
    waiting_level = State()
    waiting_style = State()


class ResortStates(StatesGroup):
    """Склоны."""
    waiting_location = State()


class BuddySearchStates(StatesGroup):
    """Поиск компании."""
    browsing = State()


class BuddyFilterStates(StatesGroup):
    """Фильтры поиска."""
    waiting_ride = State()
    waiting_level = State()


class EventStates(StatesGroup):
    """Создание события."""
    waiting_group_link = State()
    waiting_photo = State()
    waiting_resort = State()
    waiting_date = State()
    waiting_level = State()
    waiting_description = State()


class AddInstructorStates(StatesGroup):
    """Добавление инструктора (админ)."""
    waiting_name = State()
    waiting_telegram = State()
    waiting_city = State()
    waiting_resorts = State()


class ReviewStates(StatesGroup):
    """Отзыв на курорт."""
    waiting_rating = State()
    waiting_text = State()


class ChatStates(StatesGroup):
    """Анонимный чат."""
    chatting = State()


class BroadcastStates(StatesGroup):
    """Рассылка (админ)."""
    waiting_message = State()
