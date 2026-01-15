import aiosqlite
import json
from contextlib import asynccontextmanager
from typing import Iterable, List, Optional


RESORTS_SEED = [
    # МОСКВА
    {"name": "КАНТ (Нагорная)", "lat": 55.6760, "lon": 37.5720, "address": "Москва", "site": "https://kant-sport.ru/", "trails_count": 11, "trail_levels": "зелёные, синие, красные", "lifts_count": 7, "rescue_phone": "+74959092443"},
    {"name": "Крылатское", "lat": 55.7530, "lon": 37.4480, "address": "Москва", "site": "https://krylatskoe-ski.ru/", "trails_count": 5, "trail_levels": "зелёные, синие", "lifts_count": 3, "rescue_phone": "+74991448878"},
    {"name": "Лата Трэк", "lat": 55.7906, "lon": 37.5736, "address": "Москва", "site": "https://spusk.ru/", "trails_count": 3, "trail_levels": "зелёные, синие", "lifts_count": 2, "rescue_phone": "+74993174777"},
    # МОСКОВСКАЯ ОБЛАСТЬ
    {"name": "Сорочаны", "lat": 56.0090, "lon": 37.3600, "address": "Московская область", "site": "https://sorochany.ru/", "trails_count": 10, "trail_levels": "зелёные, синие, красные", "lifts_count": 8, "rescue_phone": "+74955025255"},
    {"name": "Волен", "lat": 56.0603, "lon": 37.3904, "address": "Московская область", "site": "https://volen.ru/", "trails_count": 13, "trail_levels": "зелёные, синие, красные", "lifts_count": 10, "rescue_phone": "+74955012323"},
    {"name": "Степаново", "lat": 56.0621, "lon": 37.4012, "address": "Московская область", "site": "https://stepanovo-park.ru/", "trails_count": 8, "trail_levels": "зелёные, синие, красные", "lifts_count": 5, "rescue_phone": "+74955012000"},
    {"name": "Чулково (Клуб Тягачева)", "lat": 55.6547, "lon": 37.9636, "address": "Московская область", "site": "https://chulkovo-club.ru/", "trails_count": 7, "trail_levels": "зелёные, синие, красные", "lifts_count": 4, "rescue_phone": "+74955842222"},
    {"name": "Лоза", "lat": 56.3000, "lon": 38.1330, "address": "Московская область", "site": "https://loza-ski.ru/", "trails_count": 4, "trail_levels": "зелёные, синие", "lifts_count": 2, "rescue_phone": None},
    # САНКТ-ПЕТЕРБУРГ И ОБЛАСТЬ
    {"name": "Охта-Парк", "lat": 60.0906, "lon": 30.3894, "address": "Санкт-Петербург", "site": "https://ohta-park.ru/", "trails_count": 10, "trail_levels": "зелёные, синие, красные", "lifts_count": 6, "rescue_phone": "+78123356666"},
    {"name": "Игора", "lat": 60.5189, "lon": 30.1997, "address": "Ленинградская область", "site": "https://igora.ru/", "trails_count": 15, "trail_levels": "зелёные, синие, красные, чёрные", "lifts_count": 8, "rescue_phone": "+78124565900"},
    {"name": "Северный склон", "lat": 60.0415, "lon": 30.3749, "address": "Санкт-Петербург", "site": "https://sevsklon.ru/", "trails_count": 6, "trail_levels": "зелёные, синие", "lifts_count": 3, "rescue_phone": "+78129241111"},
    {"name": "Туутари-Парк", "lat": 59.7006, "lon": 30.2003, "address": "Ленинградская область", "site": "https://tuutari-park.ru/", "trails_count": 5, "trail_levels": "зелёные, синие", "lifts_count": 3, "rescue_phone": "+78127770170"},
    {"name": "Золотая Долина", "lat": 60.5560, "lon": 29.7200, "address": "Ленинградская область", "site": "https://zolotaya-dolina.ru/", "trails_count": 12, "trail_levels": "зелёные, синие, красные", "lifts_count": 6, "rescue_phone": "+78137841111"},
    # УРАЛ
    {"name": "Гора Белая", "lat": 57.4936, "lon": 59.9375, "address": "Свердловская область", "site": "https://ski-gora-belaya.ru/", "trails_count": 7, "trail_levels": "зелёные, синие, красные", "lifts_count": 5, "rescue_phone": "+73435070707"},
    {"name": "Уктус", "lat": 56.7793, "lon": 60.6416, "address": "Екатеринбург", "site": "https://uktus.com/", "trails_count": 5, "trail_levels": "зелёные, синие", "lifts_count": 4, "rescue_phone": "+73433898989"},
    {"name": "Пильная", "lat": 56.9300, "lon": 59.9500, "address": "Свердловская область", "site": "https://pilnaya.ru/", "trails_count": 6, "trail_levels": "зелёные, синие", "lifts_count": 3, "rescue_phone": None},
    # ЧЕЛЯБИНСКАЯ ОБЛАСТЬ
    {"name": "Солнечная Долина", "lat": 54.9857, "lon": 60.2217, "address": "Челябинская область", "site": "https://solnechnaya-dolina.com/", "trails_count": 12, "trail_levels": "зелёные, синие, красные, чёрные", "lifts_count": 8, "rescue_phone": "+73519777777"},
    {"name": "Банное (Металлург-Магнитогорск)", "lat": 53.5900, "lon": 58.9700, "address": "Челябинская область", "site": "https://ski-bannoe.ru/", "trails_count": 6, "trail_levels": "синие, красные", "lifts_count": 4, "rescue_phone": "+73473633333"},
    # БАШКОРТОСТАН
    {"name": "Абзаково", "lat": 53.8200, "lon": 58.6000, "address": "Башкортостан", "site": "https://abzakovo.com/", "trails_count": 13, "trail_levels": "зелёные, синие, красные, чёрные", "lifts_count": 9, "rescue_phone": "+73519579600"},
    # СОЧИ
    {"name": "Роза Хутор", "lat": 43.6570, "lon": 40.2970, "address": "Сочи, Краснодарский край", "site": "https://roza-khutor.com/", "trails_count": 105, "trail_levels": "зелёные, синие, красные, чёрные", "lifts_count": 32, "rescue_phone": "+78622437100"},
    {"name": "Газпром Лаура", "lat": 43.6628, "lon": 40.2665, "address": "Сочи, Краснодарский край", "site": "https://polyanaski.ru/", "trails_count": 35, "trail_levels": "зелёные, синие, красные", "lifts_count": 10, "rescue_phone": "+78622437000"},
    {"name": "Красная Поляна", "lat": 43.6730, "lon": 40.2710, "address": "Сочи, Краснодарский край", "site": "https://krasnayapolyanaresort.ru/", "trails_count": 30, "trail_levels": "зелёные, синие, красные, чёрные", "lifts_count": 13, "rescue_phone": "+78622437200"},
    # КЕМЕРОВСКАЯ ОБЛАСТЬ
    {"name": "Шерегеш", "lat": 52.9150, "lon": 87.9850, "address": "Кемеровская область", "site": "https://sheregesh.su/", "trails_count": 40, "trail_levels": "зелёные, синие, красные, чёрные", "lifts_count": 19, "rescue_phone": "+73845337911"},
    # КАРАЧАЕВО-ЧЕРКЕСИЯ
    {"name": "Архыз", "lat": 43.5600, "lon": 41.2200, "address": "Карачаево-Черкесия", "site": "https://arhyz-resort.ru/", "trails_count": 15, "trail_levels": "зелёные, синие, красные", "lifts_count": 8, "rescue_phone": "+78782226600"},
    {"name": "Домбай", "lat": 43.2880, "lon": 41.6280, "address": "Карачаево-Черкесия", "site": "https://dombaj.ru/", "trails_count": 14, "trail_levels": "синие, красные, чёрные", "lifts_count": 7, "rescue_phone": "+78782259111"},
    # КАБАРДИНО-БАЛКАРИЯ
    {"name": "Эльбрус (Азау)", "lat": 43.2700, "lon": 42.4700, "address": "Кабардино-Балкария", "site": "https://elbrus.su/", "trails_count": 20, "trail_levels": "синие, красные, чёрные", "lifts_count": 7, "rescue_phone": "+78663871899"},
    # МУРМАНСКАЯ ОБЛАСТЬ
    {"name": "Большой Вудъявр", "lat": 67.6120, "lon": 33.6770, "address": "Мурманская область", "site": "https://bigwood.ru/", "trails_count": 25, "trail_levels": "зелёные, синие, красные, чёрные", "lifts_count": 10, "rescue_phone": "+78155332211"},
    # САХАЛИН
    {"name": "Горный Воздух", "lat": 46.9590, "lon": 142.7470, "address": "Сахалин", "site": "https://gornyvozdukh.ru/", "trails_count": 9, "trail_levels": "зелёные, синие, красные", "lifts_count": 5, "rescue_phone": "+74242467777"},
    # КАЗАНЬ
    {"name": "Свияжские Холмы", "lat": 55.7825, "lon": 48.8890, "address": "Татарстан", "site": "https://sviyaga-ski.ru/", "trails_count": 6, "trail_levels": "зелёные, синие, красные", "lifts_count": 4, "rescue_phone": "+78432777700"},
    # НИЖНИЙ НОВГОРОД
    {"name": "Хабарское", "lat": 56.1440, "lon": 44.0900, "address": "Нижегородская область", "site": "https://habarskoe.ru/", "trails_count": 10, "trail_levels": "зелёные, синие, красные", "lifts_count": 5, "rescue_phone": "+78314666000"},
    # НОВОСИБИРСК
    {"name": "Горский", "lat": 54.9840, "lon": 82.9080, "address": "Новосибирск", "site": None, "trails_count": 4, "trail_levels": "зелёные, синие", "lifts_count": 2, "rescue_phone": None},
    # КРАСНОЯРСК
    {"name": "Бобровый Лог", "lat": 55.9680, "lon": 92.7950, "address": "Красноярск", "site": "https://bobrovylog.ru/", "trails_count": 15, "trail_levels": "зелёные, синие, красные, чёрные", "lifts_count": 7, "rescue_phone": "+73912691111"},
]


