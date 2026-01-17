import httpx
from typing import Optional


async def get_weather(lat: float, lon: float, api_key: str) -> Optional[dict]:
    """Get current weather from OpenWeatherMap API."""
    if not api_key:
        return None
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "lang": "ru",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "temp": round(data["main"]["temp"]),
                    "feels_like": round(data["main"]["feels_like"]),
                    "description": data["weather"][0]["description"],
                    "wind": round(data["wind"]["speed"]),
                    "humidity": data["main"]["humidity"],
                    "icon": get_weather_emoji(data["weather"][0]["icon"]),
                }
    except Exception:
        pass
    return None


def get_weather_emoji(icon_code: str) -> str:
    """Convert OpenWeatherMap icon code to emoji."""
    icons = {
        "01d": "☀️", "01n": "🌙",
        "02d": "⛅", "02n": "☁️",
        "03d": "☁️", "03n": "☁️",
        "04d": "☁️", "04n": "☁️",
        "09d": "🌧️", "09n": "🌧️",
        "10d": "🌦️", "10n": "🌧️",
        "11d": "⛈️", "11n": "⛈️",
        "13d": "🌨️", "13n": "🌨️",
        "50d": "🌫️", "50n": "🌫️",
    }
    return icons.get(icon_code, "🌤️")


def format_weather(weather: dict) -> str:
    """Format weather data for display."""
    return (
        f"{weather['icon']} {weather['temp']}°C (ощущается {weather['feels_like']}°C)\n"
        f"💨 Ветер: {weather['wind']} м/с\n"
        f"💧 Влажность: {weather['humidity']}%\n"
        f"📝 {weather['description'].capitalize()}"
    )
