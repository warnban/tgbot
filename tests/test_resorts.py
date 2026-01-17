"""Тесты для расчётов расстояний."""
import pytest
from services.resorts import haversine_km


class TestHaversine:
    """Тесты формулы Haversine."""

    def test_same_location(self):
        """Расстояние до себя = 0."""
        dist = haversine_km(55.7558, 37.6173, 55.7558, 37.6173)
        assert dist == 0

    def test_moscow_to_spb(self):
        """Москва → Санкт-Петербург ≈ 634 км."""
        moscow = (55.7558, 37.6173)
        spb = (59.9343, 30.3351)
        dist = haversine_km(moscow[0], moscow[1], spb[0], spb[1])
        assert 630 <= dist <= 640

    def test_moscow_to_sochi(self):
        """Москва → Сочи ≈ 1400 км."""
        moscow = (55.7558, 37.6173)
        sochi = (43.5850, 39.7230)
        dist = haversine_km(moscow[0], moscow[1], sochi[0], sochi[1])
        assert 1350 <= dist <= 1450

    def test_short_distance(self):
        """Короткое расстояние."""
        # Примерно 1 км
        dist = haversine_km(55.7558, 37.6173, 55.7650, 37.6173)
        assert 0.5 <= dist <= 1.5

    def test_symmetry(self):
        """Расстояние A→B = B→A."""
        dist1 = haversine_km(55.7558, 37.6173, 59.9343, 30.3351)
        dist2 = haversine_km(59.9343, 30.3351, 55.7558, 37.6173)
        assert abs(dist1 - dist2) < 0.001
