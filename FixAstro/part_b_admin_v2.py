#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Part B v2: Управление админами (исправлено).
Запуск: python part_b_admin_v2.py
"""

from pathlib import Path
import shutil

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")

if not BASE.exists():
    print(f"❌ Папка не найдена: {BASE}")
    exit(1)


def backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak_b")
    if not bak.exists():
        shutil.copy2(path, bak)


# ============================================================
# 1. APPEND функций админов в database/postgres_db.py
# ============================================================
DB_APPEND = r'''

# ============================================================
# УПРАВЛЕНИЕ АДМИНАМИ
# ============================================================
async def get_extra_admins() -> list:
    data = await get_setting("extra_admins", [])
    if not isinstance(data, list):
        return []
    result = []
    for x in data:
        try:
            result.append(int(x))
        except (ValueError, TypeError):
            pass
    return result


async def add_extra_admin(user_id: int) -> bool:
    current = await get_extra_admins()
    if user_id in current:
        return False
    current.append(int(user_id))
    await set_setting("extra_admins", current)
    return True


async def remove_extra_admin(user_id: int) -> bool:
    current = await get_extra_admins()
    if user_id not in current:
        return False
    current.remove(int(user_id))
    await set_setting("extra_admins", current)
    return True


async def get_all_admins() -> list:
    from config import ADMINS as MAIN_ADMINS
    extra = await get_extra_admins()
    return list(set(MAIN_ADMINS + extra))


async def is_admin(user_id: int) -> bool:
    from config import ADMINS as MAIN_ADMINS
    if user_id in MAIN_ADMINS:
        return True
    extra = await get_extra_admins()
    return user_id in extra


async def is_main_admin(user_id: int) -> bool:
    from config import ADMINS as MAIN_ADMINS
    return user_id in MAIN_ADMINS
'''


# ============================================================
# 2. APPEND роутеров (исправлено!)
# ============================================================
ADMIN_APPEND = r'''

# ============================================================
# 👑 УПРАВЛЕНИЕ АДМИНАМИ
# ============================================================
class AdminManageStates(StatesGroup):
    waiting_new_admin_id = State()


@router.callback_query(F.data == "admin_manage_admins")
async def admin_manage_admins(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    from database.postgres_db import is_main_admin, get_extra_admins
    from config import ADMINS as MAIN_ADMINS

    is_main = await is_main_admin(callback.from_user.id)
    main_list = "\n".join([f"  • {a}" for a in MAIN_ADMINS]) or "  (нет)"
    extra = await get_extra_admins()
    extra_list = "\n".join([f"  • {a}" for a in extra]) if extra else "  (нет)"

    text = (
        f"👑 УПРАВЛЕНИЕ АДМИНАМИ\n\n"
        f"🔑 Главные (из .env):\n{main_list}\n\n"
        f"➕ Дополнительные:\n{extra_list}\n\n"
    )

    if is_main:
        text += "💡 Вы можете добавлять и удалять."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить", callback_data="admins_add")],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data="admins_remove")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
        ])
    else:
        text += "⚠️ Только главный админ."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
        ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "admins_add")
async def admins_add_start(callback: CallbackQuery, state: FSMContext):
    from database.postgres_db import is_main_admin
    if not await is_main_admin(callback.from_user.id):
        await callback.answer("❌ Только главный админ.", show_alert=True)
        return
    await state.set_state(AdminManageStates.waiting_new_admin_id)
    await callback.message.edit_text(
        "👑 ДОБАВИТЬ АДМИНА\n\n"
        "Введите ID нового админа:\n"
        "Например: 123456789\n\n"
        "⚠️ Новый админ получит полный доступ.\n\n"
        "/cancel — отмена"
    )


@router.message(AdminManageStates.waiting_new_admin_id)
async def admins_add_save(message: Message, state: FSMContext):
    from database.postgres_db import is_main_admin, add_extra_admin
    if not await is_main_admin(message.from_user.id):
        await state.clear()
        return
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    try:
        new_id = int(message.text.strip())
        if new_id <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите положительное число (ID).")
        return

    from config import ADMINS as MAIN_ADMINS
    if new_id in MAIN_ADMINS:
        await message.answer("❌ Уже главный админ.")
        await state.clear()
        return

    success = await add_extra_admin(new_id)
    if success:
        await message.answer(f"✅ Админ {new_id} добавлен.")
        try:
            from loader import bot
            await bot.send_message(
                new_id,
                "👑 Вам предоставлены права администратора AstroBot.\n\n"
                "Теперь вам доступна /admin."
            )
        except Exception:
            pass
    else:
        await message.answer(f"❌ {new_id} уже админ.")
    await state.clear()
    await show_admin_panel(message)


@router.callback_query(F.data == "admins_remove")
async def admins_remove_menu(callback: CallbackQuery):
    from database.postgres_db import is_main_admin, get_extra_admins
    if not await is_main_admin(callback.from_user.id):
        await callback.answer("❌ Только главный админ.", show_alert=True)
        return
    extra = await get_extra_admins()
    if not extra:
        await callback.answer("Нет доп. админов.", show_alert=True)
        return
    buttons = []
    for admin_id in extra:
        buttons.append([InlineKeyboardButton(
            text=f"🗑️ {admin_id}",
            callback_data=f"admin_rm_{admin_id}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_manage_admins")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("🗑️ ВЫБЕРИТЕ АДМИНА", reply_markup=keyboard)


# ВАЖНО: сначала более специфичный фильтр (do_), потом общий (rm_)
@router.callback_query(F.data.startswith("admin_rm_do_"))
async def admins_remove_do(callback: CallbackQuery):
    from database.postgres_db import is_main_admin, remove_extra_admin
    if not await is_main_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    target_id = int(callback.data.replace("admin_rm_do_", ""))
    success = await remove_extra_admin(target_id)
    if success:
        await callback.answer(f"✅ Админ {target_id} удалён", show_alert=True)
        try:
            from loader import bot
            await bot.send_message(
                target_id,
                "⚠️ Ваши права администратора отозваны."
            )
        except Exception:
            pass
    else:
        await callback.answer("❌ Не найден", show_alert=True)
    await admin_manage_admins(callback)


@router.callback_query(F.data.startswith("admin_rm_"))
async def admins_remove_confirm(callback: CallbackQuery):
    from database.postgres_db import is_main_admin
    if not await is_main_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    # Парсим только если не do_
    raw = callback.data.replace("admin_rm_", "")
    if raw.startswith("do_"):
        return  # на всякий случай
    try:
        target_id = int(raw)
    except ValueError:
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data=f"admin_rm_do_{target_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_manage_admins")],
    ])
    await callback.message.edit_text(
        f"⚠️ Удалить админа {target_id}?",
        reply_markup=keyboard
    )
'''


# ============================================================
# ЗАПУСК
# ============================================================
print("=" * 60)
print("Part B v2: Управление админами (исправлено)")
print("=" * 60)

# 1. Append функций в БД
db_path = BASE / "database" / "postgres_db.py"
backup(db_path)
content = db_path.read_text(encoding="utf-8")

if "async def is_admin" not in content:
    with open(db_path, "a", encoding="utf-8") as f:
        f.write(DB_APPEND)
    print("  ✅ database/postgres_db.py — добавлены функции админов")
else:
    print("  ℹ️  database/postgres_db.py — функции уже есть")

# 2. Fix is_paid
content = db_path.read_text(encoding="utf-8")
OLD_IS_PAID = '''async def is_paid(user_id: int) -> bool:
    if FREE_MODE:
        return True
'''
NEW_IS_PAID = '''async def is_paid(user_id: int) -> bool:
    if FREE_MODE:
        return True

    if await is_admin(user_id):
        return True
'''
if OLD_IS_PAID in content and "if await is_admin(user_id):\n        return True" not in content:
    content = content.replace(OLD_IS_PAID, NEW_IS_PAID, 1)
    db_path.write_text(content, encoding="utf-8")
    print("  ✅ is_paid — добавлена проверка админа")
else:
    print("  ℹ️  is_paid — уже есть или не найден")

# 3. Fix get_user_ai_limit
content = db_path.read_text(encoding="utf-8")
OLD = "    if user_id in ADMINS:\n        return -1"
NEW = "    if await is_admin(user_id):\n        return -1"
if OLD in content:
    content = content.replace(OLD, NEW)
    db_path.write_text(content, encoding="utf-8")
    print("  ✅ get_user_ai_limit — использует is_admin()")
else:
    print("  ℹ️  get_user_ai_limit — уже исправлен")

# 4. Append роутеров в admin_simple.py
admin_path = BASE / "handlers" / "admin_simple.py"
backup(admin_path)
content = admin_path.read_text(encoding="utf-8")

if "admin_manage_admins" not in content:
    with open(admin_path, "a", encoding="utf-8") as f:
        f.write(ADMIN_APPEND)
    print("  ✅ handlers/admin_simple.py — добавлены роутеры админов")
else:
    print("  ℹ️  handlers/admin_simple.py — роутеры уже есть")

# 5. Кнопка 👑 Админы
content = admin_path.read_text(encoding="utf-8")
if 'text="👑 Админы"' in content:
    print("  ℹ️  Кнопка 👑 Админы уже есть")
else:
    ANCHOR = '[InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu")],'
    if ANCHOR in content:
        content = content.replace(
            ANCHOR,
            '[InlineKeyboardButton(text="👑 Админы", callback_data="admin_manage_admins")],\n        ' + ANCHOR,
            1
        )
        admin_path.write_text(content, encoding="utf-8")
        print("  ✅ Кнопка 👑 Админы добавлена")
    else:
        ANCHOR2 = '[InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],'
        if ANCHOR2 in content:
            content = content.replace(
                ANCHOR2,
                '[InlineKeyboardButton(text="👑 Админы", callback_data="admin_manage_admins")],\n        ' + ANCHOR2,
                1
            )
            admin_path.write_text(content, encoding="utf-8")
            print("  ✅ Кнопка 👑 Админы добавлена (anchor 2)")
        else:
            print("  ⚠️  Добавь кнопку вручную:")
            print('     [InlineKeyboardButton(text="👑 Админы", callback_data="admin_manage_admins")],')

# 6. Патч handlers
print()
print("  Патчим handlers:")
HANDLERS_TO_PATCH = [
    "handlers/start.py",
    "handlers/ai_handler.py",
    "handlers/pdf_handler.py",
    "handlers/profile.py",
    "handlers/compatibility.py",
]

REPLACEMENTS = [
    ("if user_id in ADMINS:", "if await is_admin(user_id):"),
    ("if user_id not in ADMINS:", "if not await is_admin(user_id):"),
    ("if callback.from_user.id in ADMINS:", "if await is_admin(callback.from_user.id):"),
    ("if callback.from_user.id not in ADMINS:", "if not await is_admin(callback.from_user.id):"),
    ("if message.from_user.id in ADMINS:", "if await is_admin(message.from_user.id):"),
    ("if message.from_user.id not in ADMINS:", "if not await is_admin(message.from_user.id):"),
]

for rel in HANDLERS_TO_PATCH:
    fpath = BASE / rel
    if not fpath.exists():
        continue
    backup(fpath)
    content = fpath.read_text(encoding="utf-8")
    original = content

    if "from database.postgres_db import" in content:
        first_part = "\n".join(content.split("\n")[:40])
        if "is_admin" not in first_part:
            import_start = content.find("from database.postgres_db import")
            if import_start >= 0:
                after = content[import_start:import_start + 60]
                if "(" in after.split("\n")[0]:
                    end = content.find(")", import_start)
                    if end > 0:
                        before = content[:end].rstrip()
                        after_paren = content[end:]
                        if before.endswith(","):
                            new = before + "\n    is_admin,\n"
                        else:
                            new = before + ",\n    is_admin,\n"
                        content = new + after_paren
                else:
                    end = content.find("\n", import_start)
                    import_line = content[import_start:end]
                    if "is_admin" not in import_line:
                        new_line = import_line.rstrip() + ", is_admin"
                        content = content[:import_start] + new_line + content[end:]

    replace_count = 0
    for old, new in REPLACEMENTS:
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            replace_count += count

    if content != original:
        fpath.write_text(content, encoding="utf-8")
        print(f"    ✅ {rel}: {replace_count} замен")
    else:
        print(f"    ℹ️  {rel}: без изменений")

print()
print("=" * 60)
print("ГОТОВО!")
print("=" * 60)
print()
print("Дальше:")
print("  cd C:\\Users\\User\\Desktop\\AstroBot_clean")
print("  python webhook_bot.py")