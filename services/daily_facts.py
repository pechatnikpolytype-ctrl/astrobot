"""Daily facts service with multilang support."""
import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.postgres_db import (
    get_daily_fact_settings, get_today_fact, set_today_fact,
    save_fact_history, get_all_users, get_user_lang_cached,
)
from config import MULTILANG_ENABLED
from locales import t

logger = logging.getLogger(__name__)


FACT_KEYS = [f"DAILY_FACT_{i}" for i in range(1, 21)]


def _build_fact_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("DAILY_FACT_BTN_MORE", lang), callback_data="ai_question")],
        [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
    ])


async def _lang_safe(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


async def generate_fact(lang: str = "ru") -> str:
    try:
        from ai_service_n1n import ai_service
        lang_name = {"ru": "Russian", "en": "English", "de": "German"}.get(lang, "Russian")
        system_prompt = (
            "You are an astrologer-educator. Invent ONE interesting fact about astrology.\n"
            "Requirements:\n"
            "- 3-4 sentences\n"
            "- NO markdown (**, __, `)\n"
            "- Emoji at the start\n"
            f"- IMPORTANT: Answer ONLY in {lang_name}\n"
        )
        user_prompt = f"Come up with an interesting fact about astrology in {lang_name}."
        text = await ai_service._query_ai(system_prompt, user_prompt, max_tokens=400)
        if text:
            text = ai_service._clean_response(text)
            logger.info(f"AI fact: {len(text)} chars, lang={lang}")
            return text
    except Exception as e:
        logger.error(f"AI fact error: {e}")

    # Fallback: random from locales
    key = random.choice(FACT_KEYS)
    return t(key, lang)


async def send_daily_facts(bot: Bot):
    settings = await get_daily_fact_settings()
    if not settings.get("enabled", True):
        logger.info("Daily facts disabled")
        return

    # Prepare AI facts for all 3 languages (each cached separately)
    facts_by_lang = {}
    for lang in ["ru", "en", "de"]:
        cached = await get_today_fact(lang)
        if cached and cached.get("text"):
            facts_by_lang[lang] = cached["text"]
            logger.info(f"Fact from cache: {lang}")
        else:
            fact_text = await generate_fact(lang)
            if fact_text:
                await set_today_fact(fact_text, lang)
                facts_by_lang[lang] = fact_text
                if lang == "ru":
                    await save_fact_history(fact_text)
                logger.info(f"New fact: {lang}")

    if not facts_by_lang:
        logger.warning("No facts generated")
        return

    users = await get_all_users()
    if not users:
        return

    logger.info(f"Sending facts: {len(users)} users")

    sent = 0
    failed = 0
    for user in users:
        user_id = user["user_id"]
        try:
            lang = await _lang_safe(user_id)
            fact_text = facts_by_lang.get(lang) or facts_by_lang.get("ru")
            if not fact_text:
                continue

            divider = "\u2501" * 24
            text = (
                f"{t('DAILY_FACT_HEADER', lang)}\n\n"
                f"{fact_text}\n\n"
                f"{divider}\n"
                f"{t('DAILY_FACT_FOOTER', lang)}"
            )
            await bot.send_message(user_id, text, reply_markup=_build_fact_keyboard(lang))
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            logger.debug(f"Fact fail {user_id}: {e}")

    logger.info(f"Facts: sent={sent}, failed={failed}")


async def send_test_fact(bot: Bot, user_id: int):
    lang = await _lang_safe(user_id)
    fact_text = await generate_fact(lang)
    if not fact_text:
        return False
    text = f"{t('DAILY_FACT_TEST_PREFIX', lang)}\n\n{fact_text}"
    try:
        await bot.send_message(user_id, text, reply_markup=_build_fact_keyboard(lang))
        return True
    except Exception as e:
        logger.error(f"Test fact error: {e}")
        return False
