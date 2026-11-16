#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reply-кнопка «🏠 Меню» + /menu + /cancel.
Запуск: python part_menu_reply.py
"""

from pathlib import Path
import shutil

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")

if not BASE.exists():
    print(f"❌ Папка не найдена: {BASE}")
    exit(1)


def backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak_menu")
    if not bak.exists():
        shutil.copy2(path, bak)


# ============================================================
# 1. Добавляем main_reply_keyboard в keyboards/main.py
# ============================================================
REPLY_KEYBOARD = r'''


# ============================================================
# REPLY-КЛАВИАТУРА (постоянная, внизу)
# ============================================================
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Постоянная reply-клавиатура с кнопкой '🏠 Меню'."""
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Меню")]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Напишите сообщение или нажмите 🏠 Меню",
    )
    return kb
'''

kb_path = BASE / "keyboards" / "main.py"
backup(kb_path)
content = kb_path.read_text(encoding="utf-8")

if "def main_reply_keyboard" not in content:
    content += REPLY_KEYBOARD
    kb_path.write_text(content, encoding="utf-8")
    print("  ✅ keyboards/main.py — добавлена main_reply_keyboard()")
else:
    print("  ℹ️  keyboards/main.py — main_reply_keyboard уже есть")


# ============================================================
# 2. Новый файл handlers/menu_commands.py
# ============================================================
MENU_COMMANDS_PY = r'''import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.main import main_menu_keyboard, main_reply_keyboard
from database.postgres_db import is_paid, is_admin
from config import FREE_MODE

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# 🏠 МЕНЮ — reply-кнопка и команда
# ============================================================
@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Команда /menu — быстрый возврат в главное меню."""
    await state.clear()
    await _show_main_menu(message)


@router.message(F.text == "🏠 Меню")
async def reply_menu(message: Message, state: FSMContext):
    """Reply-кнопка '🏠 Меню'."""
    await state.clear()
    await _show_main_menu(message)


async def _show_main_menu(message: Message):
    """Показ главного меню с reply-клавиатурой."""
    user_id = message.from_user.id

    try:
        paid = await is_paid(user_id)
        admin = await is_admin(user_id)
    except Exception:
        paid = False
        admin = False

    if not paid and not admin and not FREE_MODE:
        from keyboards.main import payment_keyboard
        text = "🔒 Подписка не активна.\n\nВыберите тариф:"
        try:
            await message.answer(
                text,
                reply_markup=await payment_keyboard(),
            )
        except Exception:
            pass
        # Reply-клавиатура отдельно
        try:
            await message.answer("Меню доступно внизу.", reply_markup=main_reply_keyboard())
        except Exception:
            pass
        return

    try:
        await message.answer(
            "🏠 Главное меню:",
            reply_markup=main_menu_keyboard(user_id)
        )
    except Exception:
        pass

    # Reply-клавиатура отдельным сообщением, чтобы была всегда
    try:
        await message.answer(
            "👇 Меню всегда доступно кнопкой внизу.",
            reply_markup=main_reply_keyboard()
        )
    except Exception:
        pass


# ============================================================
# ❌ CANCEL — умный возврат
# ============================================================
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Умный /cancel — возврат в предыдущее меню или в главное."""
    current_state = await state.get_state()
    user_id = message.from_user.id

    # Пытаемся удалить сообщение /cancel
    try:
        await message.delete()
    except Exception:
        pass

    # Если пользователь был в FSM — сообщаем об отмене
    if current_state:
        await state.clear()
        await message.answer("✅ Действие отменено.")
    else:
        await message.answer("Нечего отменять.")

    # Показываем главное меню
    await _show_main_menu(message)
