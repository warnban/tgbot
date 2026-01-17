"""Конфигурация pytest."""
import pytest


@pytest.fixture
def sample_profile():
    """Пример профиля для тестов."""
    return {
        "user_id": 1,
        "first_name": "Тест",
        "age": 25,
        "gender": "м",
        "ride_type": "🏂 Сноуборд",
        "skill_level": "Средний",
        "city": "Москва",
        "location_lat": 55.7558,
        "location_lon": 37.6173,
        "about": "Тестовое описание",
        "photos": '["photo1", "photo2"]',
    }


@pytest.fixture
def sample_resort():
    """Пример курорта для тестов."""
    return {
        "id": 1,
        "name": "Тестовый склон",
        "lat": 55.8,
        "lon": 37.6,
        "address": "Москва",
        "site": "https://test.ru",
        "trails_count": 10,
        "trail_levels": "зелёные, синие",
        "lifts_count": 5,
        "rescue_phone": "+71234567890",
    }
