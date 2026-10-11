"""Mood diary handler with multilang support."""
import logging
import os
import uuid
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, Message, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.postgres_db import (
    set_mood, get_mood_today, get_mood_history, get_mood_stats,
    count_bad_mood_streak, add_user_note, get_user_notes,
    get_user_ai_limit, get_ai_usage, increment_ai_usage,
    get_user_lang_cached,
)
from keyboards.main import back_to_menu_keyboard, main_menu_keyboard
from config import MULTILANG_ENABLED
from locales import t

logger = logging.getLogger(__name__)
router = Router()


class MoodDialogueStates(StatesGroup):
    waiting_story = State()


MOOD_EMOJI = {5: "\U0001F60A", 4: "\U0001F642", 3: "\U0001F610", 2: "\U0001F614", 1: "\U0001F622"}


async def _lang(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


def mood_emoji(mood: int) -> str:
    return MOOD_EMOJI.get(mood, "\u2753")


def mood_name(mood: int, lang: str) -> str:
    return t(f"MOOD_{mood}_NAME", lang) if mood in (1, 2, 3, 4, 5) else "?"


def avg_to_mood(avg: float, lang: str) -> tuple:
    if avg >= 4.5: return "\U0001F60A", t("MOOD_5_NAME", lang)
    if avg >= 3.5: return "\U0001F642", t("MOOD_4_NAME", lang)
    if avg >= 2.5: return "\U0001F610", t("MOOD_3_NAME", lang)
    if avg >= 1.5: return "\U0001F614", t("MOOD_2_NAME", lang)
    return "\U0001F622", t("MOOD_1_NAME", lang)


def build_mood_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("MOOD_5_BTN", lang), callback_data="mood_set_5"),
         InlineKeyboardButton(text=t("MOOD_4_BTN", lang), callback_data="mood_set_4")],
        [InlineKeyboardButton(text=t("MOOD_3_BTN", lang), callback_data="mood_set_3"),
         InlineKeyboardButton(text=t("MOOD_2_BTN", lang), callback_data="mood_set_2")],
        [InlineKeyboardButton(text=t("MOOD_1_BTN", lang), callback_data="mood_set_1")],
        [InlineKeyboardButton(text=t("MOOD_BTN_STATS", lang), callback_data="mood_stats"),
         InlineKeyboardButton(text=t("MOOD_BTN_CHART", lang), callback_data="mood_chart")],
        [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
    ])


def build_skip_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("MOOD_BTN_SKIP", lang), callback_data="mood_skip_story")],
    ])


