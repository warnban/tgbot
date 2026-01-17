"""Тесты для умного матчинга."""
import pytest
from handlers.buddy_search import calculate_match_score


class TestMatchScore:
    """Тесты расчёта score для матчинга."""

    def test_identical_profiles(self):
        """Идентичные профили → максимальный score."""
        profile1 = {
            "ride_type": "🏂 Сноуборд",
            "skill_level": "Средний",
            "city": "Москва",
            "age": 25,
            "about": "Описание",
            "photos": '["photo1"]',
        }
        profile2 = profile1.copy()
        
        score = calculate_match_score(profile1, profile2)
        # +20 (ride_type) +15 (level) +20 (city) +10 (age) +5 (about) +10 (photos) = 80
        assert score >= 75

    def test_different_ride_type(self):
        """Разный тип катания → меньше score."""
        profile1 = {
            "ride_type": "🏂 Сноуборд",
            "skill_level": "Средний",
            "city": "Москва",
            "age": 25,
        }
        profile2 = {
            "ride_type": "🎿 Лыжи",
            "skill_level": "Средний",
            "city": "Москва",
            "age": 25,
        }
        
        score = calculate_match_score(profile1, profile2)
        # +15 (level) +20 (city) +10 (age) = 45
        assert 40 <= score <= 50

    def test_different_city(self):
        """Разный город → меньше score."""
        profile1 = {
            "ride_type": "🏂 Сноуборд",
            "skill_level": "Средний",
            "city": "Москва",
            "age": 25,
        }
        profile2 = {
            "ride_type": "🏂 Сноуборд",
            "skill_level": "Средний",
            "city": "Санкт-Петербург",
            "age": 25,
        }
        
        score = calculate_match_score(profile1, profile2)
        # +20 (ride_type) +15 (level) +10 (age) = 45
        assert 40 <= score <= 50

    def test_age_difference(self):
        """Большая разница в возрасте → меньше score."""
        profile1 = {
            "ride_type": "🏂 Сноуборд",
            "skill_level": "Средний",
            "city": "Москва",
            "age": 25,
        }
        profile2 = {
            "ride_type": "🏂 Сноуборд",
            "skill_level": "Средний",
            "city": "Москва",
            "age": 50,
        }
        
        score = calculate_match_score(profile1, profile2)
        # +20 (ride_type) +15 (level) +20 (city) = 55 (без бонуса за возраст)
        assert 50 <= score <= 60

    def test_neighbor_level(self):
        """Соседний уровень → небольшой бонус."""
        profile1 = {
            "ride_type": "🏂 Сноуборд",
            "skill_level": "Новичок",
            "city": "Москва",
            "age": 25,
        }
        profile2 = {
            "ride_type": "🏂 Сноуборд",
            "skill_level": "Средний",
            "city": "Москва",
            "age": 25,
        }
        
        score = calculate_match_score(profile1, profile2)
        # +20 (ride_type) +5 (neighbor level) +20 (city) +10 (age) = 55
        assert 50 <= score <= 60

    def test_empty_profiles(self):
        """Пустые профили → минимальный score."""
        profile1 = {}
        profile2 = {}
        
        score = calculate_match_score(profile1, profile2)
        assert score == 0

    def test_with_photos_bonus(self):
        """Наличие фото → бонус."""
        profile1 = {"photos": None}
        profile2_no_photo = {"photos": None}
        profile2_with_photo = {"photos": '["photo1"]'}
        
        score_no_photo = calculate_match_score(profile1, profile2_no_photo)
        score_with_photo = calculate_match_score(profile1, profile2_with_photo)
        
        assert score_with_photo > score_no_photo

    def test_with_about_bonus(self):
        """Наличие описания → бонус."""
        profile1 = {"about": ""}
        profile2_no_about = {"about": ""}
        profile2_with_about = {"about": "Какое-то описание"}
        
        score_no_about = calculate_match_score(profile1, profile2_no_about)
        score_with_about = calculate_match_score(profile1, profile2_with_about)
        
        assert score_with_about > score_no_about
