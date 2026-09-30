"""Простой in-memory кэш с TTL."""
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
