# -*- coding: utf-8 -*-
"""Diagnostic + fix."""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from config import ADMINS as CFG_ADMINS

print("=" * 60)
print("1. ADMINS from config:")
print(f"   {CFG_ADMINS}")

MY_ID = 1079935212
print(f"   My ID in ADMINS: {MY_ID in CFG_ADMINS}")

# ============================================================
# 2. Проверка lang в БД
# ============================================================
from database.postgres_db import db

async def main():
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        # Моя запись
        row = await conn.fetchrow(
            "SELECT user_id, language, is_paid FROM users WHERE user_id = $1", MY_ID
        )
        print()
        print("2. My user row:")
        print(f"   {dict(row) if row else 'NOT FOUND'}")

        # Факты в БД
        facts = await conn.fetch(
            "SELECT key FROM settings WHERE key LIKE 'daily_fact%' ORDER BY key"
        )
        print()
        print("3. daily_fact keys in settings:")
        for f in facts:
            print(f"   {f['key']}")

        # Совместимость кэш
        compat = await conn.fetch(
            "SELECT COUNT(*) as n FROM settings WHERE key LIKE 'compat%'"
        )
        print()
        print(f"4. compat_* keys in cache: {compat[0]['n']}")

asyncio.run(main())

# ============================================================
# 3. Проверка is_admin
# ============================================================
async def test_admin():
    from database.postgres_db import is_admin
    result = await is_admin(MY_ID)
    print()
    print(f"5. is_admin({MY_ID}): {result}")

asyncio.run(test_admin())