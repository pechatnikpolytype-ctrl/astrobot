#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Часть D-2: Показ рекламы + настройка ссылок.
Запуск: python part_advertising_d2.py
"""

from pathlib import Path
import shutil

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")

if not BASE.exists():
    print(f"❌ Папка не найдена: {BASE}")
    exit(1)


def backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak_d2")
    if not bak.exists():
        shutil.copy2(path, bak)


# ============================================================
# 1. Обновляем admin_ads.py — добавляем функцию построения URL + обработку клика + режим ссылки
# ============================================================
ADMIN_ADS_ADDITIONS = r'''

# ============================================================
# ОБРАБОТКА КЛИКА ПО РЕКЛАМЕ
# ============================================================
@router.callback_query(F.data.startswith("ad_click_"))
async def ad_click(callback: CallbackQuery):
    """Клик по рекламе — считаем, показываем ссылку."""
    from database.postgres_db import get_ad, log_ad_action
    try:
        ad_id = int(callback.data.replace("ad_click_", ""))
    except ValueError:
        return

    ad = await get_ad(ad_id)
    if not ad:
        await callback.answer("Реклама не найдена", show_alert=True)
        return

    # Считаем клик
    try:
        await log_ad_action(ad_id, callback.from_user.id, "click")
    except Exception:
        pass

    # Показываем детальную карточку
    full_link = _build_ad_url(ad)
    text = (
        f"📢 РЕКЛАМА\n\n"
        f"{ad['text']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    buttons = []
    if full_link:
        buttons.append([InlineKeyboardButton(
            text="➡️ Открыть сайт", url=full_link
        )])
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад в меню", callback_data="main_menu"
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.answer(text, reply_markup=keyboard)
        except Exception:
            pass
    await callback.answer()


def _build_ad_url(ad: dict) -> str:
    """
    Строит URL с учётом режима:
    - 'direct' — как есть
    - 'utm' — авто UTM
    - None / 'none' — без ссылки
    """
    link = ad.get("link")
    if not link:
        return ""

    mode = ad.get("link_mode", "direct")

    if mode == "direct":
        return link
    elif mode == "utm":
        # Разделитель ? или &
        sep = "&" if "?" in link else "?"
        utm_source = ad.get("utm_source", "astro_bot")
        utm_medium = ad.get("utm_medium", "ad")
        utm_campaign = f"ad_{ad['id']}"
        return f"{link}{sep}utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}"

    return link


# ============================================================
# ВЫБОР РЕЖИМА ССЫЛКИ
# ============================================================
@router.callback_query(F.data.startswith("ads_edit_mode_"))
async def ads_edit_mode(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_edit_mode_", ""))
    ad = await get_ad(ad_id)
    if not ad:
        await callback.answer("Не найден", show_alert=True)
        return

    current_mode = ad.get("link_mode", "direct")
    text = (
        f"⚙️ РЕЖИМ ССЫЛКИ для блока #{ad_id}\n\n"
        f"Текущий: {current_mode}\n\n"
        f"• Прямая — админ вводит полный URL\n"
        f"• Авто UTM — бот добавит utm_source, utm_medium, utm_campaign\n"
        f"• Без ссылки — только текст"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'✅' if current_mode == 'direct' else '☐'} Прямая ссылка",
            callback_data=f"ads_set_mode_direct_{ad_id}"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if current_mode == 'utm' else '☐'} Авто UTM",
            callback_data=f"ads_set_mode_utm_{ad_id}"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if current_mode == 'none' else '☐'} Без ссылки",
            callback_data=f"ads_set_mode_none_{ad_id}"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"ads_view_{ad_id}")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("ads_set_mode_"))
async def ads_set_mode(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    # ads_set_mode_direct_5
    rest = callback.data.replace("ads_set_mode_", "")
    parts = rest.rsplit("_", 1)
    if len(parts) != 2:
        return
    mode, ad_id_str = parts
    if not ad_id_str.isdigit():
        return
    ad_id = int(ad_id_str)
    if mode not in ("direct", "utm", "none"):
        return

    # Обновляем в БД (нужно добавить поле link_mode)
    pool = await __import__("database.postgres_db", fromlist=["db"]).db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "ALTER TABLE ads ADD COLUMN IF NOT EXISTS link_mode TEXT DEFAULT 'direct'"
        )
        await conn.execute(
            "UPDATE ads SET link_mode = $1 WHERE id = $2",
            mode, ad_id
        )
    await callback.answer(f"✅ Режим: {mode}", show_alert=True)
    # Перерисовываем
    callback.data = f"ads_view_{ad_id}"
    await ads_view(callback)
'''

# Добавляем "link_mode" в таблицу ads (при init)
DB_MIGRATION = '''

# ============================================================
# MIGRATION: link_mode для ads
# ============================================================
async def migrate_ads_link_mode():
    """Добавляет поле link_mode в ads, если его нет."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "ALTER TABLE ads ADD COLUMN IF NOT EXISTS link_mode TEXT DEFAULT 'direct'"
            )
        except Exception as e:
            logger.warning(f"migrate_ads_link_mode: {e}")