@router.callback_query(F.data == "mood_diary")
async def mood_diary_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    today_mood = await get_mood_today(user_id)

    if today_mood:
        today_text = t("MOOD_TODAY_SET", lang, emoji=mood_emoji(today_mood), name=mood_name(today_mood, lang))
    else:
        today_text = t("MOOD_TODAY_NOT_SET", lang)

    divider = "\u2501" * 24
    text = (
        f"{t('MOOD_TITLE', lang)}\n\n"
        f"{t('MOOD_ASK', lang)}\n\n"
        f"{today_text}\n\n"
        f"{divider}\n"
        f"{t('MOOD_SELECT_PROMPT', lang)}"
    )

    try:
        await callback.message.edit_text(text, reply_markup=build_mood_keyboard(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=build_mood_keyboard(lang))


@router.callback_query(F.data.startswith("mood_set_"))
async def mood_set(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    try:
        mood = int(callback.data.replace("mood_set_", ""))
    except ValueError:
        return
    if mood not in (1, 2, 3, 4, 5):
        return

    await set_mood(user_id, mood)
    streak = await count_bad_mood_streak(user_id)

    await state.update_data(current_mood=mood, streak=streak)
    await state.set_state(MoodDialogueStates.waiting_story)

    question = t(f"MOOD_Q_{mood}", lang) if mood in (1, 2, 3, 4, 5) else t("MOOD_Q_DEFAULT", lang)

    if streak >= 3:
        question += t("MOOD_STREAK_NOTE", lang, n=streak)

    text = (
        t("MOOD_SAVED", lang, emoji=mood_emoji(mood), name=mood_name(mood, lang)) + "\n\n"
        + question + "\n\n"
        + t("MOOD_WRITE_OR_SKIP", lang)
    )
    try:
        await callback.message.edit_text(text, reply_markup=build_skip_keyboard(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=build_skip_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "mood_skip_story")
async def mood_skip_story(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    data = await state.get_data()
    mood = data.get("current_mood")
    await state.clear()

    if mood:
        if mood <= 2:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("MOOD_BTN_TALK", lang), callback_data="ai_question")],
                [InlineKeyboardButton(text=t("MOOD_BTN_STATS", lang), callback_data="mood_stats")],
                [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
            ])
            try:
                await callback.message.edit_text(t("MOOD_SKIP_OK_TALK", lang), reply_markup=keyboard)
            except Exception:
                pass
        else:
            try:
                await callback.message.edit_text(
                    t("MOOD_SKIP_OK", lang),
                    reply_markup=main_menu_keyboard(user_id, lang),
                )
            except Exception:
                pass

    await callback.answer()


@router.message(MoodDialogueStates.waiting_story)
async def mood_story(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lang = await _lang(user_id)
    data = await state.get_data()
    mood = data.get("current_mood", 3)
    streak = data.get("streak", 0)

    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("MOOD_CANCELLED", lang), reply_markup=main_menu_keyboard(user_id, lang))
        return

    text = message.text.strip()
    if len(text) < 3:
        await message.answer(t("MOOD_TOO_SHORT", lang))
        return

    if len(text) > 2000:
        text = text[:2000]

    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)
    if limit != -1 and usage >= limit:
        await state.clear()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("MOOD_LIMIT_BUY", lang), callback_data="check_status")],
            [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
        ])
        await message.answer(
            f"{t('MOOD_LIMIT_TITLE', lang)}\n\n{t('MOOD_LIMIT_DESC', lang, usage=usage, limit=limit)}",
            reply_markup=keyboard,
        )
        return

    processing = await message.answer(t("MOOD_PROCESSING", lang))

    try:
        from ai_service_n1n import ai_service

        mood_text = f"{mood_emoji(mood)} {mood_name(mood, lang)}"
        # AI prompt - keep simple RU prompt for now, AI will be updated in 3.5
        prompt = (
            f"User mood: {mood}/5\n"
            f"User message: {text}\n\n"
            f"Respond as a caring astrologer in 3-5 sentences, no markdown."
        )

        ai_response = None
        try:
            ai_response = await ai_service._query_ai(
                "You are a caring astrologer. Respond warmly, supportive, up to 5 sentences. No markdown.",
                prompt,
                max_tokens=500,
            )
            if ai_response:
                ai_response = ai_service._clean_response(ai_response)
        except Exception as e:
            logger.error(f"mood AI error: {e}")

        if not ai_response:
            if mood >= 4:
                ai_response = "\u2728"
            else:
                ai_response = "\U0001F319"

        try:
            await processing.delete()
        except Exception:
            pass

        facts = []
        try:
            facts = await ai_service.extract_user_facts(text, ai_response or "")
        except Exception as e:
            logger.debug(f"extract facts error: {e}")

        if ai_response:
            try:
                await increment_ai_usage(user_id)
            except Exception:
                pass

        await message.answer(f"{t('MOOD_AI_PREFIX', lang)} {ai_response}")

        if facts:
            existing_notes = await get_user_notes(user_id)
            existing_texts = [n["note"] for n in existing_notes]
            new_facts = [f for f in facts if f not in existing_texts]

            if new_facts:
                await state.update_data(pending_facts=new_facts, pending_selected=list(range(len(new_facts))))
                keyboard = _build_facts_keyboard(new_facts, list(range(len(new_facts))), lang)
                await message.answer(t("MOOD_FACTS_HEADER", lang), reply_markup=keyboard)
                return

        await state.clear()
        await message.answer(t("MOOD_GOOD_DAY", lang), reply_markup=main_menu_keyboard(user_id, lang))

    except Exception as e:
        logger.error(f"mood_story error: {e}")
        try:
            await processing.edit_text(t("MOOD_ERROR", lang))
        except Exception:
            pass
        await state.clear()


