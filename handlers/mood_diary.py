import logging
import os
import uuid
import asyncio
from datetime import datetime, timedelta
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
)
from keyboards.main import back_to_menu_keyboard, main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# FSM
# ============================================================
class MoodDialogueStates(StatesGroup):
    waiting_story = State()


# ============================================================
# НАСТРОЕНИЯ
# ============================================================
MOODS = {
    5: {"emoji": "😊", "name": "Отлично"},
    4: {"emoji": "🙂", "name": "Хорошо"},
    3: {"emoji": "😐", "name": "Нормально"},
    2: {"emoji": "😔", "name": "Плохо"},
    1: {"emoji": "😢", "name": "Ужасно"},
}

# Вопросы в зависимости от настроения
MOOD_QUESTIONS = {
    5: "🌟 Супер! Расскажете, что хорошего произошло?",
    4: "😊 Здорово! Что порадовало вас сегодня?",
    3: "🤔 Что происходит? Расскажете?",
    2: "💙 Что случилось? Я готов выслушать.",
    1: "🫂 Мне жаль, что вам тяжело. Хотите поделиться?",
}


def mood_emoji(mood: int) -> str:
    return MOODS.get(mood, {}).get("emoji", "❓")


def mood_name(mood: int) -> str:
    return MOODS.get(mood, {}).get("name", "?")


def avg_to_mood(avg: float) -> tuple:
    if avg >= 4.5: return "😊", "Отлично"
    if avg >= 3.5: return "🙂", "Хорошо"
    if avg >= 2.5: return "😐", "Нормально"
    if avg >= 1.5: return "😔", "Плохо"
    return "😢", "Ужасно"


def build_mood_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😊 Отлично", callback_data="mood_set_5"),
         InlineKeyboardButton(text="🙂 Хорошо", callback_data="mood_set_4")],
        [InlineKeyboardButton(text="😐 Нормально", callback_data="mood_set_3"),
         InlineKeyboardButton(text="😔 Плохо", callback_data="mood_set_2")],
        [InlineKeyboardButton(text="😢 Ужасно", callback_data="mood_set_1")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="mood_stats"),
         InlineKeyboardButton(text="📈 График", callback_data="mood_chart")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])


def build_skip_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="mood_skip_story")],
    ])


# ============================================================
# ГЛАВНЫЙ ЭКРАН ДНЕВНИКА
# ============================================================
@router.callback_query(F.data == "mood_diary")
async def mood_diary_menu(callback: CallbackQuery, state: FSMContext):
    # Сбрасываем диалог, если был
    await state.clear()

    user_id = callback.from_user.id
    today_mood = await get_mood_today(user_id)

    if today_mood:
        today_text = f"Сегодня вы отметили: {mood_emoji(today_mood)} {mood_name(today_mood)}"
    else:
        today_text = "Сегодня вы ещё не отметили настроение."

    text = (
        "📔 ДНЕВНИК НАСТРОЕНИЯ\n\n"
        "Как ваше настроение сегодня?\n\n"
        f"{today_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Выберите настроение или посмотрите статистику:"
    )

    try:
        await callback.message.edit_text(text, reply_markup=build_mood_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=build_mood_keyboard())


# ============================================================
# СОХРАНЕНИЕ НАСТРОЕНИЯ
# ============================================================
@router.callback_query(F.data.startswith("mood_set_"))
async def mood_set(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    try:
        mood = int(callback.data.replace("mood_set_", ""))
    except ValueError:
        return
    if mood not in MOODS:
        return

    # Сохраняем настроение
    await set_mood(user_id, mood)

    # Проверяем streak плохого
    streak = await count_bad_mood_streak(user_id)

    # Запоминаем настроение в FSM для диалога
    await state.update_data(current_mood=mood, streak=streak)
    await state.set_state(MoodDialogueStates.waiting_story)

    # Вопрос
    question = MOOD_QUESTIONS.get(mood, "Расскажете?")

    # Проверка streak — если 3+, добавляем акцент
    if streak >= 3:
        question += f"\n\n💙 Кстати, это уже {streak}-й день подряд. Что происходит?"

    text = (
        f"✅ Настроение сохранено: {mood_emoji(mood)} {mood_name(mood)}\n\n"
        f"{question}\n\n"
        f"Можете написать пару слов или пропустить."
    )
    try:
        await callback.message.edit_text(text, reply_markup=build_skip_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=build_skip_keyboard())
    await callback.answer()


@router.callback_query(F.data == "mood_skip_story")
async def mood_skip_story(callback: CallbackQuery, state: FSMContext):
    """Пропуск рассказа."""
    data = await state.get_data()
    mood = data.get("current_mood")
    await state.clear()

    if mood:
        # Всё равно можно предложить AI-вопрос, если плохое настроение
        if mood <= 2:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Поговорить с астрологом", callback_data="ai_question")],
                [InlineKeyboardButton(text="📊 Статистика", callback_data="mood_stats")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
            ])
            try:
                await callback.message.edit_text(
                    "Хорошо. Если захотите поговорить — я рядом 💙",
                    reply_markup=keyboard,
                )
            except Exception:
                pass
        else:
            try:
                await callback.message.edit_text(
                    "Хорошо! Жду вас завтра 🌟",
                    reply_markup=main_menu_keyboard(callback.from_user.id),
                )
            except Exception:
                pass

    await callback.answer()


