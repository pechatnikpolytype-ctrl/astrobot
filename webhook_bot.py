#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AstroBot — polling-режим.
БЕЗ parse_mode — обычный текст, чтобы не было ошибок парсинга.
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from loader import shutdown_bot
from database.postgres_db import init_postgres_db

# --- Импорт роутеров ---
from handlers.start import router as start_router
from handlers.ai_handler import router as ai_router
from handlers.natal import router as natal_router
from handlers.admin_simple import router as admin_router
from handlers.horoscope import router as horoscope_router
from handlers.compatibility import router as compatibility_router
from handlers.profile import router as profile_router
from handlers.pdf_handler import router as pdf_router
from handlers.payment import router as payment_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("🚀 Запуск AstroBot (polling mode)")

    logger.info("Инициализация PostgreSQL...")
    await init_postgres_db()

    # ⚠️ ВАЖНО: БЕЗ parse_mode!
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(ai_router)
    dp.include_router(natal_router)
    dp.include_router(admin_router)
    dp.include_router(horoscope_router)
    dp.include_router(compatibility_router)
    dp.include_router(profile_router)
    dp.include_router(pdf_router)
    dp.include_router(payment_router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook удалён — работаем через polling")
    except Exception as e:
        logger.warning(f"Webhook warning: {e}")

    logger.info("✅ Бот готов. Пиши /start в Telegram.")
    logger.info("Для остановки нажми Ctrl+C")

    try:
        await dp.start_polling(bot)
    finally:
        await shutdown_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановлено пользователем")
        sys.exit(0)