def _build_facts_keyboard(facts: list, selected: list, lang: str):
    buttons = []
    for i, fact in enumerate(facts):
        mark = "\u2705" if i in selected else "\u2610"
        short = fact[:40] + "..." if len(fact) > 40 else fact
        buttons.append([InlineKeyboardButton(
            text=f"{mark} {short}",
            callback_data=f"mood_fact_toggle_{i}",
        )])
    buttons.append([
        InlineKeyboardButton(text=t("MOOD_FACTS_SAVE", lang), callback_data="mood_facts_save"),
        InlineKeyboardButton(text=t("MOOD_FACTS_SKIP", lang), callback_data="mood_facts_cancel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("mood_fact_toggle_"))
async def mood_fact_toggle(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    data = await state.get_data()
    facts = data.get("pending_facts", [])
    selected = data.get("pending_selected", [])
    idx = int(callback.data.replace("mood_fact_toggle_", ""))
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


@router.callback_query(F.data == "mood_facts_save")
async def mood_facts_save(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    data = await state.get_data()
    facts = data.get("pending_facts", [])
    selected = data.get("pending_selected", [])
    await state.clear()

    if not selected:
        await callback.message.edit_text(t("MOOD_FACTS_CANCELLED", lang))
        return

    saved = 0
    for idx in selected:
        if 0 <= idx < len(facts):
            await add_user_note(user_id, facts[idx])
            saved += 1

    await callback.message.edit_text(t("MOOD_FACTS_SAVED", lang, n=saved))
    await callback.message.answer(
        t("MOOD_GOOD_DAY", lang),
        reply_markup=main_menu_keyboard(user_id, lang),
    )


@router.callback_query(F.data == "mood_facts_cancel")
async def mood_facts_cancel(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    await state.clear()
    await callback.message.edit_text(t("MOOD_FACTS_CANCELLED", lang))
    await callback.message.answer(
        t("MOOD_GOOD_DAY", lang),
        reply_markup=main_menu_keyboard(user_id, lang),
    )


@router.callback_query(F.data == "mood_stats")
async def mood_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    history = await get_mood_history(user_id, days=7)
    stats = await get_mood_stats(user_id, days=7)

    if not history:
        text = t("MOOD_STATS_EMPTY", lang)
    else:
        text = t("MOOD_STATS_TITLE_7", lang) + "\n\n"
        for entry in history:
            date_str = entry["mood_date"].strftime("%d.%m")
            text += f"{date_str} \u2014 {mood_emoji(entry['mood'])} {mood_name(entry['mood'], lang)}\n"

        if stats["total"] > 0:
            avg_emoji, avg_name = avg_to_mood(stats["avg"], lang)
            divider = "\u2501" * 24
            text += (
                f"\n{divider}\n"
                f"{t('MOOD_STATS_AVG', lang)}: {avg_emoji} {avg_name} ({stats['avg']:.1f}/5)\n"
                f"{t('MOOD_STATS_COUNT', lang)}: {stats['total']}"
            )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("MOOD_BTN_DIARY", lang), callback_data="mood_diary")],
        [InlineKeyboardButton(text=t("MOOD_BTN_CHART", lang), callback_data="mood_chart")],
        [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "mood_chart")
async def mood_chart(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    history = await get_mood_history(user_id, days=30)

    if len(history) < 2:
        await callback.answer(t("MOOD_STATS_CHART_NEED", lang), show_alert=True)
        return

    msg = await callback.message.edit_text(t("MOOD_CHART_BUILDING", lang))
    try:
        chart_path = _build_mood_chart(history)
        if not chart_path:
            await msg.edit_text(t("MOOD_CHART_FAIL", lang))
            return
        try:
            await msg.delete()
        except Exception:
            pass
        photo = FSInputFile(chart_path)
        await callback.message.answer_photo(photo, caption=t("MOOD_CHART_CAPTION", lang))
        await callback.message.answer(
            t("MOOD_CHART_WHAT_NEXT", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("MOOD_BTN_DIARY", lang), callback_data="mood_diary")],
                [InlineKeyboardButton(text=t("MOOD_BTN_STATS", lang), callback_data="mood_stats")],
                [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
            ]),
        )
        try:
            os.remove(chart_path)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"chart error: {e}")
        try:
            await msg.edit_text(f"\u274c {e}")
        except Exception:
            pass


def _build_mood_chart(history: list) -> str:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib not installed")
        return None

    data = sorted(history, key=lambda x: x["mood_date"])
    dates = [d["mood_date"].strftime("%d.%m") for d in data]
    moods = [d["mood"] for d in data]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#1a2a3a")
    ax.set_facecolor("#1a2a3a")
    ax.plot(dates, moods, "o-", color="#FFD700", linewidth=2, markersize=8)
    ax.grid(True, alpha=0.3, color="#c9a959")
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["\U0001F622", "\U0001F614", "\U0001F610", "\U0001F642", "\U0001F60A"], fontsize=14)
    ax.set_title("Mood", color="#FFD700", fontsize=16, pad=15)
    ax.tick_params(colors="#F0F0F0", labelsize=9)
    plt.xticks(rotation=45, ha="right")
    for spine in ax.spines.values():
        spine.set_color("#c9a959")
    plt.tight_layout()
    filename = f"mood_chart_{uuid.uuid4().hex}.png"
    plt.savefig(filename, facecolor="#1a2a3a", dpi=100)
    plt.close()
    return filename
