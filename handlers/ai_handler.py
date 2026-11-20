"""AI handler with multilang support."""
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import AIQuestionStates
from ai_service_n1n import ai_service
from keyboards.main import (
    ai_question_keyboard, ai_dialog_keyboard,
    back_to_menu_keyboard, main_menu_keyboard
)
from utils.validators import validator
from database.postgres_db import (
    get_user_ai_limit, get_ai_usage, increment_ai_usage,
    add_user_note, get_user, get_user_notes,
    is_admin, get_user_lang_cached,
)
from config import ADMINS, MULTILANG_ENABLED
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


def _ai_question_kb(lang: str):
    labels = {
        "ru": ("\U0001F4AD \u0417\u0430\u0434\u0430\u0442\u044c \u0432\u043e\u043f\u0440\u043e\u0441", "\U0001F4DD \u041f\u0440\u0438\u043c\u0435\u0440\u044b"),
        "en": ("\U0001F4AD Ask a question", "\U0001F4DD Examples"),
        "de": ("\U0001F4AD Frage stellen", "\U0001F4DD Beispiele"),
    }
    ask, ex = labels.get(lang, labels["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ask, callback_data="ask_ai")],
        [InlineKeyboardButton(text=ex, callback_data="ai_examples")],
        [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
    ])


def _ai_dialog_kb(lang: str):
    labels = {
        "ru": ("\U0001F51A \u0417\u0430\u043a\u043e\u043d\u0447\u0438\u0442\u044c \u0434\u0438\u0430\u043b\u043e\u0433", "\U0001F4DD \u041f\u0440\u0438\u043c\u0435\u0440\u044b \u0432\u043e\u043f\u0440\u043e\u0441\u043e\u0432"),
        "en": ("\U0001F51A End dialogue", "\U0001F4DD Question examples"),
        "de": ("\U0001F51A Dialog beenden", "\U0001F4DD Fragebeispiele"),
    }
    end, ex = labels.get(lang, labels["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=end, callback_data="ai_end_dialog")],
        [InlineKeyboardButton(text=ex, callback_data="ai_examples")],
    ])


@router.callback_query(F.data == "ai_question")
async def ai_question_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)

    if limit == -1:
        limit_text = t("AI_MENU_LIMIT_UNLIMITED", lang)
    else:
        left = max(0, limit - usage)
        limit_text = t("AI_MENU_LIMIT", lang, left=left, limit=limit)

    divider = "\u2501" * 24
    text = (
        t("AI_MENU_TITLE", lang) + "\n\n"
        + t("AI_MENU_DESC", lang) + "\n\n"
        + t("AI_MENU_EXAMPLES", lang) + "\n\n"
        + limit_text + "\n\n"
        + t("AI_MENU_PROFILE_NOTE", lang) + "\n\n"
        + t("AI_MENU_DIALOG_NOTE", lang)
    )

    try:
        await callback.message.edit_text(text, reply_markup=_ai_question_kb(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=_ai_question_kb(lang))


@router.callback_query(F.data == "ask_ai")
async def start_ai_question(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    from database.postgres_db import has_ai_access
    if not await has_ai_access(user_id):
        from keyboards.main import back_to_menu_keyboard
        await callback.message.edit_text(
            "🔒 Для доступа к этой функции оформите подписку или начните бесплатный триал.",
            reply_markup=back_to_menu_keyboard(lang)
        )
        return

    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)

    if limit != -1 and usage >= limit:
        from database.postgres_db import get_limit_message
        limit_text, kb = await get_limit_message(user_id, lang, t, is_admin, usage=usage, limit=limit)
        try:
            await callback.message.edit_text(limit_text, reply_markup=kb)
        except Exception:
            await callback.message.answer(limit_text, reply_markup=kb)
        return

    await state.set_state(AIQuestionStates.waiting_question)
    try:
        await callback.message.edit_text(t("AI_ASK", lang))
    except Exception:
        await callback.message.answer(t("AI_ASK_SHORT", lang))


@router.message(AIQuestionStates.waiting_question)
async def process_ai_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await _lang(user_id)

    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("AI_CANCELLED", lang), reply_markup=back_to_menu_keyboard(lang))
        return

    valid, result = validator.validate_question(message.text)
    if not valid:
        await message.answer(f"\u274c {result}", reply_markup=_ai_dialog_kb(lang))
        return

    from database.postgres_db import has_ai_access
    if not await has_ai_access(user_id):
        from keyboards.main import back_to_menu_keyboard
        await callback.message.edit_text(
            "🔒 Для доступа к этой функции оформите подписку или начните бесплатный триал.",
            reply_markup=back_to_menu_keyboard(lang)
        )
        return

    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)

    if limit != -1 and usage >= limit:
        await state.clear()
        from database.postgres_db import get_limit_message
        limit_text, kb = await get_limit_message(user_id, lang, t, is_admin, usage=usage, limit=limit)
        await message.answer(limit_text, reply_markup=kb)
        return

    processing_msg = await message.answer(t("AI_PROCESSING", lang))

    async def update_thinking():
        await asyncio.sleep(3)
        try:
            await processing_msg.edit_text(t("AI_THINKING", lang))
        except Exception:
            pass

    thinking_task = asyncio.create_task(update_thinking())

    try:
        response = await ai_service.process_question(user_id, result, lang=lang)
        thinking_task.cancel()

        try:
            await processing_msg.delete()
        except Exception:
            pass

        answer = response.get("message", "Error")
        from_cache = response.get("from_cache", False)
        facts = response.get("facts", [])

        if not from_cache:
            new_usage = await increment_ai_usage(user_id)
            try:
                _lim = await get_user_ai_limit(user_id)
                if _lim == -1:
                    _left_txt = t("AI_MENU_LIMIT_UNLIMITED", lang)
                else:
                    _left_txt = t("AI_MENU_LIMIT", lang, left=max(0, _lim - new_usage), limit=_lim)
                await message.answer(_left_txt)
            except Exception:
                pass

        admin_marker = ""
        if await is_admin(user_id):
            admin_marker = "\n\n" + t("AI_ANSWER_MODEL", lang, model=response.get("model", "?"))

        hint_text = t("AI_ANSWER_HINT", lang)
        await message.answer(
            f"{t('AI_ANSWER_TITLE', lang)}\n\n{answer}{admin_marker}\n\n{hint_text}",
            reply_markup=_ai_dialog_kb(lang)
        )

        if limit != -1:
            new_usage = await get_ai_usage(user_id)
            left = max(0, limit - new_usage)
            if 0 < left <= 5:
                await message.answer(t("AI_LEFT_5", lang, left=left))
            elif left == 0:
                await message.answer(t("AI_LEFT_0", lang))

        if facts:
            existing_notes = await get_user_notes(user_id)
            existing_texts = [n["note"] for n in existing_notes]
            new_facts = [f for f in facts if f not in existing_texts]
            if new_facts:
                await show_facts_confirmation(message, state, new_facts, lang)
            else:
                await message.answer(t("AI_FACTS_ALREADY", lang))
        else:
            q_lower = message.text.lower()
            pronouns = ["\u044f ", "\u043c\u043d\u0435 ", "\u043c\u0435\u043d\u044f ", "\u043c\u043e\u0439 ",
                        "i ", "me ", "my ", "ich ", "mir ", "mein "]
            if any(p in q_lower for p in pronouns):
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=t("AI_FILL_PROFILE_BTN", lang), callback_data="profile_edit")],
                    [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
                ])
                await message.answer(t("AI_FILL_PROFILE_NOTE", lang), reply_markup=keyboard)

    except Exception as e:
        thinking_task.cancel()
        logger.error(f"AI error: {e}")
        try:
            await processing_msg.edit_text(t("AI_ERROR", lang), reply_markup=_ai_dialog_kb(lang))
        except Exception:
            await message.answer(t("AI_ERROR", lang), reply_markup=_ai_dialog_kb(lang))