'''


# ============================================================
# 3. Обработка reply-кнопки через callback-сценарии из меню
# ============================================================
# Хак: чтобы reply-клавиатура оставалась, добавим её к main_menu
# Это делаем через патч handlers/start.py — обернём возврат в меню

menu_path = BASE / "handlers" / "menu_commands.py"
menu_path.write_text(MENU_COMMANDS_PY, encoding="utf-8")
print("  ✅ handlers/menu_commands.py — создан")


# ============================================================
# 4. Добавить роутер в handlers/__init__.py
# ============================================================
init_path = BASE / "handlers" / "__init__.py"
backup(init_path)
content = init_path.read_text(encoding="utf-8")

if "menu_commands" not in content:
    # Добавляем импорт в конец и в __all__
    lines = content.rstrip().split("\n")
    # Найдём блок __all__
    for i, line in enumerate(lines):
        if line.startswith("__all__"):
            # Вставляем импорт перед __all__
            lines.insert(i, "from .menu_commands import router as menu_router")
            # Добавляем в __all__ (после открывающей скобки)
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "]":
                    lines.insert(j, "    'menu_router',")
                    break
            break

    content = "\n".join(lines) + "\n"
    init_path.write_text(content, encoding="utf-8")
    print("  ✅ handlers/__init__.py — menu_router подключён")
else:
    print("  ℹ️  handlers/__init__.py — menu_router уже есть")


# ============================================================
# 5. Патч handlers/start.py — отправить reply-клавиатуру при /start
# ============================================================
start_path = BASE / "handlers" / "start.py"
backup(start_path)
content = start_path.read_text(encoding="utf-8")

# Импорт main_reply_keyboard
if "main_reply_keyboard" not in content:
    content = content.replace(
        "from keyboards.main import welcome_keyboard, main_menu_keyboard, payment_keyboard",
        "from keyboards.main import welcome_keyboard, main_menu_keyboard, payment_keyboard, main_reply_keyboard"
    )
    print("  ✅ handlers/start.py — добавлен импорт main_reply_keyboard")

# Патч welcome_keyboard — отправить reply-клавиатуру ДО меню
OLD_WELCOME = '''        text = f"🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!"
        await message.answer(text, reply_markup=await welcome_keyboard())
        return'''
NEW_WELCOME = '''        text = f"🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!"
        await message.answer(
            "👇 Меню всегда доступно кнопкой внизу.",
            reply_markup=main_reply_keyboard()
        )
        await message.answer(text, reply_markup=await welcome_keyboard())
        return'''

if OLD_WELCOME in content:
    content = content.replace(OLD_WELCOME, NEW_WELCOME, 1)
    print("  ✅ handlers/start.py — reply-клавиатура приветствия")

# Патч финальной отправки
OLD_FINAL = '''    text = f"🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!"
    await message.answer(text, reply_markup=await welcome_keyboard())'''
NEW_FINAL = '''    text = f"🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!"
    await message.answer(
        "👇 Меню всегда доступно кнопкой внизу.",
        reply_markup=main_reply_keyboard()
    )
    await message.answer(text, reply_markup=await welcome_keyboard())'''

if OLD_FINAL in content:
    content = content.replace(OLD_FINAL, NEW_FINAL, 1)
    print("  ✅ handlers/start.py — reply-клавиатура финального меню")

start_path.write_text(content, encoding="utf-8")


# ============================================================
# 6. Патч webhook_bot.py и bot_prod.py — добавить menu_router
# ============================================================
for fname in ["webhook_bot.py", "bot_prod.py"]:
    fpath = BASE / fname
    if not fpath.exists():
        continue

    backup(fpath)
    content = fpath.read_text(encoding="utf-8")

    if "menu_router" in content:
        print(f"  ℹ️  {fname} — menu_router уже есть")
        continue

    # Добавляем импорт
    if "from handlers.start import router as start_router" in content:
        content = content.replace(
            "from handlers.start import router as start_router",
            "from handlers.start import router as start_router\nfrom handlers.menu_commands import router as menu_router"
        )

    # Подключаем роутер (сразу после start_router)
    if "dp.include_router(start_router)" in content:
        content = content.replace(
            "dp.include_router(start_router)",
            "dp.include_router(start_router)\ndp.include_router(menu_router)"
        )

    fpath.write_text(content, encoding="utf-8")
    print(f"  ✅ {fname} — menu_router подключён")


print()
print("=" * 60)
print("ГОТОВО!")
print("=" * 60)
print()
print("Что работает:")
print("  • Reply-кнопка «🏠 Меню» — всегда внизу")
print("  • /menu — команда возврата в меню")
print("  • /cancel — умный возврат")
print()
print("Дальше:")
print("  cd C:\\Users\\User\\Desktop\\AstroBot_clean")
print("  python webhook_bot.py")
print()
print("Проверь:")
print("  1. /start — появится reply-кнопка «🏠 Меню»")
print("  2. Зайди в AI-диалог → нажми «🏠 Меню»")
print("  3. /cancel — вернёт в меню")