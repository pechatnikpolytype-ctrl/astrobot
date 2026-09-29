import asyncio
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import AIQuestionStates
from ai_service_n1n import ai_service
from keyboards.main import ai_question_keyboard, back_to_menu_keyboard
from utils.validators import validator
from database.postgres_db import (
    get_user_ai_limit, get_ai_usage, increment_ai_usage,
    add_user_note, get_user, get_user_notes,
)
from config import ADMINS

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# МЕНЮ
# ============================================================
@router.callback_query(F.data == "ai_question")
async def ai_question_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)

    if limit == -1:
        limit_text = "🤖 AI-лимит: ♾️ без лимита"
    else:
        left = max(0, limit - usage)
        limit_text = f"🤖 AI-лимит: осталось {left}/{limit}"

    text = (
        "🤖 АСТРОЛОГ AI\n\n"
        "Задайте любой вопрос о гороскопах, знаках зодиака, "
        "совместимости или влиянии планет!\n\n"
        "📝 Примеры:\n"
        "  • Что ждёт Овна на этой неделе?\n"
        "  • Какая совместимость у Льва и Скорпиона?\n"
        "  • Как ретроградный Меркурий влияет на меня?\n\n"
        f"{limit_text}\n\n"
        "💡 AI знает ваш профиль и отвечает персонально!"
    )

    try:
        await callback.message.edit_text(text, reply_markup=ai_question_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=ai_question_keyboard())


@router.callback_query(F.data == "ask_ai")
async def start_ai_question(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)

    if limit != -1 and usage >= limit:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить Премиум", callback_data="check_status")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ])
        try:
            await callback.message.edit_text(
                "⚠️ AI-ЛИМИТ ИСЧЕРПАН\n\n"
                f"Вы задали {usage}/{limit} вопросов сегодня.\n"
                "Лимит обновится в 00:00 UTC.\n\n"
                "💎 Купите Премиум — 100 запросов/день.",
                reply_markup=keyboard
            )
        except Exception:
            await callback.message.answer(
                "⚠️ AI-ЛИМИТ ИСЧЕРПАН\n\n"
                f"Вы задали {usage}/{limit} вопросов сегодня.",
                reply_markup=keyboard
            )
        return

    await state.set_state(AIQuestionStates.waiting_question)
    try:
        await callback.message.edit_text(
            "🔮 ЗАДАЙТЕ ВАШ ВОПРОС\n\n"
            "Напишите любой астрологический вопрос.\n\n"
            "Чем больше вы расскажете о себе в профиле, "
            "тем точнее будет ответ.\n\n"
            "/cancel — отмена"
        )
    except Exception:
        await callback.message.answer(
            "🔮 ЗАДАЙТЕ ВАШ ВОПРОС\n\n/cancel — отмена"
        )


# ============================================================
# ОБРАБОТКА ВОПРОСА
# ============================================================
@router.message(AIQuestionStates.waiting_question)
async def process_ai_question(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    if message.text == "/cancel":
        await message.answer("Отменено", reply_markup=back_to_menu_keyboard())
        return

    valid, result = validator.validate_question(message.text)
    if not valid:
        await message.answer(
            f"❌ {result}\n\nПожалуйста, задайте осмысленный вопрос.",
            reply_markup=ai_question_keyboard()
        )
        return

    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)

    if limit != -1 and usage >= limit:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить Премиум", callback_data="check_status")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ])
        await message.answer(
            "⚠️ AI-ЛИМИТ ИСЧЕРПАН\n\n"
            f"Вы задали {usage}/{limit} вопросов сегодня.",
            reply_markup=keyboard
        )
        return

    processing_msg = await message.answer("🔮 Астролог AI анализирует ваш вопрос...")

    async def update_thinking():
        await asyncio.sleep(3)
        try:
            await processing_msg.edit_text(
                "🤖 AI ДУМАЕТ...\n\n"
                "Это может занять 10-30 секунд.\n"
                "Пожалуйста, подождите."
            )
        except Exception:
            pass

    thinking_task = asyncio.create_task(update_thinking())

    try:
        response = await ai_service.process_question(user_id, result)
        thinking_task.cancel()

        try:
            await processing_msg.delete()
        except Exception:
            pass

        answer = response.get("message", "Ошибка ответа")
        from_cache = response.get("from_cache", False)
        facts = response.get("facts", [])

        if not from_cache:
            await increment_ai_usage(user_id)

        admin_marker = ""
        if user_id in ADMINS:
            admin_marker = f"\n\n🤖 Модель: {response.get('model', '?')}"

        await message.answer(
            f"🤖 ОТВЕТ АСТРОЛОГА:\n\n{answer}{admin_marker}",
            reply_markup=ai_question_keyboard()
        )

        # Остаток лимита
        if limit != -1:
            new_usage = await get_ai_usage(user_id)
            left = max(0, limit - new_usage)
            if left <= 5 and left > 0:
                await message.answer(
                    f"⚠️ У вас осталось {left} запросов на сегодня."
                )
            elif left == 0:
                await message.answer(
                    "⚠️ AI-лимит исчерпан на сегодня. "
                    "Обновится в 00:00 UTC."
                )

        # Факты
        if facts:
            existing_notes = await get_user_notes(user_id)
            existing_texts = [n["note"] for n in existing_notes]
            new_facts = [f for f in facts if f not in existing_texts]

            if new_facts:
                await show_facts_confirmation(message, state, new_facts)
            else:
                await message.answer(
                    "✅ AI заметил, что вы уже рассказывали об этом ранее.\n"
                    "Новые факты не найдены."
                )
        else:
            # Если вопрос личный, но фактов нет — предложить профиль
            q_lower = message.text.lower()
            personal_pronouns = ["я ", "мне ", "меня ", "мой ", "моя ", "мои "]
            if any(p in q_lower for p in personal_pronouns):
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="👤 Заполнить профиль", callback_data="profile_edit")],
                    [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
                ])
                await message.answer(
                    "💡 Хотите, чтобы AI знал о вас больше?\n\n"
                    "Заполните профиль — и ответы станут точнее.",
                    reply_markup=keyboard
                )

    except Exception as e:
        thinking_task.cancel()
        logger.error(f"Ошибка AI: {e}")
        try:
            await processing_msg.edit_text(
                "❌ Произошла ошибка. Попробуйте позже.",
                reply_markup=ai_question_keyboard()
            )
        except Exception:
            await message.answer("❌ Произошла ошибка.", reply_markup=ai_question_keyboard())


