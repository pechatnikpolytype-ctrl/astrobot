"""Compatibility handler with multilang support."""
import logging
import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.main import back_to_menu_keyboard, main_menu_keyboard
from database.postgres_db import is_paid, get_setting, set_setting, is_admin, get_user_lang_cached
from config import ADMINS, MULTILANG_ENABLED
from astrology_calculator import AstrologyCalculator, sign_display
from locales import t
from ai_service_n1n import ai_service

logger = logging.getLogger(__name__)
router = Router()


# ZODIAC_SIGNS - multilingual triggers for parse
ZODIAC_KEYS = {
    "Овен": ["овен", "aries", "widder"],
    "Телец": ["телец", "taurus", "stier"],
    "Близнецы": ["близнец", "gemini", "zwilling"],
    "Рак": ["рак", "cancer", "krebs"],
    "Лев": ["лев", "leo", "löwe", "loewe"],
    "Дева": ["дев", "virgo", "jungfrau"],
    "Весы": ["вес", "libra", "waage"],
    "Скорпион": ["скорпион", "scorpio", "skorpion"],
    "Стрелец": ["стрелец", "sagittarius", "schütze", "schuetze"],
    "Козерог": ["козерог", "capricorn", "steinbock"],
    "Водолей": ["водолей", "aquarius", "wassermann"],
    "Рыбы": ["рыб", "pisces", "fische"],
}


class CompatibilityStates(StatesGroup):
    waiting_partner1 = State()
    waiting_partner2 = State()


async def _lang(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


def parse_input(text: str) -> dict:
    """Parse sign name or date. Returns dict with type/value/sign."""
    text_clean = text.strip().lower()

    # Try sign names (all languages)
    for sign_ru, triggers in ZODIAC_KEYS.items():
        for tr in triggers:
            if tr in text_clean:
                return {"type": "sign", "value": sign_ru, "sign": sign_ru}

    # Try date
    from utils.date_parser import parse_date
    ok, iso_date, _ = parse_date(text_clean)
    if ok:
        try:
            date_obj = datetime.strptime(iso_date, "%Y-%m-%d")
            sign = AstrologyCalculator.get_zodiac_sign(date_obj)
            return {"type": "date", "value": iso_date, "sign": sign}
        except Exception:
            pass

    return {"type": None, "value": None, "sign": None}


def build_cache_key(p1: dict, p2: dict, lang: str = "ru") -> str:
    if p1["type"] == "date" and p2["type"] == "date":
        dates = sorted([p1["value"], p2["value"]])
        return f"compat_{dates[0]}_{dates[1]}_{lang}"
    else:
        signs = sorted([p1["sign"].lower(), p2["sign"].lower()])
        return f"compat_{signs[0]}_{signs[1]}_{lang}"


# ============================================================
# Fallback compatibility (uses t)
# ============================================================
ELEMENTS_RU = {
    "Овен": "Огонь", "Лев": "Огонь", "Стрелец": "Огонь",
    "Телец": "Земля", "Дева": "Земля", "Козерог": "Земля",
    "Близнецы": "Воздух", "Весы": "Воздух", "Водолей": "Воздух",
    "Рак": "Вода", "Скорпион": "Вода", "Рыбы": "Вода",
}

RULING_PLANETS_RU = {
    "Овен": "Марс", "Телец": "Венера", "Близнецы": "Меркурий",
    "Рак": "Луна", "Лев": "Солнце", "Дева": "Меркурий",
    "Весы": "Венера", "Скорпион": "Плутон", "Стрелец": "Юпитер",
    "Козерог": "Сатурн", "Водолей": "Уран", "Рыбы": "Нептун",
}

QUALITIES_RU = {
    "Овен": "Кардинальный", "Рак": "Кардинальный",
    "Весы": "Кардинальный", "Козерог": "Кардинальный",
    "Телец": "Фиксированный", "Лев": "Фиксированный",
    "Скорпион": "Фиксированный", "Водолей": "Фиксированный",
    "Близнецы": "Мутабельный", "Дева": "Мутабельный",
    "Стрелец": "Мутабельный", "Рыбы": "Мутабельный",
}

BASE_SCORES = {
    ("Овен", "Лев"): 95, ("Овен", "Стрелец"): 98, ("Овен", "Близнецы"): 75,
    ("Телец", "Дева"): 90, ("Телец", "Козерог"): 95, ("Телец", "Рак"): 70,
    ("Близнецы", "Весы"): 92, ("Близнецы", "Водолей"): 88,
    ("Рак", "Скорпион"): 96, ("Рак", "Рыбы"): 94,
    ("Лев", "Стрелец"): 97, ("Лев", "Овен"): 93,
    ("Дева", "Козерог"): 92, ("Дева", "Телец"): 88,
    ("Весы", "Водолей"): 91, ("Весы", "Близнецы"): 85,
    ("Скорпион", "Рыбы"): 95, ("Скорпион", "Рак"): 92,
    ("Стрелец", "Овен"): 96, ("Стрелец", "Лев"): 94,
    ("Козерог", "Телец"): 90, ("Козерог", "Дева"): 88,
    ("Водолей", "Весы"): 90, ("Водолей", "Близнецы"): 86,
    ("Рыбы", "Рак"): 94, ("Рыбы", "Скорпион"): 92,
}


def fallback_compatibility(sign1: str, sign2: str, lang: str = "ru") -> dict:
    key = (sign1, sign2)
    score = BASE_SCORES.get(key, BASE_SCORES.get((sign2, sign1), random.randint(55, 90)))

    if score >= 90:
        level = t("COMPAT_FALLBACK_LEVEL_IDEAL", lang)
    elif score >= 80:
        level = t("COMPAT_FALLBACK_LEVEL_EXCELLENT", lang)
    elif score >= 70:
        level = t("COMPAT_FALLBACK_LEVEL_GOOD", lang)
    elif score >= 60:
        level = t("COMPAT_FALLBACK_LEVEL_MEDIUM", lang)
    else:
        level = t("COMPAT_FALLBACK_LEVEL_HARD", lang)

    s1 = sign_display(sign1, lang)
    s2 = sign_display(sign2, lang)
    text = f"{s1} + {s2}\n\n{level}"
    return {"score": score, "level": level, "text": text}


@router.callback_query(F.data == "compatibility")
async def compatibility_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)

    _paid = await is_paid(user_id)
    _trial = False
    try:
        from database.postgres_db import is_trial_active
        _trial = await is_trial_active(user_id)
    except Exception:
        pass
    if user_id not in ADMINS and not _paid and not _trial:
        try:
            await callback.message.edit_text(
                t("COMPAT_SUB_LOCK", lang),
                reply_markup=back_to_menu_keyboard(lang)
            )
        except Exception:
            await callback.message.answer(
                t("COMPAT_SUB_LOCK_SHORT", lang),
                reply_markup=back_to_menu_keyboard(lang)
            )
        return

    text = t("COMPAT_MENU_TITLE", lang)
    try:
        from database.postgres_db import get_user_ai_limit, get_ai_usage
        limit = await get_user_ai_limit(user_id)
        usage = await get_ai_usage(user_id)
        if limit == -1:
            counter = t("AI_MENU_LIMIT_UNLIMITED", lang)
        else:
            left = max(0, limit - usage)
            counter = t("AI_MENU_LIMIT", lang, left=left, limit=limit)
        text = text + "\n\n" + counter
    except Exception as _e:
        logger.warning(f"counter failed: {_e}")
    try:
        await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_menu_keyboard(lang))
    await state.set_state(CompatibilityStates.waiting_partner1)


