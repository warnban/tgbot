"""Тесты для калькуляторов снаряжения."""
import pytest
from services.equipment import calculate_snowboard_length, calculate_ski_length


class TestSnowboardCalculator:
    """Тесты калькулятора сноуборда."""

    def test_basic_calculation_male(self):
        """Базовый расчёт для мужчины."""
        result = calculate_snowboard_length(
            height_cm=175,
            weight_kg=75,
            gender="м",
            shoe_size=42,
            style="Универсал",
        )
        assert 150 <= result.min_length <= 160
        assert 155 <= result.max_length <= 170
        assert result.width == ""  # Обычная доска

    def test_wide_board_for_large_feet(self):
        """Широкая доска для большого размера ноги."""
        result = calculate_snowboard_length(
            height_cm=180,
            weight_kg=80,
            gender="м",
            shoe_size=45,
            style="Универсал",
        )
        assert result.width == "W"

    def test_female_adjustment(self):
        """Корректировка для женщины."""
        result_male = calculate_snowboard_length(
            height_cm=165,
            weight_kg=60,
            gender="м",
            shoe_size=40,
            style="Универсал",
        )
        result_female = calculate_snowboard_length(
            height_cm=165,
            weight_kg=60,
            gender="ж",
            shoe_size=38,
            style="Универсал",
        )
        # Женская доска должна быть короче
        assert result_female.min_length < result_male.min_length

    def test_freestyle_shorter(self):
        """Фристайл — короче."""
        result_uni = calculate_snowboard_length(
            height_cm=175,
            weight_kg=75,
            gender="м",
            shoe_size=42,
            style="Универсал",
        )
        result_free = calculate_snowboard_length(
            height_cm=175,
            weight_kg=75,
            gender="м",
            shoe_size=42,
            style="Фристайл",
        )
        assert result_free.min_length < result_uni.min_length

    def test_freeride_longer(self):
        """Фрирайд — длиннее."""
        result_uni = calculate_snowboard_length(
            height_cm=175,
            weight_kg=75,
            gender="м",
            shoe_size=42,
            style="Универсал",
        )
        result_ride = calculate_snowboard_length(
            height_cm=175,
            weight_kg=75,
            gender="м",
            shoe_size=42,
            style="Фрирайд",
        )
        assert result_ride.max_length > result_uni.max_length


class TestSkiCalculator:
    """Тесты калькулятора лыж."""

    def test_basic_calculation(self):
        """Базовый расчёт."""
        result = calculate_ski_length(
            height_cm=175,
            weight_kg=75,
            level="Средний",
            style="Универсал",
        )
        assert 150 <= result.min_length <= 170
        assert 165 <= result.max_length <= 180

    def test_beginner_shorter(self):
        """Новичок — короче."""
        result_mid = calculate_ski_length(
            height_cm=175,
            weight_kg=75,
            level="Средний",
            style="Универсал",
        )
        result_beg = calculate_ski_length(
            height_cm=175,
            weight_kg=75,
            level="Новичок",
            style="Универсал",
        )
        assert result_beg.min_length < result_mid.min_length

    def test_advanced_longer(self):
        """Продвинутый — длиннее."""
        result_mid = calculate_ski_length(
            height_cm=175,
            weight_kg=75,
            level="Средний",
            style="Универсал",
        )
        result_adv = calculate_ski_length(
            height_cm=175,
            weight_kg=75,
            level="Продвинутый",
            style="Универсал",
        )
        assert result_adv.max_length > result_mid.max_length

    def test_trail_narrower_waist(self):
        """Трасса — узкая талия."""
        result = calculate_ski_length(
            height_cm=175,
            weight_kg=75,
            level="Средний",
            style="Трасса",
        )
        assert "до 75" in result.waist

    def test_freeride_wider_waist(self):
        """Фрирайд — широкая талия."""
        result = calculate_ski_length(
            height_cm=175,
            weight_kg=75,
            level="Средний",
            style="Фрирайд",
        )
        assert "100+" in result.waist

    def test_heavy_weight_longer(self):
        """Большой вес — длиннее."""
        result_light = calculate_ski_length(
            height_cm=175,
            weight_kg=60,
            level="Средний",
            style="Универсал",
        )
        result_heavy = calculate_ski_length(
            height_cm=175,
            weight_kg=90,
            level="Средний",
            style="Универсал",
        )
        assert result_heavy.max_length > result_light.max_length