'''


# --- Патчим database/postgres_db.py ---
db_path = BASE / "database" / "postgres_db.py"
backup(db_path)
content = db_path.read_text(encoding="utf-8")

if "migrate_ads_link_mode" not in content:
    with open(db_path, "a", encoding="utf-8") as f:
        f.write(DB_MIGRATION)
    print("  ✅ database/postgres_db.py — migrate_ads_link_mode")

# Вызов migrate в init_ads_tables
content = db_path.read_text(encoding="utf-8")
OLD_INIT = '''    logger.info("✅ Таблицы ads/ad_stats созданы/проверены")'''
NEW_INIT = '''    # Миграция: link_mode
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "ALTER TABLE ads ADD COLUMN IF NOT EXISTS link_mode TEXT DEFAULT 'direct'"
            )
    except Exception:
        pass
    logger.info("✅ Таблицы ads/ad_stats созданы/проверены")'''

if OLD_INIT in content and "link_mode TEXT DEFAULT 'direct'" not in content:
    content = content.replace(OLD_INIT, NEW_INIT, 1)
    db_path.write_text(content, encoding="utf-8")
    print("  ✅ init_ads_tables — добавлена миграция link_mode")


# --- Патчим handlers/admin_ads.py ---
ads_path = BASE / "handlers" / "admin_ads.py"
backup(ads_path)
content = ads_path.read_text(encoding="utf-8")

# Добавляем кнопку "Режим ссылки" в ads_view
OLD_VIEW = '''        [InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data=f"ads_edit_link_{ad_id}")],
        [InlineKeyboardButton(text="🔘 Кнопка", callback_data=f"ads_edit_button_{ad_id}")],'''

NEW_VIEW = '''        [InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data=f"ads_edit_link_{ad_id}")],
        [InlineKeyboardButton(text="⚙️ Режим ссылки", callback_data=f"ads_edit_mode_{ad_id}")],
        [InlineKeyboardButton(text="🔘 Кнопка", callback_data=f"ads_edit_button_{ad_id}")],'''

if OLD_VIEW in content:
    content = content.replace(OLD_VIEW, NEW_VIEW, 1)
    print("  ✅ handlers/admin_ads.py — кнопка «Режим ссылки»")

# Показываем mode в ads_view
OLD_TEXT = '''        f"🔗 Ссылка: {ad.get('link') or '(нет)'}\\n"
        f"🔘 Кнопка: {ad.get('button_text', 'Подробнее')}\\n\\n"'''

NEW_TEXT = '''        f"🔗 Ссылка: {ad.get('link') or '(нет)'}\\n"
        f"⚙️ Режим: {ad.get('link_mode', 'direct')}\\n"
        f"🔘 Кнопка: {ad.get('button_text', 'Подробнее')}\\n\\n"'''

if OLD_TEXT in content:
    content = content.replace(OLD_TEXT, NEW_TEXT, 1)
    print("  ✅ handlers/admin_ads.py — показывает режим")

# Добавляем обработчик клика в конец файла
with open(ads_path, "a", encoding="utf-8") as f:
    f.write(ADMIN_ADS_ADDITIONS)
print("  ✅ handlers/admin_ads.py — ad_click + ads_edit_mode + ads_set_mode")


# ============================================================
# 2. Патчим menu_commands.py — показ рекламы в меню
# ============================================================
menu_path = BASE / "handlers" / "menu_commands.py"
backup(menu_path)
content = menu_path.read_text(encoding="utf-8")

# Добавляем импорт
OLD_IMPORT = '''from database.postgres_db import (
    is_paid, is_admin, get_last_menus, set_last_menus,
)'''

NEW_IMPORT = '''from database.postgres_db import (
    is_paid, is_admin, get_last_menus, set_last_menus,
    get_ads_config, should_show_ad, pick_random_ad, log_ad_action,
)'''

if OLD_IMPORT in content:
    content = content.replace(OLD_IMPORT, NEW_IMPORT)
    print("  ✅ menu_commands.py — импорт рекламы")

# Показ рекламы в _show_main_menu
OLD_MENU = '''    # 3. Сохраняем ID обоих сообщений
    await set_last_menus(
        user_id, chat_id,
        fact_id=fact_msg.message_id,
        inline_id=inline_msg.message_id,
    )'''

NEW_MENU = '''    # 3. Сохраняем ID обоих сообщений
    await set_last_menus(
        user_id, chat_id,
        fact_id=fact_msg.message_id,
        inline_id=inline_msg.message_id,
    )

    # 4. Показ рекламы
    try:
        await _maybe_show_ad(message, user_id, chat_id)
    except Exception as e:
        logger.debug(f"Реклама: {e}")