@router.message(CompatibilityStates.waiting_partner1)
async def process_partner1(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("COMPAT_CANCELLED", lang), reply_markup=back_to_menu_keyboard(lang))
        return

    p1 = parse_input(message.text)
    if not p1["sign"]:
        await message.answer(t("COMPAT_PARTNER1_NOT_RECOGNIZED", lang))
        return

    await state.update_data(p1=p1)
    await state.set_state(CompatibilityStates.waiting_partner2)

    await message.answer(
        t("COMPAT_PARTNER1_OK", lang, sign=sign_display(p1["sign"], lang))
    )


@router.message(CompatibilityStates.waiting_partner2)
async def process_partner2(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("COMPAT_CANCELLED", lang), reply_markup=back_to_menu_keyboard(lang))
        return

    p2 = parse_input(message.text)
    if not p2["sign"]:
        await message.answer(t("COMPAT_PARTNER2_NOT_RECOGNIZED", lang))
        return

    data = await state.get_data()
    p1 = data["p1"]
    await state.clear()

    # Проверка лимита ДО кэша
    user_id = message.from_user.id
    from database.postgres_db import get_user_ai_limit, get_ai_usage, get_limit_message, is_admin, increment_ai_usage
    _lim = await get_user_ai_limit(user_id)
    _use = await get_ai_usage(user_id)
    if _lim != -1 and _use >= _lim:
        _txt, _kb = await get_limit_message(user_id, lang, t, is_admin, usage=_use, limit=_lim)
        await message.answer(_txt, reply_markup=_kb)
        return

    processing_msg = await message.answer(t("COMPAT_PROCESSING", lang))

    cache_key = build_cache_key(p1, p2, lang=lang)
    result = None
    from_cache = False

    try:
        cached = await get_setting(cache_key)
        if cached and isinstance(cached, dict) and cached.get("text"):
            result = cached
            from_cache = True
            logger.info(f"compat cache: {cache_key}")
    except Exception as e:
        logger.warning(f"compat cache error: {e}")

    if not result:
        try:
            ai_result = await ai_service.generate_compatibility(
                sign_display(p1["sign"], "en"),
                sign_display(p2["sign"], "en"),
                lang=lang,
            )
            if ai_result:
                result = ai_result
                await set_setting(cache_key, ai_result)
                try:
                    from database.postgres_db import increment_ai_usage
                    await increment_ai_usage(user_id)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"AI compat error: {e}")

    if not result:
        result = fallback_compatibility(p1["sign"], p2["sign"], lang)

    score = result.get("score", 75)
    level = result.get("level", "—")
    text = result.get("text", "")

    stars = "\u2b50" * (score // 10) + "\u2606" * (10 - (score // 10))
    divider = "\u2501" * 24

    final_text = (
        f"{t('COMPAT_RESULT_TITLE', lang)}\n\n"
        f"{sign_display(p1['sign'], lang)} \U0001F49E {sign_display(p2['sign'], lang)}\n\n"
        f"{stars}\n"
        f"{score}% \u2014 {level}\n\n"
        f"{divider}\n\n"
        f"{text}"
    )

    try:
        await processing_msg.delete()
    except Exception:
        pass

    await message.answer(final_text, reply_markup=main_menu_keyboard(message.from_user.id, lang))
