"""Horoscope handler with multilang support."""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.main import back_to_menu_keyboard
from ai_service_n1n import ai_service
from database.postgres_db import get_daily_horoscope, set_daily_horoscope, get_user_lang_cached, get_user
from config import MULTILANG_ENABLED
from locales import t

logger = logging.getLogger(__name__)
router = Router()


async def _lang(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


@router.callback_query(F.data == "daily_horoscope")
async def daily_horoscope_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    today_str = datetime.now().strftime("%d.%m.%Y")

    # Получаем знак из профиля
    sign = ""
    try:
        user = await get_user(user_id)
        if user and user.get("birth_date"):
            bd = _dt.strptime(user["birth_date"], "%Y-%m-%d")
            sign = AstrologyCalculator.get_zodiac_sign(bd) or ""
    except Exception as _e:
        logger.warning(f"sign detect failed: {_e}")

    cached = await get_daily_horoscope(sign=sign, lang=lang)
    if cached:
        logger.info(t("HOROSCOPE_CACHE_LOG", lang))
        try:
            await callback.message.edit_text(
                cached, reply_markup=back_to_menu_keyboard(lang)
            )
        except Exception:
            await callback.message.answer(
                cached, reply_markup=back_to_menu_keyboard(lang)
            )
        return

    processing_msg = None
    try:
        processing_msg = await callback.message.edit_text(t("HOROSCOPE_PROCESSING", lang))
    except Exception:
        processing_msg = await callback.message.answer(t("HOROSCOPE_PROCESSING", lang))

    try:
        text = await ai_service.generate_horoscope(sign=sign, lang=lang)
    except TypeError:
        try:
            text = await ai_service.generate_horoscope(sign=sign, lang=lang)
        except Exception as e:
            logger.error(f"horoscope error: {e}")
            text = None
    except Exception as e:
        logger.error(f"horoscope error: {e}")
        text = None

    if text:
        await set_daily_horoscope(text, sign=sign, lang=lang)
        logger.info(f"new horoscope saved: {len(text)} chars")
    else:
        logger.warning("horoscope fallback")
        fallback = (
            t("HOROSCOPE_FALLBACK_TITLE", lang) + "\n\n"
            + today_str + "\n\n"
            + t("HOROSCOPE_FALLBACK_TEXT", lang)
        )
        text = fallback

    try:
        await processing_msg.edit_text(text, reply_markup=back_to_menu_keyboard(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_menu_keyboard(lang))
