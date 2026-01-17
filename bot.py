"""Главный файл бота — точка входа."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import load_config
from db import Database
from handlers import setup_routers
from middlewares import LoggingMiddleware, RateLimitMiddleware, StateRestoreMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════════

async def reminder_checker(bot: Bot, db: Database) -> None:
    """Background task to check and send reminders."""
    while True:
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            reminders = await db.get_pending_reminders(current_time)
            
            for reminder in reminders:
                try:
                    await bot.send_message(
                        reminder["telegram_id"],
                        f"🔔 <b>Напоминание!</b>\n\n"
                        f"Завтра событие на {reminder['resort_name']}!\n"
                        f"📆 {reminder['event_date']}\n\n"
                        f"👥 Группа: {reminder['telegram_group_link']}",
                    )
                    await db.mark_reminder_sent(reminder["id"])
                except Exception as e:
                    logger.error(f"Failed to send reminder {reminder['id']}: {e}")
            
            # Cleanup old events
            cleaned = await db.cleanup_old_events()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old events")
                
        except Exception as e:
            logger.error(f"Reminder checker error: {e}")
        
        await asyncio.sleep(3600)  # Check every hour


async def weather_notifier(bot: Bot, db: Database, config) -> None:
    """Background task для уведомлений о погоде."""
    while True:
        try:
            from services.weather import get_weather, format_weather
            from datetime import datetime
            
            # Проверяем погоду раз в день в 8:00
            now = datetime.now()
            if now.hour != 8:
                await asyncio.sleep(3600)
                continue
            
            resorts = await db.list_resorts()
            
            for resort in resorts:
                subscribers = await db.get_weather_subscribers(resort["id"])
                if not subscribers:
                    continue
                
                # Получаем погоду
                weather = await get_weather(resort["lat"], resort["lon"], config.weather_api_key)
                if not weather:
                    continue
                
                # Проверяем снег
                if "snow" in weather.get("description", "").lower():
                    text = (
                        f"❄️ <b>Снег на {resort['name']}!</b>\n\n"
                        f"{format_weather(weather)}\n\n"
                        "Отличный день для катания!"
                    )
                    
                    for sub in subscribers:
                        try:
                            await bot.send_message(sub["telegram_id"], text)
                        except Exception as e:
                            logger.error(f"Failed to send weather to {sub['telegram_id']}: {e}")
                    
                    await asyncio.sleep(1)  # Rate limit
            
        except Exception as e:
            logger.error(f"Weather notifier error: {e}")
        
        await asyncio.sleep(3600)  # Check every hour


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

async def main() -> None:
    """Точка входа."""
    config = load_config()
    
    # Инициализация БД
    db = Database(config.database_path)
    await db.init()
    logger.info("Database initialized")
    
    # Создание бота
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # Dispatcher
    dp = Dispatcher()
    
    # Регистрация middleware
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(RateLimitMiddleware(rate_limit=30, period=60))
    dp.message.middleware(StateRestoreMiddleware())
    
    # Dependency Injection
    dp["db"] = db
    dp["config"] = config
    
    # Регистрация роутеров
    router = setup_routers()
    dp.include_router(router)
    
    # Запуск background tasks
    asyncio.create_task(reminder_checker(bot, db))
    asyncio.create_task(weather_notifier(bot, db, config))
    
    logger.info("🏂 Snow Crew started!")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
