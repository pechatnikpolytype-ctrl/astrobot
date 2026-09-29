#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AstroBot — webhook-версия для продакшена (Render).
Запускается через Flask + webhook от Telegram.
"""

import os
import logging
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from config import BOT_TOKEN
from loader import setup_bot
from database.postgres_db import init_postgres_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --- Flask ---
app = Flask(__name__)

# --- Bot + Dispatcher ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

dp.include_router(start_router)
dp.include_router(ai_router)
dp.include_router(natal_router)
dp.include_router(admin_router)
dp.include_router(horoscope_router)
dp.include_router(compatibility_router)
dp.include_router(profile_router)
dp.include_router(pdf_router)
dp.include_router(payment_router)

# --- Глобальный цикл событий ---
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


@app.route("/webhook", methods=["POST"])
def webhook():
    """Приём обновлений от Telegram."""
    try:
        data = request.get_json(force=True)
        update = Update.model_validate(data, context={"bot": bot})
        future = asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
        future.result(timeout=30)
        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return "Error", 500


@app.route("/health")
def health():
    """Эндпоинт для UptimeRobot."""
    return "OK", 200


@app.route("/")
def home():
    return "AstroBot is running!", 200


async def setup_webhook():
    logger.info("Инициализация PostgreSQL...")
    await init_postgres_db()

    # URL берём из переменной окружения или Render
    external_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not external_url:
        external_url = os.environ.get("WEBHOOK_URL", "").rstrip("/")

    if not external_url:
        logger.warning("⚠️ RENDER_EXTERNAL_URL не установлен — webhook не установится!")
        return

    webhook_url = f"{external_url}/webhook"
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(webhook_url)
    logger.info(f"✅ Webhook установлен: {webhook_url}")


def run_event_loop():
    """Запускает asyncio-loop в отдельном потоке."""
    loop.run_forever()


if __name__ == "__main__":
    import threading

    # 1. Инициализация БД + установка webhook
    loop.run_until_complete(setup_webhook())

    # 2. Запуск asyncio-loop в фоне
    threading.Thread(target=run_event_loop, daemon=True).start()

    # 3. Flask слушает порт
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"✅ Flask запущен на порту {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
