from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    waiting_photos = State()
    waiting_more_photos = State()
    waiting_gender = State()
    waiting_ride_type = State()
    waiting_skill_level = State()
    waiting_age = State()
    waiting_city = State()
    waiting_about = State()


class EditDescriptionStates(StatesGroup):
    waiting_description = State()


class SnowboardCalcStates(StatesGroup):
    waiting_height = State()
    waiting_weight = State()
    waiting_gender = State()
    waiting_shoe_size = State()
    waiting_style = State()


class SkiCalcStates(StatesGroup):
    waiting_height = State()
    waiting_weight = State()
    waiting_level = State()
    waiting_style = State()


class ResortStates(StatesGroup):
    waiting_location = State()


class BuddySearchStates(StatesGroup):
    browsing = State()


class EventStates(StatesGroup):
    waiting_group_link = State()
    waiting_photo = State()
    waiting_resort = State()
    waiting_date = State()
    waiting_level = State()
    waiting_description = State()


class AddInstructorStates(StatesGroup):
    waiting_name = State()
    waiting_telegram = State()
    waiting_city = State()
    waiting_resorts = State()