# ============================================================
# ОБРАБОТКА РАССКАЗА
# ============================================================
@router.message(MoodDialogueStates.waiting_story)
async def mood_story(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    mood = data.get("current_mood", 3)
    streak = data.get("streak", 0)
    user_id = message.from_user.id

    # /cancel
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Хорошо. До встречи!", reply_markup=main_menu_keyboard(user_id))
        return

    text = message.text.strip()
    if len(text) < 3:
        await message.answer("Расскажите чуть подробнее или нажмите «⏭️ Пропустить».")
        return

    if len(text) > 2000:
        text = text[:2000]

    # Проверка лимита
    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)
    if limit != -1 and usage >= limit:
        await state.clear()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить Премиум", callback_data="check_status")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ])
        await message.answer(
            "⚠️ ЛИМИТ ВОПРОСОВ ИСЧЕРПАН\n\n"
            f"Вы задали {usage}/{limit} вопросов сегодня.\n"
            "Лимит обновится в 00:00 UTC.\n\n"
            "💎 Купите Премиум — 100 запросов/день.\n\n"
            "Ваше настроение сохранено 🌟",
            reply_markup=keyboard,
        )
        return

    # Отправляем «AI думает»
    processing = await message.answer("🔮 Астролог обрабатывает ваш рассказ...")

    try:
        # 1. AI-ответ (совет) на основе настроения + текста
        from ai_service_n1n import ai_service

        mood_text = f"{mood_emoji(mood)} {mood_name(mood)}"
        prompt = (
            f"Пользователь отметил настроение: {mood_text} (шкала: 5=отлично, 1=ужасно).\n"
            f"Рассказ пользователя: {text}\n\n"
            f"Ответь от лица заботливого астролога:\n"
            f"- Поддержи или порадуйся\n"
            f"- Дай 1-2 коротких совета на основе настроения\n"
            f"- Упомяни астрологию, если уместно\n"
            f"- Без markdown (**, __, `)\n"
            f"- 3-5 предложений\n"
        )

        ai_response = None
        try:
            ai_response = await ai_service._query_ai(
                "Ты — заботливый астролог. Отвечай тёпло, поддерживающе, до 5 предложений. Без markdown.",
                prompt,
                max_tokens=500,
            )
            if ai_response:
                ai_response = ai_service._clean_response(ai_response)
        except Exception as e:
            logger.error(f"Ошибка AI mood: {e}")

        if not ai_response:
            # Fallback
            if mood >= 4:
                ai_response = "Рад за вас! Пусть этот позитив заряжает вас на всю неделю ✨"
            elif mood <= 2:
                ai_response = "Держитесь! Помните: даже самая тёмная ночь заканчивается рассветом 🌅"
            else:
                ai_response = "Спасибо, что поделились. Желаю вам гармонии и спокойствия ✨"

        try:
            await processing.delete()
        except Exception:
            pass

        # 2. Извлекаем факты (через AI)
        facts = []
        try:
            facts = await ai_service.extract_user_facts(text, ai_response or "")
        except Exception as e:
            logger.debug(f"Ошибка извлечения фактов mood: {e}")

        # 3. Тратим лимит ТОЛЬКО при успешном AI-ответе
        if ai_response:
            try:
                await increment_ai_usage(user_id)
            except Exception:
                pass

        # 4. Отправляем AI-ответ
        await message.answer(f"🤖 {ai_response}")

        # 4. Предлагаем сохранить факты (если есть)
        if facts:
            existing_notes = await get_user_notes(user_id)
            existing_texts = [n["note"] for n in existing_notes]
            new_facts = [f for f in facts if f not in existing_texts]

            if new_facts:
                # Сохраняем в state для подтверждения
                await state.update_data(pending_facts=new_facts, pending_selected=list(range(len(new_facts))))
                keyboard = _build_facts_keyboard(new_facts, list(range(len(new_facts))))
                await message.answer(
                    "✨ Астролог хочет запомнить о вас:\n\n"
                    "Нажмите на факт, чтобы выбрать/убрать.\n"
                    "Затем нажмите «💾 Сохранить».",
                    reply_markup=keyboard,
                )
                return  # FSM не сбрасываем — ждём подтверждения

        # 5. Если фактов нет — выходим из FSM
        await state.clear()
        await message.answer(
            "Хорошего дня! 🌟",
            reply_markup=main_menu_keyboard(user_id),
        )

    except Exception as e:
        logger.error(f"Ошибка mood_story: {e}")
        try:
            await processing.edit_text("❌ Произошла ошибка. Попробуйте ещё раз.")
        except Exception:
            pass
        await state.clear()


