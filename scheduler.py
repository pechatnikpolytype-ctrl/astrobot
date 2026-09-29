import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot

logger = logging.getLogger(__name__)


# ============================================================
# УТРЕННИЕ СООБЩЕНИЯ АДМИНАМ
# ============================================================
async def send_morning_message(bot: Bot):
    from config import ADMINS
    text = "🌅 Доброе утро! Бот работает, всё в порядке."
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text)
        except Exception as e:
            logger.error(f"Утреннее сообщение админу {admin_id}: {e}")


# ============================================================
# НАПОМИНАНИЯ ПОЛЬЗОВАТЕЛЯМ
# ============================================================
async def send_daily_reminders(bot: Bot):
    try:
        from services.reminder import send_reminders
        await send_reminders(bot)
    except Exception as e:
        logger.error(f"Ошибка напоминаний: {e}")


# ============================================================
# АВТООЧИСТКА КЭША
# ============================================================
async def daily_cache_cleanup():
    try:
        from database.postgres_db import (
            auto_clean_cache, get_cache_cleanup_settings
        )
        settings = await get_cache_cleanup_settings()
        if not settings.get("enabled", True):
            logger.info("⏸️ Автоочистка отключена")
            return
        await auto_clean_cache()
    except Exception as e:
        logger.error(f"Ошибка автоочистки: {e}")


# ============================================================
# ЕЖЕДНЕВНЫЙ БЭКАП
# ============================================================
async def daily_backup():
    try:
        from backup_db import create_backup
        create_backup()
    except Exception as e:
        logger.error(f"Ошибка бэкапа: {e}")


# ============================================================
# ГЛАВНЫЙ WORKER
# ============================================================
async def scheduler_worker(bot: Bot):
    """Фоновая задача: проверяет время и запускает функции."""
    last_backup_date = None
    last_reminder_date = None
    last_cleanup_date = None
    last_morning_date = None

    logger.info("⏰ Scheduler запущен")

    while True:
        now = datetime.utcnow()

        # 08:00 UTC — утренние сообщения админам
        if now.hour == 8 and now.minute == 0 and last_morning_date != now.date():
            logger.info("⏰ 08:00 UTC — утренние сообщения")
            await send_morning_message(bot)
            last_morning_date = now.date()
            await asyncio.sleep(61)

        # 18:00 UTC — напоминания пользователям
        elif now.hour == 18 and now.minute == 0 and last_reminder_date != now.date():
            logger.info("⏰ 18:00 UTC — напоминания")
            await send_daily_reminders(bot)
            last_reminder_date = now.date()
            await asyncio.sleep(61)

        # 03:00 UTC — автоочистка + бэкап
        elif now.hour == 3 and now.minute == 0 and last_backup_date != now.date():
            logger.info("⏰ 03:00 UTC — бэкап + очистка")
            await daily_cache_cleanup()
            await daily_backup()
            last_backup_date = now.date()
            await asyncio.sleep(61)

        else:
            await asyncio.sleep(30)


async def start_scheduler(bot: Bot):
    """Запускает планировщик как фоновую задачу."""
    logger.info("⏰ Запуск планировщика...")
    asyncio.create_task(scheduler_worker(bot))
