"""Tarot handler with multilang support."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.tarot import (
    get_or_create_reading,
    get_card_caption,
    get_card_image,
    get_total_cards,
    get_positions,
)
from database.postgres_db import is_paid, is_admin, get_user_lang_cached
from config import ADMINS, MULTILANG_ENABLED
from locales import t

logger = logging.getLogger(__name__)
router = Router()


class TarotStates(StatesGroup):
    waiting_question = State()


async def _lang(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


def _menu_kb(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("TAROT_BTN_NEW", lang), callback_data="tarot_new")],
        [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
    ])


def _back_kb(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("TAROT_BTN_MORE", lang), callback_data="tarot_new")],
        [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
    ])


def _pay_kb(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("TAROT_BTN_BUY", lang), callback_data="check_status")],
        [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
    ])


@router.callback_query(F.data == "tarot_menu")
async def tarot_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    lang = await _lang(user_id)

    try:
        paid = await is_paid(user_id)
        admin = await is_admin(user_id)
    except Exception:
        paid, admin = False, False

    total = get_total_cards()
    if total == 0:
        await callback.answer(t("TAROT_NOT_LOADED", lang), show_alert=True)
        return

    text = t("TAROT_MENU_TITLE", lang)

    if not paid and not admin:
        text += t("TAROT_LOCK", lang)
        try:
            await callback.message.edit_text(text, reply_markup=_pay_kb(lang))
        except Exception:
            await callback.message.answer(text, reply_markup=_pay_kb(lang))
        return

    try:
        await callback.message.edit_text(text, reply_markup=_menu_kb(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=_menu_kb(lang))


@router.callback_query(F.data == "tarot_new")
async def tarot_new_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)

    try:
        paid = await is_paid(user_id)
        admin = await is_admin(user_id)
    except Exception:
        paid, admin = False, False

    if not paid and not admin:
        await callback.answer(t("TAROT_NEED_SUB", lang), show_alert=True)
        return

    await state.set_state(TarotStates.waiting_question)
    text = t("TAROT_ASK_Q", lang)
    try:
        await callback.message.edit_text(text)
    except Exception:
        await callback.message.answer(text)


@router.message(TarotStates.waiting_question)
async def tarot_process_question(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    lang = await _lang(user_id)
    question = (message.text or "").strip()

    if question == "/cancel":
        await message.answer(t("TAROT_CANCELLED", lang))
        return

    if len(question) < 5:
        await message.answer(t("TAROT_TOO_SHORT", lang))
        return

    if len(question) > 500:
        question = question[:500]

    processing = await message.answer(t("TAROT_PROCESSING", lang))

    try:
        result = await get_or_create_reading(user_id, question, count=3)

        if "error" in result:
            await processing.edit_text(t("TAROT_ERROR", lang, err=result["error"]))
            return

        cards = result["cards"]
        ai_answer = result["ai_answer"]
        from_cache = result.get("from_cache", False)

        try:
            await processing.delete()
        except Exception:
            pass

        positions = get_positions(question, lang=lang)
        for i, card_key in enumerate(cards):
            img_path = get_card_image(card_key)
            caption = get_card_caption(card_key)
            if i < len(positions):
                caption = f"{positions[i]}: {caption}"

            if img_path and img_path.exists():
                try:
                    await message.answer_photo(FSInputFile(img_path), caption=caption)
                except Exception as e:
                    logger.warning(f"send photo {card_key}: {e}")
                    await message.answer(caption)
            else:
                await message.answer(caption)

        cache_note = t("TAROT_AI_CACHE", lang) if from_cache else ""
        answer_text = f"{t('TAROT_AI_TITLE', lang)}{cache_note}:\n\n{ai_answer}"
        if len(answer_text) > 4000:
            for i in range(0, len(answer_text), 4000):
                await message.answer(answer_text[i:i+4000])
        else:
            await message.answer(answer_text)

        await message.answer(t("TAROT_WANT_MORE", lang), reply_markup=_back_kb(lang))

    except Exception as e:
        logger.error(f"tarot error: {e}")
        try:
            await processing.edit_text(t("TAROT_ERROR", lang, err=str(e)))
        except Exception:
            await message.answer(t("TAROT_ERROR", lang, err=str(e)))