async def _maybe_show_ad(message: Message, user_id: int, chat_id: int):
    """Показывает рекламу, если нужно."""
    # Проверка: показывать ли
    if not await should_show_ad(user_id):
        return

    # Выбор блока
    ad = await pick_random_ad()
    if not ad:
        return

    # Текст + кнопка
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\\n"
        "📢 РЕКЛАМА\\n\\n"
        f"{ad['text']}"
    )

    button_text = ad.get("button_text", "Подробнее")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🔥 {button_text}",
            callback_data=f"ad_click_{ad['id']}"
        )],
    ])

    try:
        ad_msg = await message.answer(text, reply_markup=keyboard)
        # Логируем показ
        await log_ad_action(ad["id"], user_id, "show")
    except Exception as e:
        logger.debug(f"Не отправили рекламу: {e}")'''

if OLD_MENU in content:
    content = content.replace(OLD_MENU, NEW_MENU, 1)
    print("  ✅ menu_commands.py — показ рекламы в меню")
else:
    print("  ⚠️  menu_commands.py — anchor не найден")

menu_path.write_text(content, encoding="utf-8")


print()
print("=" * 60)
print("ГОТОВО! Часть D-2")
print("=" * 60)
print()
print("Что работает:")
print("  • Реклама показывается в главном меню (отдельным сообщением)")
print("  • Клик по кнопке → показ ссылки с UTM")
print("  • Режим ссылки настраивается в админке:")
print("    - Прямая")
print("    - Авто UTM")
print("    - Без ссылки")
print()
print("Дальше:")
print("  cd C:\\Users\\User\\Desktop\\AstroBot_clean")
print("  python webhook_bot.py")
print()
print("Проверь:")
print("  1. /admin → 📢 Реклама → ⚙️ Настройки → включи")
print("  2. Добавь блок с ссылкой")
print("  3. В блоке — «⚙️ Режим ссылки» → выбери «Авто UTM»")
print("  4. Главное меню → должна появиться реклама")
print("  5. Нажми на кнопку → ссылка с UTM")