@router.callback_query(F.data == "ai_end_dialog")
async def ai_end_dialog(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    await state.clear()
    try:
        await callback.message.edit_text(
            t("AI_ENDED", lang),
            reply_markup=main_menu_keyboard(user_id, lang)
        )
    except Exception:
        await callback.message.answer(
            t("AI_ENDED_SHORT", lang),
            reply_markup=main_menu_keyboard(user_id, lang)
        )


async def show_facts_confirmation(message: Message, state: FSMContext, facts: list, lang: str):
    current_data = await state.get_data()
    current_data["pending_facts"] = facts
    current_data["pending_selected"] = list(range(len(facts)))
    await state.update_data(**current_data)

    keyboard = _build_facts_keyboard(facts, list(range(len(facts))), lang)
    await message.answer(
        t("AI_FACTS_TITLE", lang) + "\n\n" + t("AI_FACTS_HINT", lang),
        reply_markup=keyboard
    )


def _build_facts_keyboard(facts: list, selected: list, lang: str):
    buttons = []
    for i, fact in enumerate(facts):
        mark = "\u2705" if i in selected else "\u2610"
        short = fact[:40] + "..." if len(fact) > 40 else fact
        buttons.append([InlineKeyboardButton(
            text=f"{mark} {short}",
            callback_data=f"fact_toggle_{i}"
        )])
    buttons.append([
        InlineKeyboardButton(text=t("AI_FACTS_SAVE", lang), callback_data="facts_save"),
        InlineKeyboardButton(text=t("AI_FACTS_SKIP", lang), callback_data="facts_cancel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("fact_toggle_"))
async def fact_toggle(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    data = await state.get_data()
    facts = data.get("pending_facts", [])
    selected = data.get("pending_selected", [])
    idx = int(callback.data.replace("fact_toggle_", ""))
    if idx in selected:
        selected.remove(idx)
    else:
        selected.append(idx)
    await state.update_data(pending_selected=selected)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=_build_facts_keyboard(facts, selected, lang)
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "facts_save")
async def facts_save(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    data = await state.get_data()
    facts = data.get("pending_facts", [])
    selected = data.get("pending_selected", [])

    data["pending_facts"] = []
    data["pending_selected"] = []
    await state.update_data(**data)

    if not selected:
        await callback.message.edit_text(t("AI_FACTS_NOTHING", lang))
        return

    saved = 0
    for idx in selected:
        if 0 <= idx < len(facts):
            await add_user_note(user_id, facts[idx])
            saved += 1

    await callback.message.edit_text(t("AI_FACTS_SAVED", lang, n=saved))


@router.callback_query(F.data == "facts_cancel")
async def facts_cancel(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    data = await state.get_data()
    data["pending_facts"] = []
    data["pending_selected"] = []
    await state.update_data(**data)
    await callback.message.edit_text(t("AI_FACTS_CANCELLED", lang))


@router.callback_query(F.data == "ai_examples")
async def ai_examples(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    try:
        await callback.message.answer(t("AI_EXAMPLES_TEXT", lang))
    except Exception as e:
        logger.error(f"ai_examples error: {e}")