# ============================================================
# ФАКТЫ (копия логики из ai_handler)
# ============================================================
def _build_facts_keyboard(facts: list, selected: list):
    buttons = []
    for i, fact in enumerate(facts):
        mark = "✅" if i in selected else "☐"
        short = fact[:40] + "..." if len(fact) > 40 else fact
        buttons.append([InlineKeyboardButton(
            text=f"{mark} {short}",
            callback_data=f"mood_fact_toggle_{i}",
        )])
    buttons.append([
        InlineKeyboardButton(text="💾 Сохранить", callback_data="mood_facts_save"),
        InlineKeyboardButton(text="❌ Не надо", callback_data="mood_facts_cancel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("mood_fact_toggle_"))
async def mood_fact_toggle(callback: CallbackQuery, state: FSMContext):
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
            reply_markup=_build_facts_keyboard(facts, selected)
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "mood_facts_save")
async def mood_facts_save(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    facts = data.get("pending_facts", [])
    selected = data.get("pending_selected", [])
    await state.clear()

    if not selected:
        await callback.message.edit_text("❌ Ничего не сохранено.")
        return

    saved = 0
    for idx in selected:
        if 0 <= idx < len(facts):
            await add_user_note(callback.from_user.id, facts[idx])
            saved += 1

    await callback.message.edit_text(
        f"✅ Сохранено {saved} факт(ов).\n\nПосмотреть: 👤 Профиль → 🧠 Заметки астролога."
    )
    await callback.message.answer(
        "Хорошего дня! 🌟",
        reply_markup=main_menu_keyboard(callback.from_user.id),
    )


@router.callback_query(F.data == "mood_facts_cancel")
async def mood_facts_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Факты не сохранены.")
    await callback.message.answer(
        "Хорошего дня! 🌟",
        reply_markup=main_menu_keyboard(callback.from_user.id),
    )


# ============================================================
# СТАТИСТИКА (без изменений)
# ============================================================
@router.callback_query(F.data == "mood_stats")
async def mood_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    history = await get_mood_history(user_id, days=7)
    stats = await get_mood_stats(user_id, days=7)

    if not history:
        text = "📊 СТАТИСТИКА\n\nПока нет записей. Отметьте настроение!"
    else:
        text = "📊 СТАТИСТИКА ЗА 7 ДНЕЙ\n\n"
        for entry in history:
            date_str = entry["mood_date"].strftime("%d.%m")
            text += f"{date_str} — {mood_emoji(entry['mood'])} {mood_name(entry['mood'])}\n"

        if stats["total"] > 0:
            avg_emoji, avg_name = avg_to_mood(stats["avg"])
            text += (
                f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Средний балл: {avg_emoji} {avg_name} ({stats['avg']:.1f}/5)\n"
                f"Записей: {stats['total']}"
            )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📔 Дневник", callback_data="mood_diary")],
        [InlineKeyboardButton(text="📈 График", callback_data="mood_chart")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ГРАФИК
# ============================================================
@router.callback_query(F.data == "mood_chart")
async def mood_chart(callback: CallbackQuery):
    user_id = callback.from_user.id
    history = await get_mood_history(user_id, days=30)

    if len(history) < 2:
        await callback.answer("Нужно минимум 2 записи для графика.", show_alert=True)
        return

    msg = await callback.message.edit_text("📈 Строю график...")
    try:
        chart_path = _build_mood_chart(history)
        if not chart_path:
            await msg.edit_text("❌ Не удалось построить график.")
            return
        try:
            await msg.delete()
        except Exception:
            pass
        photo = FSInputFile(chart_path)
        await callback.message.answer_photo(photo, caption="📈 Настроение за 30 дней")
        await callback.message.answer(
            "Что дальше?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📔 Дневник", callback_data="mood_diary")],
                [InlineKeyboardButton(text="📊 Статистика", callback_data="mood_stats")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
            ]),
        )
        try:
            os.remove(chart_path)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Ошибка графика: {e}")
        try:
            await msg.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


def _build_mood_chart(history: list) -> str:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib не установлен")
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
    ax.set_yticklabels(["😢", "😔", "😐", "🙂", "😊"], fontsize=14)
    ax.set_title("Настроение за 30 дней", color="#FFD700", fontsize=16, pad=15)
    ax.tick_params(colors="#F0F0F0", labelsize=9)
    plt.xticks(rotation=45, ha="right")
    for spine in ax.spines.values():
        spine.set_color("#c9a959")
    plt.tight_layout()
    filename = f"mood_chart_{uuid.uuid4().hex}.png"
    plt.savefig(filename, facecolor="#1a2a3a", dpi=100)
    plt.close()
    return filename
