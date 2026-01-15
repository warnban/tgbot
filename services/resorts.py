import math
from typing import Iterable, List, Tuple


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def sort_by_distance(
    user_lat: float,
    user_lon: float,
    resorts: Iterable[dict],
) -> List[Tuple[dict, float]]:
    enriched: List[Tuple[dict, float]] = []
    for resort in resorts:
        dist = haversine_km(user_lat, user_lon, resort["lat"], resort["lon"])
        enriched.append((resort, dist))
    enriched.sort(key=lambda item: item[1])
    return enriched
