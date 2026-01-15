from dataclasses import dataclass, field
from typing import List
import os

from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str
    database_path: str
    weather_api_key: str
    admin_ids: List[int] = field(default_factory=list)


def load_config() -> Config:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")
    database_path = os.getenv("DATABASE_PATH", "bot.db").strip()
    weather_api_key = os.getenv("WEATHER_API_KEY", "").strip()
    
    # Admin IDs (comma-separated)
    admin_ids_str = os.getenv("ADMIN_IDS", "").strip()
    admin_ids = []
    if admin_ids_str:
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]
    
    return Config(
        bot_token=bot_token,
        database_path=database_path,
        weather_api_key=weather_api_key,
        admin_ids=admin_ids,
    )