class Database:
    def __init__(self, path: str) -> None:
        self._path = path

    @asynccontextmanager
    async def connection(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self._path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            await conn.close()

    async def init(self) -> None:
        async with self.connection() as conn:
            await conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_state TEXT
                );

                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    photos TEXT,
                    gender TEXT,
                    ride_type TEXT NOT NULL,
                    skill_level TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    city TEXT NOT NULL,
                    location_lat REAL,
                    location_lon REAL,
                    about TEXT NOT NULL,
                    ride_plan TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(from_user_id, to_user_id),
                    FOREIGN KEY(from_user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(to_user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER NOT NULL,
                    user2_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user1_id, user2_id),
                    FOREIGN KEY(user1_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(user2_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS resorts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    address TEXT,
                    site TEXT,
                    trails_count INTEGER,
                    trail_levels TEXT,
                    lifts_count INTEGER
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER NOT NULL,
                    resort_id INTEGER NOT NULL,
                    event_date TEXT NOT NULL,
                    skill_level TEXT NOT NULL,
                    photo_file_id TEXT,
                    telegram_group_link TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY(creator_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(resort_id) REFERENCES resorts(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS instructors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    telegram_link TEXT NOT NULL,
                    city TEXT NOT NULL,
                    resorts TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS event_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_id INTEGER NOT NULL,
                    remind_at TEXT NOT NULL,
                    sent INTEGER DEFAULT 0,
                    UNIQUE(user_id, event_id),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_profiles_city ON profiles(city);
                CREATE INDEX IF NOT EXISTS idx_profiles_ride_type ON profiles(ride_type);
                CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
                CREATE INDEX IF NOT EXISTS idx_events_resort ON events(resort_id);
                CREATE INDEX IF NOT EXISTS idx_instructors_city ON instructors(city);
                CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON event_reminders(remind_at);
                """
            )
            await conn.commit()
        await self._ensure_new_columns()
        await self._seed_resorts()

    async def _ensure_new_columns(self) -> None:
        async with self.connection() as conn:
            # Profiles columns
            async with conn.execute("PRAGMA table_info(profiles)") as cursor:
                columns = {row["name"] for row in await cursor.fetchall()}
            if "location_lat" not in columns:
                await conn.execute("ALTER TABLE profiles ADD COLUMN location_lat REAL")
            if "location_lon" not in columns:
                await conn.execute("ALTER TABLE profiles ADD COLUMN location_lon REAL")
            if "photos" not in columns:
                await conn.execute("ALTER TABLE profiles ADD COLUMN photos TEXT")
            if "gender" not in columns:
                await conn.execute("ALTER TABLE profiles ADD COLUMN gender TEXT")
            if "ride_plan" not in columns:
                await conn.execute("ALTER TABLE profiles ADD COLUMN ride_plan TEXT")
            
            # Resorts columns
            async with conn.execute("PRAGMA table_info(resorts)") as cursor:
                resort_columns = {row["name"] for row in await cursor.fetchall()}
            if "rescue_phone" not in resort_columns:
                await conn.execute("ALTER TABLE resorts ADD COLUMN rescue_phone TEXT")
            
            await conn.commit()

    async def _seed_resorts(self) -> None:
        async with self.connection() as conn:
            async with conn.execute("SELECT COUNT(*) as cnt FROM resorts") as cursor:
                row = await cursor.fetchone()
                if row["cnt"] >= len(RESORTS_SEED):
                    # Update rescue phones for existing resorts
                    for resort in RESORTS_SEED:
                        if resort.get("rescue_phone"):
                            await conn.execute(
                                "UPDATE resorts SET rescue_phone = ? WHERE name = ?",
                                (resort["rescue_phone"], resort["name"]),
                            )
                    await conn.commit()
                    return
            await conn.execute("DELETE FROM resorts")
            await conn.executemany(
                """
                INSERT INTO resorts (
                    name, lat, lon, address, site,
                    trails_count, trail_levels, lifts_count, rescue_phone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        resort["name"],
                        resort["lat"],
                        resort["lon"],
                        resort.get("address"),
                        resort.get("site"),
                        resort.get("trails_count"),
                        resort.get("trail_levels"),
                        resort.get("lifts_count"),
                        resort.get("rescue_phone"),
                    )
                    for resort in RESORTS_SEED
                ],
            )
            await conn.commit()

    async def upsert_user(self, telegram_id: int, username: str, first_name: str) -> int:
        async with self.connection() as conn:
            await conn.execute(
                """
                INSERT INTO users (telegram_id, username, first_name)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name
                """,
                (telegram_id, username, first_name),
            )
            await conn.commit()
            async with conn.execute(
                "SELECT id FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return row["id"]

    async def get_user_by_id(self, user_id: int) -> Optional[aiosqlite.Row]:
        async with self.connection() as conn:
            async with conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,),
            ) as cursor:
                return await cursor.fetchone()

    async def update_user_state(self, telegram_id: int, state: Optional[str]) -> None:
        async with self.connection() as conn:
            await conn.execute(
                "UPDATE users SET last_state = ? WHERE telegram_id = ?",
                (state, telegram_id),
            )
            await conn.commit()

    async def get_profile(self, user_id: int) -> Optional[aiosqlite.Row]:
        async with self.connection() as conn:
            async with conn.execute(
                """
                SELECT p.*, u.username, u.first_name
                FROM profiles p
                JOIN users u ON u.id = p.user_id
                WHERE p.user_id = ?
                """,
                (user_id,),
            ) as cursor:
                return await cursor.fetchone()

    async def upsert_profile(
        self,
        user_id: int,
        ride_type: str,
        skill_level: str,
        age: int,
        city: str,
        about: str,
        photos: List[str],
        gender: str,
        location_lat: Optional[float],
        location_lon: Optional[float],
    ) -> None:
        photos_json = json.dumps(photos) if photos else None
        async with self.connection() as conn:
            await conn.execute(
                """
                INSERT INTO profiles (
                    user_id, ride_type, skill_level, age, city, about, photos, gender, location_lat, location_lon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    ride_type = excluded.ride_type,
                    skill_level = excluded.skill_level,
                    age = excluded.age,
                    city = excluded.city,
                    about = excluded.about,
                    photos = excluded.photos,
                    gender = excluded.gender,
                    location_lat = excluded.location_lat,
                    location_lon = excluded.location_lon
                """,
                (
                    user_id,
                    ride_type,
                    skill_level,
                    age,
                    city,
                    about,
                    photos_json,
                    gender,
                    location_lat,
                    location_lon,
                ),
            )
            await conn.commit()

    async def update_ride_plan(self, user_id: int, ride_plan: str) -> None:
        async with self.connection() as conn:
            await conn.execute(
                "UPDATE profiles SET ride_plan = ? WHERE user_id = ?",
                (ride_plan, user_id),
            )
            await conn.commit()

    async def clear_ride_plan(self, user_id: int) -> None:
        async with self.connection() as conn:
            await conn.execute(
                "UPDATE profiles SET ride_plan = NULL WHERE user_id = ?",
                (user_id,),
            )
            await conn.commit()

    async def delete_profile(self, user_id: int) -> None:
        async with self.connection() as conn:
            await conn.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
            await conn.commit()

    async def update_profile_location(
        self,
        user_id: int,
        location_lat: float,
        location_lon: float,
    ) -> None:
        async with self.connection() as conn:
            await conn.execute(
                """
                UPDATE profiles
                SET location_lat = ?, location_lon = ?
                WHERE user_id = ?
                """,
                (location_lat, location_lon, user_id),
            )
            await conn.commit()

    async def list_resorts(self) -> Iterable[aiosqlite.Row]:
        async with self.connection() as conn:
            async with conn.execute("SELECT * FROM resorts") as cursor:
                return await cursor.fetchall()

    async def get_resort(self, resort_id: int) -> Optional[aiosqlite.Row]:
        async with self.connection() as conn:
            async with conn.execute(
                "SELECT * FROM resorts WHERE id = ?",
                (resort_id,),
            ) as cursor:
                return await cursor.fetchone()

    async def get_resort_cities(self) -> List[str]:
        """Get list of unique cities with resorts."""
        async with self.connection() as conn:
            async with conn.execute(
                "SELECT DISTINCT address FROM resorts WHERE address IS NOT NULL ORDER BY address"
            ) as cursor:
                rows = await cursor.fetchall()
                return [row["address"] for row in rows]

    async def get_resorts_by_city(self, city: str) -> Iterable[aiosqlite.Row]:
        """Get resorts in a specific city."""
        async with self.connection() as conn:
            async with conn.execute(
                "SELECT * FROM resorts WHERE address LIKE ? ORDER BY name",
                (f"%{city}%",),
            ) as cursor:
                return await cursor.fetchall()

    async def get_all_profiles(self, current_user_id: int) -> Iterable[aiosqlite.Row]:
        """Get all profiles (excluding current user)."""
        async with self.connection() as conn:
            async with conn.execute(
                """
                SELECT p.*, u.username, u.first_name
                FROM profiles p
                JOIN users u ON u.id = p.user_id
                WHERE p.user_id != ?
                ORDER BY p.id DESC
                """,
                (current_user_id,),
            ) as cursor:
                return await cursor.fetchall()

    async def update_about(self, user_id: int, about: str) -> None:
        """Update profile description."""
        async with self.connection() as conn:
            await conn.execute(
                "UPDATE profiles SET about = ? WHERE user_id = ?",
                (about, user_id),
            )
            await conn.commit()

    async def add_like(self, from_user_id: int, to_user_id: int) -> None:
        async with self.connection() as conn:
            await conn.execute(
                """
                INSERT OR IGNORE INTO likes (from_user_id, to_user_id)
                VALUES (?, ?)
                """,
                (from_user_id, to_user_id),
            )
            await conn.commit()

    async def has_like(self, from_user_id: int, to_user_id: int) -> bool:
        async with self.connection() as conn:
            async with conn.execute(
                """
                SELECT 1 FROM likes
                WHERE from_user_id = ? AND to_user_id = ?
                """,
                (from_user_id, to_user_id),
            ) as cursor:
                return await cursor.fetchone() is not None

    async def add_match(self, user1_id: int, user2_id: int) -> None:
        user_low = min(user1_id, user2_id)
        user_high = max(user1_id, user2_id)
        async with self.connection() as conn:
            await conn.execute(
                """
                INSERT OR IGNORE INTO matches (user1_id, user2_id)
                VALUES (?, ?)
                """,
                (user_low, user_high),
            )
            await conn.commit()

    async def get_already_liked(self, user_id: int) -> set:
        """Get set of user IDs that current user has already liked."""
        async with self.connection() as conn:
            async with conn.execute(
                "SELECT to_user_id FROM likes WHERE from_user_id = ?",
                (user_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return {row["to_user_id"] for row in rows}

    async def get_user_matches(self, user_id: int) -> Iterable[aiosqlite.Row]:
        """Get all mutual matches for a user."""
        async with self.connection() as conn:
            async with conn.execute(
                """
                SELECT u.*, p.ride_type, p.skill_level, p.city, p.about
                FROM matches m
                JOIN users u ON (
                    (m.user1_id = ? AND u.id = m.user2_id)
                    OR (m.user2_id = ? AND u.id = m.user1_id)
                )
                LEFT JOIN profiles p ON p.user_id = u.id
                ORDER BY m.created_at DESC
                """,
                (user_id, user_id),
            ) as cursor:
                return await cursor.fetchall()

    # ═══════════════════════════════════════════════════════════════════
    # EVENTS
    # ═══════════════════════════════════════════════════════════════════

    async def create_event(
        self,
        creator_id: int,
        resort_id: int,
        event_date: str,
        skill_level: str,
        telegram_group_link: str,
        photo_file_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> int:
        async with self.connection() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO events (
                    creator_id, resort_id, event_date, skill_level,
                    telegram_group_link, photo_file_id, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (creator_id, resort_id, event_date, skill_level, telegram_group_link, photo_file_id, description),
            )
            await conn.commit()
            return cursor.lastrowid

    async def get_active_events(self) -> Iterable[aiosqlite.Row]:
        """Get all active events with resort info."""
        async with self.connection() as conn:
            async with conn.execute(
                """
                SELECT e.*, r.name as resort_name, r.address as resort_address,
                       u.first_name as creator_name, u.username as creator_username
                FROM events e
                JOIN resorts r ON r.id = e.resort_id
                JOIN users u ON u.id = e.creator_id
                WHERE e.is_active = 1 AND e.event_date >= date('now')
                ORDER BY e.event_date ASC
                """,
            ) as cursor:
                return await cursor.fetchall()

    async def get_event(self, event_id: int) -> Optional[aiosqlite.Row]:
        async with self.connection() as conn:
            async with conn.execute(
                """
                SELECT e.*, r.name as resort_name, r.address as resort_address,
                       u.first_name as creator_name, u.username as creator_username
                FROM events e
                JOIN resorts r ON r.id = e.resort_id
                JOIN users u ON u.id = e.creator_id
                WHERE e.id = ?
                """,
                (event_id,),
            ) as cursor:
                return await cursor.fetchone()

    async def get_user_events(self, user_id: int) -> Iterable[aiosqlite.Row]:
        """Get events created by user."""
        async with self.connection() as conn:
            async with conn.execute(
                """
                SELECT e.*, r.name as resort_name
                FROM events e
                JOIN resorts r ON r.id = e.resort_id
                WHERE e.creator_id = ? AND e.is_active = 1
                ORDER BY e.event_date ASC
                """,
                (user_id,),
            ) as cursor:
                return await cursor.fetchall()

    async def deactivate_event(self, event_id: int) -> None:
        async with self.connection() as conn:
            await conn.execute("UPDATE events SET is_active = 0 WHERE id = ?", (event_id,))
            await conn.commit()

    # ═══════════════════════════════════════════════════════════════════
    # INSTRUCTORS
    # ═══════════════════════════════════════════════════════════════════

    async def add_instructor(
        self,
        name: str,
        telegram_link: str,
        city: str,
        resorts: str,
    ) -> int:
        async with self.connection() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO instructors (name, telegram_link, city, resorts)
                VALUES (?, ?, ?, ?)
                """,
                (name, telegram_link, city, resorts),
            )
            await conn.commit()
            return cursor.lastrowid

    async def get_instructor_cities(self) -> List[str]:
        """Get unique cities with instructors."""
        async with self.connection() as conn:
            async with conn.execute(
                "SELECT DISTINCT city FROM instructors ORDER BY city"
            ) as cursor:
                rows = await cursor.fetchall()
                return [row["city"] for row in rows]

    async def get_instructors_by_city(self, city: str) -> Iterable[aiosqlite.Row]:
        """Get instructors in a specific city."""
        async with self.connection() as conn:
            async with conn.execute(
                "SELECT * FROM instructors WHERE city = ? ORDER BY name",
                (city,),
            ) as cursor:
                return await cursor.fetchall()

    async def delete_instructor(self, instructor_id: int) -> None:
        async with self.connection() as conn:
            await conn.execute("DELETE FROM instructors WHERE id = ?", (instructor_id,))
            await conn.commit()

    # ═══════════════════════════════════════════════════════════════════
    # REMINDERS
    # ═══════════════════════════════════════════════════════════════════

    async def add_event_reminder(self, user_id: int, event_id: int, remind_at: str) -> None:
        """Add a reminder for an event."""
        async with self.connection() as conn:
            await conn.execute(
                """
                INSERT OR IGNORE INTO event_reminders (user_id, event_id, remind_at)
                VALUES (?, ?, ?)
                """,
                (user_id, event_id, remind_at),
            )
            await conn.commit()

    async def get_pending_reminders(self, current_time: str) -> Iterable[aiosqlite.Row]:
        """Get reminders that need to be sent."""
        async with self.connection() as conn:
            async with conn.execute(
                """
                SELECT r.*, e.event_date, e.telegram_group_link, 
                       rs.name as resort_name, u.telegram_id
                FROM event_reminders r
                JOIN events e ON e.id = r.event_id
                JOIN resorts rs ON rs.id = e.resort_id
                JOIN users u ON u.id = r.user_id
                WHERE r.sent = 0 AND r.remind_at <= ? AND e.is_active = 1
                """,
                (current_time,),
            ) as cursor:
                return await cursor.fetchall()

    async def mark_reminder_sent(self, reminder_id: int) -> None:
        async with self.connection() as conn:
            await conn.execute(
                "UPDATE event_reminders SET sent = 1 WHERE id = ?",
                (reminder_id,),
            )
            await conn.commit()

    async def get_user_reminders(self, user_id: int) -> Iterable[aiosqlite.Row]:
        """Get user's active reminders."""
        async with self.connection() as conn:
            async with conn.execute(
                """
                SELECT r.*, e.event_date, rs.name as resort_name
                FROM event_reminders r
                JOIN events e ON e.id = r.event_id
                JOIN resorts rs ON rs.id = e.resort_id
                WHERE r.user_id = ? AND r.sent = 0 AND e.is_active = 1
                ORDER BY r.remind_at
                """,
                (user_id,),
            ) as cursor:
                return await cursor.fetchall()

    async def cleanup_old_events(self) -> int:
        """Deactivate events older than 7 days. Returns count of deactivated."""
        async with self.connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE events 
                SET is_active = 0 
                WHERE is_active = 1 AND date(event_date) < date('now', '-7 days')
                """
            )
            await conn.commit()
            return cursor.rowcount

    # ═══════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════

    async def get_stats(self) -> dict:
        async with self.connection() as conn:
            stats = {}
            async with conn.execute("SELECT COUNT(*) as cnt FROM users") as cursor:
                stats["users"] = (await cursor.fetchone())["cnt"]
            async with conn.execute("SELECT COUNT(*) as cnt FROM profiles") as cursor:
                stats["profiles"] = (await cursor.fetchone())["cnt"]
            async with conn.execute("SELECT COUNT(*) as cnt FROM matches") as cursor:
                stats["matches"] = (await cursor.fetchone())["cnt"]
            async with conn.execute("SELECT COUNT(*) as cnt FROM likes") as cursor:
                stats["likes"] = (await cursor.fetchone())["cnt"]
            async with conn.execute("SELECT COUNT(*) as cnt FROM events WHERE is_active = 1") as cursor:
                stats["events"] = (await cursor.fetchone())["cnt"]
            return stats
