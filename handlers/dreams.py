"""Dream interpretation handler (subscription + AI limits)."""
import hashlib
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.postgres_db import (
    get_setting, set_setting, get_user_lang_cached,
    is_paid, is_admin, get_user_ai_limit, get_ai_usage, increment_ai_usage,
)
from config import MULTILANG_ENABLED
from locales import t
from ai_service_n1n import ai_service

logger = logging.getLogger(__name__)
router = Router()


class DreamStates(StatesGroup):
    waiting_dream = State()


async def _lang(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


async def _check_access(user_id: int, lang: str):
    """Возвращает (ok, error_text, error_kb, is_limit_reached)."""
    # 1. Проверка подписки
    try:
        paid = await is_paid(user_id)
        admin = await is_admin(user_id)
        from database.postgres_db import is_trial_active
        trial = await is_trial_active(user_id)
    except Exception:
        paid, admin, trial = False, False, False

    if not paid and not admin and not trial:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("DREAM_BTN_BUY", lang), callback_data="check_status")],
            [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
        ])
        return False, t("DREAM_SUB_LOCK", lang), kb, False

    # 2. Проверка AI-лимита
    try:
        limit = await get_user_ai_limit(user_id)
        usage = await get_ai_usage(user_id)
    except Exception:
        limit, usage = -1, 0

    if limit != -1 and usage >= limit:
        from database.postgres_db import get_limit_message
        limit_text, kb = await get_limit_message(user_id, lang, t, is_admin, usage=usage, limit=limit)
        return False, limit_text, kb, True

    return True, None, None, False


async def _interpret_dream(user_id: int, dream_text: str, lang: str) -> str:
    """AI dream interpretation with cache (не считает лимит — вызов после проверки)."""
    cache_key = "dream_" + hashlib.md5(f"{dream_text.lower().strip()}|{lang}".encode()).hexdigest()[:16]
    cached = await get_setting(cache_key)
    if cached and isinstance(cached, dict) and cached.get("text"):
        logger.info(f"dream cache hit: {cache_key}")
        return cached["text"], True  # from_cache

    lang_name = {"ru": "Russian", "en": "English", "de": "German"}.get(lang, "Russian")
    system_prompt = (
        "You are an experienced dream interpreter. Analyze the dream.\n"
        "Requirements:\n"
        "- No markdown (**, __, `)\n"
        "- Use emoji for formatting\n"
        "- Tone: warm, mystical, supportive\n"
        f"- IMPORTANT: Answer ONLY in {lang_name}\n"
        "- Reference specific symbols from the dream\n"
        "- 6-10 sentences total\n"
    )
    user_prompt = (
        f"User's dream:\n{dream_text}\n\n"
        "Structure:\n"
        "1. Main symbols and what they mean (2-3 sentences)\n"
        "2. Emotional analysis (1-2 sentences)\n"
        "3. Interpretation for the user (2-3 sentences)\n"
        "4. Advice (1-2 sentences)\n\n"
        f"Answer in {lang_name}."
    )

    answer = await ai_service._query_ai(system_prompt, user_prompt, max_tokens=800)
    if answer:
        answer = ai_service._clean_response(answer)
        await set_setting(cache_key, {"text": answer})
        return answer, False
    return t("DREAM_FALLBACK", lang), False


# ============================================================
# Меню
# ============================================================
@router.callback_query(F.data == "dreams_menu")
async def dreams_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    await state.clear()

    # Проверка доступа (без списания)
    ok, err_text, err_kb, _ = await _check_access(user_id, lang)
    if not ok:
        try:
            await callback.message.edit_text(err_text, reply_markup=err_kb)
        except Exception:
            await callback.message.answer(err_text, reply_markup=err_kb)
        return

    # Лимит
    try:
        limit = await get_user_ai_limit(user_id)
        usage = await get_ai_usage(user_id)
    except Exception:
        limit, usage = -1, 0

    if limit == -1:
        limit_text = t("DREAM_LIMIT_UNLIMITED", lang)
    else:
        left = max(0, limit - usage)
        limit_text = t("DREAM_LIMIT_INFO", lang, left=left, limit=limit)

    text = t("DREAM_MENU_TITLE", lang) + "\n\n" + limit_text

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("DREAM_BTN_NEW", lang), callback_data="dream_new")],
        [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "dream_new")
async def dream_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)

    # Повторная проверка доступа (мог исчерпаться пока смотрел меню)
    ok, err_text, err_kb, _ = await _check_access(user_id, lang)
    if not ok:
        try:
            await callback.message.edit_text(err_text, reply_markup=err_kb)
        except Exception:
            await callback.message.answer(err_text, reply_markup=err_kb)
        return

    await state.set_state(DreamStates.waiting_dream)
    text = t("DREAM_ASK", lang)
    try:
        await callback.message.edit_text(text)
    except Exception:
        await callback.message.answer(text)


@router.message(DreamStates.waiting_dream)
async def dream_process(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await _lang(user_id)
    dream_text = (message.text or "").strip()

    if dream_text == "/cancel":
        await state.clear()
        await message.answer(t("DREAM_CANCELLED", lang))
        return

    if len(dream_text) < 10:
        await message.answer(t("DREAM_TOO_SHORT", lang))
        return

    if len(dream_text) > 1500:
        dream_text = dream_text[:1500]

    # Проверка лимита (перед AI)
    ok, err_text, err_kb, is_limit = await _check_access(user_id, lang)
    if not ok:
        await state.clear()
        await message.answer(err_text, reply_markup=err_kb)
        return

    await state.clear()
    processing = await message.answer(t("DREAM_PROCESSING", lang))

    try:
        interpretation, from_cache = await _interpret_dream(user_id, dream_text, lang)
        try:
            await processing.delete()
        except Exception:
            pass

        # Тратим лимит ТОЛЬКО если AI сгенерировал (не из кэша)
        if not from_cache:
            try:
                new_usage = await increment_ai_usage(user_id)
                try:
                    _lim = await get_user_ai_limit(user_id)
                    if _lim == -1:
                        _left_txt = t("DREAM_LIMIT_UNLIMITED", lang)
                    else:
                        _left_txt = t("DREAM_LIMIT_INFO", lang, left=max(0, _lim - new_usage), limit=_lim)
                    await message.answer(_left_txt)
                except Exception:
                    pass
            except Exception:
                pass

        cache_note = t("DREAM_CACHE_NOTE", lang) if from_cache else ""
        text = t("DREAM_ANSWER_TITLE", lang) + cache_note + "\n\n" + interpretation
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await message.answer(text[i:i+4000])
        else:
            await message.answer(text)

        # Остаток лимита
        try:
            limit = await get_user_ai_limit(user_id)
            usage = await get_ai_usage(user_id)
            if limit != -1:
                left = max(0, limit - usage)
                if 0 < left <= 5:
                    await message.answer(t("DREAM_LEFT", lang, left=left))
                elif left == 0:
                    await message.answer(t("DREAM_LEFT_0", lang))
        except Exception:
            pass

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("DREAM_BTN_MORE", lang), callback_data="dream_new")],
            [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
        ])
        await message.answer(t("DREAM_WHAT_NEXT", lang), reply_markup=kb)

    except Exception as e:
        logger.error(f"dream error: {e}")
        try:
            await processing.edit_text(t("DREAM_ERROR", lang, err=str(e)))
        except Exception:
            await message.answer(t("DREAM_ERROR", lang, err=str(e)))
