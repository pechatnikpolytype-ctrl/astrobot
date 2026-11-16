#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Диагностика payments + pricing."""
import asyncio
import os
import sys

sys.path.insert(0, r"C:\Users\User\Desktop\AstroBot_clean")
os.chdir(r"C:\Users\User\Desktop\AstroBot_clean")

from dotenv import load_dotenv
load_dotenv()

from database.postgres_db import (
    init_postgres_db, db, get_pricing, get_stats
)


async def main():
    print("=" * 60)
    print("ДИАГНОСТИКА")
    print("=" * 60)

    await init_postgres_db()
    print()

    # 1. Колонки в payments
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        cols = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'payments'
            ORDER BY ordinal_position
        """)
    print("📋 Колонки в payments:")
    for c in cols:
        print(f"  • {c['column_name']} ({c['data_type']})")
    print()

    # 2. Данные в payments
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM payments ORDER BY created_at DESC LIMIT 10")
    print(f"💳 Записей в payments: {len(rows)}")
    for r in rows:
        print(f"  • user_id={r['user_id']}, stars={r['stars_paid']}, days={r.get('days', '?')}, payment_id={r['payment_id']}")
    print()

    # 3. Pricing
    pricing = await get_pricing()
    print("💰 Текущие тарифы (из БД):")
    for plan, info in pricing.items():
        print(f"  • {plan}: {info['days']} дней — {info['stars']} ⭐")
    print()

    # 4. Stats
    stats = await get_stats()
    print("📊 Статистика:")
    for k, v in stats.items():
        print(f"  • {k}: {v}")


asyncio.run(main())