
# --- Health server для Render (чтобы деплой не висел на "No open ports") ---
import asyncio as _asyncio
import os as _os

async def _start_health_server():
    try:
        from aiohttp import web
        async def _health(request):
            return web.Response(text="OK")
        app = web.Application()
        app.router.add_get("/health", _health)
        app.router.add_get("/", _health)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(_os.environ.get("PORT", "10000"))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(f"[health] listening on 0.0.0.0:{port}/health")
    except Exception as e:
        print(f"[health] failed: {e}")

def _ensure_health_server():
    try:
        loop = _asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_start_health_server())
        else:
            loop.run_until_complete(_start_health_server())
    except Exception as e:
        print(f"[health] ensure failed: {e}")
# --- end health server ---

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AstroBot — long polling версия (без webhook).
Устраняет дублирование update на бесплатном Render.
"""

import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, MULTILANG_ENABLED
from database.postgres_db import init_postgres_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

# Роутеры
from handlers.start import router as start_router
if MULTILANG_ENABLED:
    from handlers.lang import router as lang_router
from handlers.menu_commands import router as menu_router
from handlers.tarot import router as tarot_router
from handlers.mood_diary import router as mood_router
from handlers.admin_ads import router as ads_router
from handlers.ai_handler import router as ai_router
from handlers.natal import router as natal_router
from handlers.admin_simple import router as admin_router
from handlers.horoscope import router as horoscope_router
from handlers.compatibility import router as compatibility_router
from handlers.profile import router as profile_router
from handlers.pdf_handler import router as pdf_router
from handlers.payment import router as payment_router
from handlers.dreams import router as dreams_router

dp.include_router(start_router)
if MULTILANG_ENABLED:
    dp.include_router(lang_router)
dp.include_router(ads_router)
dp.include_router(mood_router)
dp.include_router(menu_router)
dp.include_router(tarot_router)
dp.include_router(ai_router)
dp.include_router(natal_router)
dp.include_router(admin_router)
dp.include_router(horoscope_router)
dp.include_router(compatibility_router)
dp.include_router(profile_router)
dp.include_router(pdf_router)
dp.include_router(payment_router)
dp.include_router(dreams_router)


async def main():
    logger.info("Инициализация PostgreSQL...")
    await init_postgres_db()

    try:
        from scheduler import start_scheduler
        await start_scheduler(bot)
        logger.info("✅ Scheduler запущен")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")

    # Удаляем webhook, иначе polling не запустится
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook удалён, запуск long polling...")

    _ensure_health_server()

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")