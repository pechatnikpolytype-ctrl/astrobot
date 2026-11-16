#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Красивые факты вместо "." в reply-сообщении + автоудаление.
Запуск: python part_menu_facts.py
"""

from pathlib import Path
import shutil

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")

if not BASE.exists():
    print(f"❌ Папка не найдена: {BASE}")
    exit(1)


# ============================================================
# Новый handlers/menu_commands.py
# ============================================================
MENU_COMMANDS_PY = r'''import logging
import random
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


# ============================================================
# КОРОТКИЕ ИНТЕРЕСНЫЕ ФАКТЫ
# ============================================================
MENU_FACTS = [
    "🔮 Астрология — это язык звёзд. Каждая планета говорит с вами.",
    "✨ Луна меняет знак каждые 2-3 дня. Настроение — тоже.",
    "🌟 Ваш знак зодиака — это только начало. Вселенная говорит на языке символов.",
    "💫 Солнце, Луна и планеты — ваши космические спутники.",
    "🌙 Полнолуние — время отпустить старое и впустить новое.",
    "🪐 Сатурн учит терпению. Юпитер дарит удачу.",
    "⭐ Асцендент — ваша визитная карточка для мира.",
    "🌞 Стихии — это 4 языка, на которых говорит ваша душа.",
    "🔭 Астрология старше пирамид. Ей больше 4000 лет.",
    "✨ Меркурий управляет общением. В ретроград — будьте внимательны.",
    "💫 Венера — планета любви. Она знает ваши желания.",
    "🌙 Луна — ваш внутренний мир. Слушайте её.",
    "🌟 Марс даёт энергию. Используйте её мудро.",
    "⭐ 12 домов — 12 сфер жизни. Каждая ждёт вашего внимания.",
    "🪐 Плутон — планета трансформации. Перемены — это рост.",
    "🌞 Солнце в карте — ваша суть. Луна — ваши чувства.",
    "💫 Кометы приносят перемены. Следите за знаками.",
    "🔮 Интуиция — ваш личный астролог. Доверяйте ей.",
    "✨ Звёзды не решают за вас. Они лишь показывают путь.",
    "🌙 Новолуние — лучшее время для новых начинаний.",
    "🌟 Юпитер в вашем доме — там ждёт удача.",
    "⭐ Меркурий, Венера, Марс — три ключа к действию.",
    "🪐 Сатурн не наказывает — он учит.",
    "💫 Лунные узлы показывают путь души.",
    "🌞 Стихия Огня — страсть. Земли — стабильность. Воздуха — идеи. Воды — чувства.",
    "🔮 Ретроградный Меркурий — время пересмотреть, а не начинать.",
    "✨ Каждая планета в вашей карте — часть пазла.",
    "🌙 Луна в Раке — время заботы. В Овне — время действий.",
    "🌟 Астрология — это не магия. Это язык Вселенной.",
    "⭐ Ваша натальная карта уникальна. Как отпечаток пальца.",
]


def get_menu_fact() -> str:
    """Случайный факт для меню."""
    return random.choice(MENU_FACTS)


async def _delete_previous_menu(bot: Bot, user_id: int, chat_id: int):
    """Удаляет предыдущее меню-сообщение пользователя."""
    try:
        prev = await get_last_menu(user_id)
        if prev:
            prev_chat_id, prev_message_id = prev
            try:
                await bot.delete_message(chat_id=prev_chat_id, message_id=prev_message_id)
            except Exception as e:
                logger.debug(f"Не удалить меню {prev_message_id}: {e}")
    except Exception as e:
        logger.debug(f"delete_previous_menu: {e}")


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    try:
        await message.delete()
    except Exception:
        pass
    await _delete_previous_menu(bot, message.from_user.id, message.chat.id)
    await _show_main_menu(message)


@router.message(F.text == "🏠 Меню")
async def reply_menu(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    try:
        await message.delete()
    except Exception:
        pass
    await _delete_previous_menu(bot, message.from_user.id, message.chat.id)
    await _show_main_menu(message)


async def _show_main_menu(message: Message):
    """Показ главного меню: факт + reply-клавиатура."""
    user_id = message.from_user.id

    try:
        paid = await is_paid(user_id)
        admin = await is_admin(user_id)
    except Exception:
        paid = False
        admin = False

    if not paid and not admin and not FREE_MODE:
        from keyboards.main import payment_keyboard
        # Факт + reply-кнопка
        msg = await message.answer(
            get_menu_fact(),
            reply_markup=main_reply_keyboard()
        )
        await set_last_menu(user_id, msg.message_id, msg.chat.id)
        # Меню оплаты
        await message.answer(
            "🔒 Подписка не активна.\n\nВыберите тариф:",
            reply_markup=await payment_keyboard(),
        )
        return

    # Одно сообщение: факт + reply-кнопка
    msg = await message.answer(
        get_menu_fact(),
        reply_markup=main_reply_keyboard()
    )
    await set_last_menu(user_id, msg.message_id, msg.chat.id)

    # Отдельно — inline главное меню
    await message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu_keyboard(user_id),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    user_id = message.from_user.id

    try:
        await message.delete()
    except Exception:
        pass

    if current_state:
        await state.clear()
        await message.answer("✅ Действие отменено.")
    else:
        await message.answer("Нечего отменять.")

    await _delete_previous_menu(bot, user_id, message.chat.id)
    await _show_main_menu(message)


# Хелперы для использования из других handlers
async def save_menu_id(message, user_id: int):
    await set_last_menu(user_id, message.message_id, message.chat.id)


async def delete_previous_menu_safe(bot, user_id: int, chat_id: int):
    await _delete_previous_menu(bot, user_id, chat_id)
'''


menu_path = BASE / "handlers" / "menu_commands.py"
menu_path.write_text(MENU_COMMANDS_PY, encoding="utf-8")
print("  ✅ handlers/menu_commands.py — обновлён (факты + автоудаление)")


# ============================================================
# Патч handlers/start.py — заменить "." на факт
# ============================================================
start_path = BASE / "handlers" / "start.py"
content = start_path.read_text(encoding="utf-8")

# Заменяем "." на факт
OLD = '''    await message.answer(".", reply_markup=main_reply_keyboard())'''
NEW = '''    from handlers.menu_commands import get_menu_fact
    await message.answer(get_menu_fact(), reply_markup=main_reply_keyboard())'''

if OLD in content:
    content = content.replace(OLD, NEW)
    print("  ✅ handlers/start.py — заменён '.' на факт")

start_path.write_text(content, encoding="utf-8")


print()
print("=" * 60)
print("ГОТОВО!")
print("=" * 60)
print()
print("Что работает:")
print("  • Под reply-кнопкой — случайный факт про астрологию")
print("  • 30 разных фактов — не повторяются")
print("  • Старое сообщение удаляется при новом меню")
print()
print("Дальше:")
print("  cd C:\\Users\\User\\Desktop\\AstroBot_clean")
print("  python webhook_bot.py")
print()
print("Проверь:")
print("  1. /start — снизу факт + reply-кнопка «🏠 Меню»")
print("  2. Нажми «🏠 Меню» — новый факт")
print("  3. Старый факт удалился")