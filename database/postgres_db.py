import asyncpg
import logging
import json
from datetime import datetime, timedelta
from config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, FREE_MODE
)

logger = logging.getLogger(__name__)


class Database:
    pool = None

    @classmethod
    async def create_pool(cls):
        if cls.pool is None:
            cls.pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=int(DB_PORT),
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                min_size=1,
                max_size=5,
                ssl="require",
                statement_cache_size=0,
            )
            logger.info("✅ Пул соединений с PostgreSQL создан.")
        return cls.pool

    @classmethod
    async def close_pool(cls):
        if cls.pool:
            await cls.pool.close()
            cls.pool = None
            logger.info("Пул соединений закрыт.")


db = Database()


# ============================================================
# НАСТРОЙКИ ПО УМОЛЧАНИЮ
# ============================================================
DEFAULT_PRICING = {
    "7":  {"days": 7,  "stars": 99},
    "30": {"days": 30, "stars": 299},
    "90": {"days": 90, "stars": 699},
}

DEFAULT_TRIAL = {
    "enabled": True,
    "days": 1,
}


async def init_postgres_db():
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                birth_date TEXT,
                birth_time TEXT,
                birth_place TEXT,
                is_paid BOOLEAN DEFAULT FALSE,
                subscription_end TEXT,
                trial_used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                stars_paid INTEGER NOT NULL,
                payment_id TEXT UNIQUE NOT NULL,
                days INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Инициализация цен
        existing = await conn.fetchval(
            "SELECT value FROM settings WHERE key = 'pricing'"
        )
        if not existing:
            await conn.execute(
                "INSERT INTO settings (key, value) VALUES ($1, $2)",
                "pricing", json.dumps(DEFAULT_PRICING, ensure_ascii=False)
            )

        # Инициализация триала
        existing = await conn.fetchval(
            "SELECT value FROM settings WHERE key = 'trial'"
        )
        if not existing:
            await conn.execute(
                "INSERT INTO settings (key, value) VALUES ($1, $2)",
                "trial", json.dumps(DEFAULT_TRIAL, ensure_ascii=False)
            )

    logger.info("✅ Таблицы в PostgreSQL созданы/обновлены")


# ============================================================
# USERS
# ============================================================
async def create_user(user_id: int, username: str = "", first_name: str = ""):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id, username, first_name)


async def get_user(user_id: int):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(row) if row else None


async def update_birth_data(user_id: int, birth_date: str, birth_time: str, birth_place: str):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET birth_date = $2, birth_time = $3, birth_place = $4
            WHERE user_id = $1
        """, user_id, birth_date, birth_time, birth_place)


async def set_subscription(user_id: int, days: int):
    end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET is_paid = TRUE, subscription_end = $2 WHERE user_id = $1
        """, user_id, end_date)


async def is_paid(user_id: int) -> bool:
    if FREE_MODE:
        return True

    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT is_paid, subscription_end FROM users WHERE user_id = $1",
            user_id,
        )
    if not row:
        return False
    today = datetime.now().strftime("%Y-%m-%d")
    if row["is_paid"] and row["subscription_end"] and today <= row["subscription_end"]:
        return True
    if row["is_paid"] and row["subscription_end"] and today > row["subscription_end"]:
        pool = await db.create_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET is_paid = FALSE WHERE user_id = $1", user_id
            )
        return False
    return False


async def has_trial_used(user_id: int) -> bool:
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT trial_used FROM users WHERE user_id = $1", user_id
        )
        return row["trial_used"] if row else False


async def set_trial_used(user_id: int):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET trial_used = TRUE WHERE user_id = $1", user_id
        )


async def reset_all_trials():
    """Сбрасывает флаг trial_used у всех пользователей."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("UPDATE users SET trial_used = FALSE")
    return result


async def count_trial_used() -> int:
    """Сколько пользователей уже использовали триал."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE trial_used = TRUE")
    return count or 0


async def add_payment(user_id: int, stars_paid: int, payment_id: str, days: int = 0):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO payments (user_id, stars_paid, payment_id, days)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (payment_id) DO NOTHING
        """, user_id, stars_paid, payment_id, days)


async def get_stats():
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
        paid = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_paid = TRUE")
        total_stars = await conn.fetchval("SELECT COALESCE(SUM(stars_paid), 0) FROM payments")
        total_payments = await conn.fetchval("SELECT COUNT(*) FROM payments")
    return {
        "total_users": total or 0,
        "paid_users": paid or 0,
        "free_users": (total or 0) - (paid or 0),
        "total_stars": total_stars or 0,
        "total_payments": total_payments or 0,
    }


# ============================================================
# SETTINGS
# ============================================================
async def get_setting(key: str, default=None):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT value FROM settings WHERE key = $1", key)
    if val is None:
        return default
    try:
        return json.loads(val)
    except Exception:
        return val


async def set_setting(key: str, value):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO settings (key, value, updated_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE
            SET value = $2, updated_at = CURRENT_TIMESTAMP
        """, key, json.dumps(value, ensure_ascii=False))


# ============================================================
# PRICING
# ============================================================
async def get_pricing() -> dict:
    data = await get_setting("pricing", DEFAULT_PRICING)
    if not isinstance(data, dict):
        return DEFAULT_PRICING
    return data


async def set_pricing(pricing: dict):
    await set_setting("pricing", pricing)


# ============================================================
# TRIAL
# ============================================================
async def get_trial() -> dict:
    data = await get_setting("trial", DEFAULT_TRIAL)
    if not isinstance(data, dict):
        return DEFAULT_TRIAL
    if "enabled" not in data:
        data["enabled"] = True
    if "days" not in data:
        data["days"] = 1
    return data


async def set_trial(enabled: bool, days: int):
    await set_setting("trial", {"enabled": enabled, "days": days})
