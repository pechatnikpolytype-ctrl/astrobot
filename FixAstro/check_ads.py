#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Диагностика рекламы."""
import asyncio
import os
import sys

sys.path.insert(0, r"C:\Users\User\Desktop\AstroBot_clean")
os.chdir(r"C:\Users\User\Desktop\AstroBot_clean")

from dotenv import load_dotenv
load_dotenv()

from database.postgres_db import (
    init_postgres_db, get_ads_config, get_all_ads,
    should_show_ad, pick_random_ad,
)


async def main():
    print("=" * 60)
    print("ДИАГНОСТИКА РЕКЛАМЫ")
    print("=" * 60)

    await init_postgres_db()
    print()

    # 1. Config
    config = await get_ads_config()
    print("📋 Настройки:")
    for k, v in config.items():
        print(f"  • {k}: {v}")
    print()

    # 2. Ads
    ads = await get_all_ads()
    print(f"📢 Всего блоков: {len(ads)}")
    for a in ads:
        status = "✅" if a["enabled"] else "❌"
        print(f"  {status} #{a['id']} — {a['text'][:40]}...")
        print(f"     link: {a.get('link')}")
        print(f"     link_mode: {a.get('link_mode')}")
    print()

    # 3. should_show_ad для тестового юзера
    test_user = 1079935212  # замени на свой
    show = await should_show_ad(test_user)
    print(f"🔎 should_show_ad({test_user}): {show}")

    # 4. pick_random_ad
    ad = await pick_random_ad()
    if ad:
        print(f"🎯 pick_random_ad: #{ad['id']} — {ad['text'][:40]}...")
    else:
        print(f"🎯 pick_random_ad: (нет активных блоков)")

    print()
    print("=" * 60)


asyncio.run(main())