# ============================================================
# ФАКТЫ
# ============================================================
async def show_facts_confirmation(message: Message, state: FSMContext, facts: list):
    await state.update_data(
        facts=facts,
        selected=list(range(len(facts))),
    )
    keyboard = _build_facts_keyboard(facts, list(range(len(facts))))
    await message.answer(
        "🧠 AI ХОЧЕТ ЗАПОМНИТЬ О ВАС\n\n"
        "Эти факты будут использоваться для персонализации:\n\n"
        "Нажмите на факт, чтобы выбрать/убрать.\n"
        "Затем нажмите «💾 Сохранить».\n\n"
        "⏱️ Если не ответите за 5 минут — факты НЕ сохранятся.",
        reply_markup=keyboard
    )


def _build_facts_keyboard(facts: list, selected: list):
    buttons = []
    for i, fact in enumerate(facts):
        mark = "✅" if i in selected else "☐"
        short = fact[:40] + "..." if len(fact) > 40 else fact
        buttons.append([InlineKeyboardButton(
            text=f"{mark} {short}",
            callback_data=f"fact_toggle_{i}"
        )])
    buttons.append([
        InlineKeyboardButton(text="💾 Сохранить", callback_data="facts_save"),
        InlineKeyboardButton(text="❌ Не надо", callback_data="facts_cancel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("fact_toggle_"))
async def fact_toggle(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    facts = data.get("facts", [])
    selected = data.get("selected", [])
    idx = int(callback.data.replace("fact_toggle_", ""))

    if idx in selected:
        selected.remove(idx)
    else:
        selected.append(idx)

    await state.update_data(selected=selected)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=_build_facts_keyboard(facts, selected)
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "facts_save")
async def facts_save(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    facts = data.get("facts", [])
    selected = data.get("selected", [])
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
        f"✅ Сохранено {saved} факт(ов).\n\n"
        "Теперь AI знает о вас больше.\n"
        "Посмотреть: 👤 Профиль → 🧠 AI-заметки."
    )


@router.callback_query(F.data == "facts_cancel")
async def facts_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Факты не сохранены.\n\n"
        "Заполнить профиль вручную: 👤 Профиль."
    )


# ============================================================
# ПРИМЕРЫ
# ============================================================
@router.callback_query(F.data == "ai_examples")
async def ai_examples(callback: CallbackQuery):
    examples = (
        "📝 ПРИМЕРЫ ВОПРОСОВ\n\n"
        "🔮 О гороскопе:\n"
        "  • Что ждёт меня на этой неделе?\n"
        "  • Какой день лучший для важных дел?\n\n"
        "💕 О любви:\n"
        "  • Подходит ли мне партнёр-Скорпион?\n"
        "  • Как улучшить отношения?\n\n"
        "💼 О карьере:\n"
        "  • Стоит ли менять работу?\n"
        "  • Какая профессия мне подходит?\n\n"
        "🌟 О себе:\n"
        "  • Что говорит моя натальная карта?\n"
        "  • Какие у меня сильные стороны?\n\n"
        "✨ Задавайте свои вопросы!"
    )
    try:
        await callback.message.answer(examples)
    except Exception as e:
        logger.error(f"Ошибка ai_examples: {e}")
