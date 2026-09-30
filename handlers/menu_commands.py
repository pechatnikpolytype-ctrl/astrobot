import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.main import main_menu_keyboard, main_reply_keyboard
from database.postgres_db import (
    is_paid, is_admin, get_last_menu, set_last_menu, clear_last_menu,
)
from config import FREE_MODE

logger = logging.getLogger(__name__)
router = Router()


async def _delete_previous_menu(bot: Bot, user_id: int, chat_id: int):
    """Удаляет предыдущее меню-сообщение пользователя."""
    try:
        prev = await get_last_menu(user_id)
        if prev:
            prev_chat_id, prev_message_id = prev
            try:
                await bot.delete_message(chat_id=prev_chat_id, message_id=prev_message_id)
            except Exception as e:
                logger.debug(f"Не удалось удалить меню {prev_message_id}: {e}")
    except Exception as e:
        logger.debug(f"delete_previous_menu: {e}")


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, bot: Bot):
    """Команда /menu — быстрый возврат в главное меню."""
    await state.clear()
    # Удаляем сообщение /menu
    try:
        await message.delete()
    except Exception:
        pass
    # Удаляем предыдущее меню
    await _delete_previous_menu(bot, message.from_user.id, message.chat.id)
    await _show_main_menu(message)


@router.message(F.text == "🏠 Меню")
async def reply_menu(message: Message, state: FSMContext, bot: Bot):
    """Reply-кнопка '🏠 Меню'."""
    await state.clear()
    # Удаляем сообщение с reply-кнопкой (само "🏠 Меню")
    try:
        await message.delete()
    except Exception:
        pass
    # Удаляем предыдущее меню
    await _delete_previous_menu(bot, message.from_user.id, message.chat.id)
    await _show_main_menu(message)


async def _show_main_menu(message: Message):
    """Показ главного меню с автоудалением старого."""
    user_id = message.from_user.id

    try:
        paid = await is_paid(user_id)
        admin = await is_admin(user_id)
    except Exception:
        paid = False
        admin = False

    if not paid and not admin and not FREE_MODE:
        from keyboards.main import payment_keyboard
        msg = await message.answer(
            "🔒 Подписка не активна.\n\nВыберите тариф:",
            reply_markup=await payment_keyboard()
        )
        # Сохраняем ID меню для следующего удаления
        await set_last_menu(user_id, msg.message_id, msg.chat.id)
        # Reply-клавиатура
        r = await message.answer(
            "Меню всегда внизу 👇",
            reply_markup=main_reply_keyboard()
        )
        return

    msg = await message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu_keyboard(user_id)
    )
    # Сохраняем ID меню
    await set_last_menu(user_id, msg.message_id, msg.chat.id)

    # Reply-клавиатура — отдельным сообщением
    r = await message.answer(
        "Меню всегда внизу 👇",
        reply_markup=main_reply_keyboard()
    )


# ============================================================
# ❌ CANCEL — умный возврат + автоудаление
# ============================================================
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, bot: Bot):
    """Умный /cancel."""
    current_state = await state.get_state()
    user_id = message.from_user.id

    # Удаляем сообщение /cancel
    try:
        await message.delete()
    except Exception:
        pass

    if current_state:
        await state.clear()
        info = await message.answer("✅ Действие отменено.")
    else:
        info = await message.answer("Нечего отменять.")

    # Удаляем предыдущее меню
    await _delete_previous_menu(bot, user_id, message.chat.id)

    # Показываем главное меню
    await _show_main_menu(message)


# ============================================================
# ХЕЛПЕР: сохранить ID меню (используется из других handlers)
# ============================================================
async def save_menu_id(message, user_id: int):
    """Сохраняет ID меню-сообщения. Для использования из других handlers."""
    await set_last_menu(user_id, message.message_id, message.chat.id)


async def delete_old_and_send_new_menu(bot, user_id: int, chat_id: int, message_text: str, reply_markup):
    """
    Удаляет старое меню и отправляет новое.
    Возвращает отправленное сообщение.
    """
    await _delete_previous_menu(bot, user_id, chat_id)
    return None  # вызывающий сам отправляет
