"""Обработчик раскладов Таро."""

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
from database.postgres_db import is_paid, is_admin
from config import ADMINS

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# FSM
# ============================================================
class TarotStates(StatesGroup):
    waiting_question = State()


# ============================================================
# КЛАВИАТУРЫ
# ============================================================
def tarot_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Сделать расклад", callback_data="tarot_new")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])


def tarot_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Ещё расклад", callback_data="tarot_new")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])


def tarot_pay_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить подписку", callback_data="check_status")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])


# ============================================================
# ГЛАВНОЕ МЕНЮ ТАРО
# ============================================================
@router.callback_query(F.data == "tarot_menu")
async def tarot_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id

    # Проверка подписки
    try:
        paid = await is_paid(user_id)
        admin = await is_admin(user_id)
    except Exception:
        paid, admin = False, False

    total = get_total_cards()
    if total == 0:
        await callback.answer("❌ Карты не загружены", show_alert=True)
        return

    text = (
        "🃏 ТАРО — ГАДАНИЕ И СОВЕТЫ\n\n"
        "Задайте свой вопрос — и карты Таро дадут ответ "
        "вместе с персональным толкованием от AI-таролога.\n\n"
        "💡 Как это работает:\n"
        "1. Вы пишете вопрос (про любовь, работу, будущее)\n"
        "2. Мы вытягиваем 3 карты\n"
        "3. AI даёт развёрнутое толкование\n\n"
        "⚠️ Один и тот же вопрос в один день — один и тот же расклад.\n"
        "На следующий день — новый."
    )

    if not paid and not admin:
        text += "\n\n🔒 Функция доступна по подписке."
        try:
            await callback.message.edit_text(text, reply_markup=tarot_pay_keyboard())
        except Exception:
            await callback.message.answer(text, reply_markup=tarot_pay_keyboard())
        return

    try:
        await callback.message.edit_text(text, reply_markup=tarot_menu_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=tarot_menu_keyboard())


# ============================================================
# НАЧАЛО РАСКЛАДА
# ============================================================
@router.callback_query(F.data == "tarot_new")
async def tarot_new_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    try:
        paid = await is_paid(user_id)
        admin = await is_admin(user_id)
    except Exception:
        paid, admin = False, False

    if not paid and not admin:
        await callback.answer("🔒 Требуется подписка", show_alert=True)
        return

    await state.set_state(TarotStates.waiting_question)
    try:
        await callback.message.edit_text(
            "🔮 ЗАДАЙТЕ ВАШ ВОПРОС\n\n"
            "Напишите вопрос, на который хотите получить ответ.\n\n"
            "Примеры:\n"
            "• Что меня ждёт в отношениях?\n"
            "• Стоит ли менять работу?\n"
            "• Что ждёт меня в ближайший месяц?\n\n"
            "/cancel — отмена",
        )
    except Exception:
        await callback.message.answer(
            "🔮 ЗАДАЙТЕ ВАШ ВОПРОС\n\n"
            "Напишите вопрос.\n\n/cancel — отмена"
        )


# ============================================================
# ОБРАБОТКА ВОПРОСА
# ============================================================
@router.message(TarotStates.waiting_question)
async def tarot_process_question(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    question = (message.text or "").strip()

    if question == "/cancel":
        await message.answer("Отменено.")
        return

    if len(question) < 5:
        await message.answer("❌ Вопрос слишком короткий. Опишите подробнее.")
        return

    if len(question) > 500:
        question = question[:500]

    # Сообщение о обработке
    processing = await message.answer("🔮 Тасуем карты... Это займёт 5-15 секунд.")

    try:
        result = await get_or_create_reading(user_id, question, count=3)

        if "error" in result:
            await processing.edit_text(f"❌ Ошибка: {result['error']}")
            return

        cards = result["cards"]
        ai_answer = result["ai_answer"]
        from_cache = result.get("from_cache", False)

        try:
            await processing.delete()
        except Exception:
            pass

        # 1. Показываем карты (3 картинки)
        positions = get_positions(question)
        for i, card_key in enumerate(cards):
            img_path = get_card_image(card_key)
            caption = get_card_caption(card_key)
            if i < len(positions):
                caption = f"{positions[i]}: {caption}"

            if img_path and img_path.exists():
                try:
                    await message.answer_photo(
                        FSInputFile(img_path),
                        caption=caption,
                    )
                except Exception as e:
                    logger.warning(f"Не отправить карту {card_key}: {e}")
                    await message.answer(caption)
            else:
                await message.answer(caption)

        # 2. AI-толкование
        cache_note = " (из кэша)" if from_cache else ""
        answer_text = (
            f"🤖 ТОЛКОВАНИЕ АСТРОЛОГА{cache_note}:\n\n"
            f"{ai_answer}"
        )
        if len(answer_text) > 4000:
            for i in range(0, len(answer_text), 4000):
                await message.answer(answer_text[i:i+4000])
        else:
            await message.answer(answer_text)

        # 3. Кнопки
        await message.answer(
            "Хотите ещё один расклад?",
            reply_markup=tarot_back_keyboard(),
        )

    except Exception as e:
        logger.error(f"Ошибка таро: {e}")
        try:
            await processing.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            await message.answer(f"❌ Ошибка: {e}")
