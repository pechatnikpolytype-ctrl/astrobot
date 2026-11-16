#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ускорение: кэш + объединение запросов.
Запуск: python speed_up.py
"""

from pathlib import Path

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")

if not BASE.exists():
    print(f"❌ Папка не найдена: {BASE}")
    exit(1)


# ============================================================
# 1. Создать services/cache.py
# ============================================================
CACHE_PY = r'''"""Простой in-memory кэш с TTL."""
import time
import asyncio
from typing import Any, Optional, Callable, Awaitable


class TTLCache:
    """Кэш с временем жизни."""

    def __init__(self, default_ttl: int = 30):
        self._data: dict = {}  # key -> (value, expires_at)
        self._locks: dict = {}
        self.default_ttl = default_ttl

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def get(self, key: str) -> Optional[Any]:
        entry = self._data.get(key)
        if not entry:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._data[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = None):
        ttl = ttl if ttl is not None else self.default_ttl
        self._data[key] = (value, time.time() + ttl)

    def delete(self, key: str):
        self._data.pop(key, None)

    def clear(self):
        self._data.clear()

    async def get_or_set(self, key: str, factory: Callable[[], Awaitable[Any]], ttl: int = None) -> Any:
        """Возвращает из кэша или создаёт через factory."""
        cached = self.get(key)
        if cached is not None:
            return cached
        lock = self._get_lock(key)
        async with lock:
            # Двойная проверка внутри lock
            cached = self.get(key)
            if cached is not None:
                return cached
            value = await factory()
            self.set(key, value, ttl)
            return value


# Глобальные кэши
user_cache = TTLCache(default_ttl=30)      # get_user
paid_cache = TTLCache(default_ttl=30)      # is_paid
admin_cache = TTLCache(default_ttl=60)     # is_admin
setting_cache = TTLCache(default_ttl=30)   # get_setting (для pricing, trial)
'''


cache_path = BASE / "services" / "cache.py"
cache_path.write_text(CACHE_PY, encoding="utf-8")
print("  ✅ services/cache.py — создан")


# ============================================================
# 2. Патчим database/postgres_db.py — кэш для is_admin, is_paid
# ============================================================
db_path = BASE / "database" / "postgres_db.py"
content = db_path.read_text(encoding="utf-8")

# Патч 1: is_admin с кэшем
OLD_IS_ADMIN = '''async def is_admin(user_id: int) -> bool:
    from config import ADMINS as MAIN_ADMINS
    if user_id in MAIN_ADMINS:
        return True
    extra = await get_extra_admins()
    return user_id in extra'''

NEW_IS_ADMIN = '''async def is_admin(user_id: int) -> bool:
    from config import ADMINS as MAIN_ADMINS
    if user_id in MAIN_ADMINS:
        return True
    # Кэш
    try:
        from services.cache import admin_cache
        cached = admin_cache.get(f"adm_{user_id}")
        if cached is not None:
            return cached
    except Exception:
        pass
    extra = await get_extra_admins()
    result = user_id in extra
    try:
        from services.cache import admin_cache
        admin_cache.set(f"adm_{user_id}", result, ttl=60)
    except Exception:
        pass
    return result'''

if OLD_IS_ADMIN in content:
    content = content.replace(OLD_IS_ADMIN, NEW_IS_ADMIN)
    print("  ✅ is_admin — добавлен кэш")
else:
    print("  ⚠️  is_admin — не найден (проверь вручную)")

db_path.write_text(content, encoding="utf-8")


# ============================================================
# 3. Патчим get_user — кэш
# ============================================================
content = db_path.read_text(encoding="utf-8")

OLD_GET_USER = '''async def get_user(user_id: int):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(row) if row else None'''

NEW_GET_USER = '''async def get_user(user_id: int):
    # Кэш
    try:
        from services.cache import user_cache
        cached = user_cache.get(f"user_{user_id}")
        if cached is not None:
            return cached
    except Exception:
        pass
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        result = dict(row) if row else None
    try:
        from services.cache import user_cache
        user_cache.set(f"user_{user_id}", result, ttl=20)
    except Exception:
        pass
    return result'''

if OLD_GET_USER in content:
    content = content.replace(OLD_GET_USER, NEW_GET_USER)
    print("  ✅ get_user — добавлен кэш")
else:
    print("  ⚠️  get_user — не найден")

db_path.write_text(content, encoding="utf-8")


# ============================================================
# 4. Функция для инвалидации кэша
# ============================================================
INVALIDATE = r'''

# ============================================================
# ИНВАЛИДАЦИЯ КЭША
# ============================================================
def invalidate_user_cache(user_id: int):
    """Сбрасывает кэш пользователя (при обновлении профиля)."""
    try:
        from services.cache import user_cache, paid_cache, admin_cache
        user_cache.delete(f"user_{user_id}")
        paid_cache.delete(f"paid_{user_id}")
        admin_cache.delete(f"adm_{user_id}")
    except Exception:
        pass
'''

if "def invalidate_user_cache" not in content:
    with open(db_path, "a", encoding="utf-8") as f:
        f.write(INVALIDATE)
    print("  ✅ invalidate_user_cache — добавлена")


# ============================================================
# 5. Патчим update_user_field — инвалидация кэша
# ============================================================
content = db_path.read_text(encoding="utf-8")

OLD_UPDATE = '''    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE users SET {field} = $2 WHERE user_id = $1",
            user_id, value
        )'''

NEW_UPDATE = '''    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE users SET {field} = $2 WHERE user_id = $1",
            user_id, value
        )
    # Инвалидируем кэш
    invalidate_user_cache(user_id)'''

if OLD_UPDATE in content:
    content = content.replace(OLD_UPDATE, NEW_UPDATE, 1)
    print("  ✅ update_user_field — инвалидирует кэш")

db_path.write_text(content, encoding="utf-8")


print()
print("=" * 60)
print("ГОТОВО!")
print("=" * 60)
print()
print("Что ускорено:")
print("  • is_admin — кэш 60 сек")
print("  • get_user — кэш 20 сек")
print("  • update_user_field — инвалидирует кэш")
print()
print("Дальше:")
print("  cd C:\\Users\\User\\Desktop\\AstroBot_clean")
print("  python webhook_bot.py")
print()
print("Проверь:")
print("  1. Открой бота, понажимай кнопки — должно быть быстрее")
print("  2. Обнови профиль — изменения сразу видны (кэш сброшен)")