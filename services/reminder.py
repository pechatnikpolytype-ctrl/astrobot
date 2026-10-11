"""Reminder service with multilang support."""
import asyncio
import logging
import random
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.postgres_db import (
    get_users_for_reminder, set_last_reminder,
    should_send_reminder, get_reminder_settings,
    get_user_lang_cached,
)
from config import MULTILANG_ENABLED
from locales import t

logger = logging.getLogger(__name__)


REMINDER_KEYS = ["REMINDER_1", "REMINDER_2", "REMINDER_3", "REMINDER_4"]


def _build_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("REMINDER_BTN_FILL", lang),
            callback_data="profile_edit"
        )],
        [InlineKeyboardButton(
            text=t("BTN_BACK_MENU", lang),
            callback_data="main_menu"
        )],
    ])


async def _lang_safe(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


async def send_reminders(bot: Bot):
    settings = await get_reminder_settings()
    if not settings.get("enabled", True):
        logger.info("Reminders disabled")
        return

    users = await get_users_for_reminder(limit=200)
    if not users:
        logger.info("No users for reminders")
        return

    logger.info(f"Sending reminders: {len(users)} users")

    sent = 0
    failed = 0

    for user in users:
        user_id = user["user_id"]
        try:
            if not await should_send_reminder(user_id):
                continue

            lang = await _lang_safe(user_id)
            key = random.choice(REMINDER_KEYS)
            text = t(key, lang)
            await bot.send_message(user_id, text, reply_markup=_build_keyboard(lang))
            await set_last_reminder(user_id)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            logger.debug(f"Reminder fail {user_id}: {e}")

    logger.info(f"Reminders: sent={sent}, failed={failed}")


async def send_test_reminder(bot: Bot, user_id: int):
    lang = await _lang_safe(user_id)
    key = random.choice(REMINDER_KEYS)
    text = t(key, lang)
    try:
        await bot.send_message(user_id, f"\U0001F9EA {text}", reply_markup=_build_keyboard(lang))
        return True
    except Exception as e:
        logger.error(f"Test reminder error: {e}")
        return False
