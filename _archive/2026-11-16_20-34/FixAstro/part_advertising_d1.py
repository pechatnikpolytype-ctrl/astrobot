#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Часть D-1: Реклама — БД + админка.
Запуск: python part_advertising_d1.py
"""

from pathlib import Path
import shutil

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")

if not BASE.exists():
    print(f"❌ Папка не найдена: {BASE}")
    exit(1)


def backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak_ads")
    if not bak.exists():
        shutil.copy2(path, bak)


# ============================================================
# 1. APPEND в database/postgres_db.py
# ============================================================
DB_APPEND = r'''

# ============================================================
# РЕКЛАМА
# ============================================================
async def init_ads_tables():
    """Создаёт таблицы ads и ad_stats."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                link TEXT,
                button_text TEXT DEFAULT 'Подробнее',
                utm_source TEXT DEFAULT 'astro_bot',
                utm_medium TEXT DEFAULT 'ad',
                enabled BOOLEAN DEFAULT TRUE,
                weight INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ad_stats (
                id SERIAL PRIMARY KEY,
                ad_id INTEGER REFERENCES ads(id) ON DELETE CASCADE,
                user_id BIGINT,
                action TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ad_stats_ad ON ad_stats(ad_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ad_stats_date ON ad_stats(created_at)
        """)
    logger.info("✅ Таблицы ads/ad_stats созданы/проверены")


async def get_ads_config() -> dict:
    default = {
        "enabled": False,
        "place": "menu",
        "frequency": "daily",
        "frequency_value": 1,
        "max_per_day": 3,
        "show_to_admins": False,
    }
    data = await get_setting("ads_config", default)
    if not isinstance(data, dict):
        return default
    for k, v in default.items():
        if k not in data:
            data[k] = v
    return data


async def set_ads_config(**kwargs):
    current = await get_ads_config()
    for k, v in kwargs.items():
        current[k] = v
    await set_setting("ads_config", current)


async def get_all_ads(only_enabled: bool = False) -> list:
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        if only_enabled:
            rows = await conn.fetch(
                "SELECT * FROM ads WHERE enabled = TRUE ORDER BY id"
            )
        else:
            rows = await conn.fetch("SELECT * FROM ads ORDER BY id")
        return [dict(r) for r in rows]


async def get_ad(ad_id: int):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM ads WHERE id = $1", ad_id)
        return dict(row) if row else None


async def add_ad(text: str, link: str = None, button_text: str = "Подробнее",
                  utm_source: str = "astro_bot", utm_medium: str = "ad") -> int:
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO ads (text, link, button_text, utm_source, utm_medium)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, text, link, button_text, utm_source, utm_medium)
        return row["id"]


async def update_ad(ad_id: int, **kwargs) -> bool:
    allowed = {"text", "link", "button_text", "enabled", "weight",
               "utm_source", "utm_medium"}
    fields = []
    values = []
    for i, (k, v) in enumerate(kwargs.items(), 1):
        if k not in allowed:
            continue
        fields.append(f"{k} = ${i}")
        values.append(v)
    if not fields:
        return False
    values.append(ad_id)
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE ads SET {', '.join(fields)} WHERE id = ${len(values)}",
            *values
        )
    return True


async def delete_ad(ad_id: int) -> bool:
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM ads WHERE id = $1", ad_id)
    return result.endswith("1")


async def toggle_ad(ad_id: int) -> bool:
    """Переключает enabled. Возвращает новое состояние."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE ads SET enabled = NOT enabled WHERE id = $1 RETURNING enabled",
            ad_id
        )
        return row["enabled"] if row else False


async def log_ad_action(ad_id: int, user_id: int, action: str):
    """Логирует показ или клик."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO ad_stats (ad_id, user_id, action)
            VALUES ($1, $2, $3)
        """, ad_id, user_id, action)


async def get_ad_stats(ad_id: int, days: int = 7) -> dict:
    """Статистика одного блока за N дней."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        shows = await conn.fetchval(f"""
            SELECT COUNT(*) FROM ad_stats
            WHERE ad_id = $1 AND action = 'show'
            AND created_at >= NOW() - INTERVAL '{days} days'
        """, ad_id) or 0
        clicks = await conn.fetchval(f"""
            SELECT COUNT(*) FROM ad_stats
            WHERE ad_id = $1 AND action = 'click'
            AND created_at >= NOW() - INTERVAL '{days} days'
        """, ad_id) or 0
    ctr = (clicks / shows * 100) if shows > 0 else 0
    return {"shows": shows, "clicks": clicks, "ctr": round(ctr, 1)}


async def get_all_ad_stats(days: int = 7) -> dict:
    """Общая статистика за N дней."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        shows = await conn.fetchval(f"""
            SELECT COUNT(*) FROM ad_stats
            WHERE action = 'show'
            AND created_at >= NOW() - INTERVAL '{days} days'
        """) or 0
        clicks = await conn.fetchval(f"""
            SELECT COUNT(*) FROM ad_stats
            WHERE action = 'click'
            AND created_at >= NOW() - INTERVAL '{days} days'
        """) or 0
    ctr = (clicks / shows * 100) if shows > 0 else 0
    return {"shows": shows, "clicks": clicks, "ctr": round(ctr, 1)}


async def should_show_ad(user_id: int) -> bool:
    """Проверяет, показывать ли рекламу пользователю сейчас."""
    config = await get_ads_config()
    if not config.get("enabled"):
        return False

    # Админам?
    if not config.get("show_to_admins", False):
        if await is_admin(user_id):
            return False

    # Лимит в день
    from datetime import date
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        today_count = await conn.fetchval("""
            SELECT COUNT(*) FROM ad_stats
            WHERE user_id = $1
            AND action = 'show'
            AND created_at::date = CURRENT_DATE
        """, user_id) or 0

    max_per_day = config.get("max_per_day", 3)
    if max_per_day > 0 and today_count >= max_per_day:
        return False

    # Частота
    freq = config.get("frequency", "daily")
    if freq == "always":
        return True
    elif freq == "daily":
        # Уже показывали сегодня?
        pool = await db.create_pool()
        async with pool.acquire() as conn:
            shown_today = await conn.fetchval("""
                SELECT COUNT(*) FROM ad_stats
                WHERE user_id = $1
                AND action = 'show'
                AND created_at::date = CURRENT_DATE
            """, user_id) or 0
        return shown_today == 0
    elif freq == "every_n":
        n = config.get("frequency_value", 5)
        if n <= 0:
            return True
        # Считаем все действия пользователя (можно заменить на счётчик меню)
        pool = await db.create_pool()
        async with pool.acquire() as conn:
            total = await conn.fetchval("""
                SELECT COUNT(*) FROM requests WHERE user_id = $1
            """, user_id) or 0
        return (total % n) == 0
    return True


async def pick_random_ad() -> dict:
    """Случайный активный рекламный блок."""
    ads = await get_all_ads(only_enabled=True)
    if not ads:
        return {}
    import random
    # Взвешенный выбор
    weights = [max(1, a.get("weight", 1)) for a in ads]
    return random.choices(ads, weights=weights, k=1)[0]
'''


db_path = BASE / "database" / "postgres_db.py"
backup(db_path)
content = db_path.read_text(encoding="utf-8")

if "async def init_ads_tables" not in content:
    with open(db_path, "a", encoding="utf-8") as f:
        f.write(DB_APPEND)
    print("  ✅ database/postgres_db.py — функции рекламы")

# Добавляем вызов init_ads_tables в init_postgres_db
content = db_path.read_text(encoding="utf-8")
ANCHOR = '    # --- Инициализация дневника настроения ---'
if "await init_ads_tables()" not in content and ANCHOR in content:
    content = content.replace(
        ANCHOR,
        "    # --- Инициализация рекламы ---\n    await init_ads_tables()\n\n" + ANCHOR,
        1
    )
    db_path.write_text(content, encoding="utf-8")
    print("  ✅ init_ads_tables вызывается в init_postgres_db")


# ============================================================
# 2. handlers/admin_ads.py — НОВЫЙ
# ============================================================
ADMIN_ADS_PY = r'''import logging
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import ADMINS
from database.postgres_db import (
    get_ads_config, set_ads_config,
    get_all_ads, get_ad, add_ad, update_ad, delete_ad, toggle_ad,
    get_ad_stats, get_all_ad_stats,
)

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# FSM
# ============================================================
class AdStates(StatesGroup):
    waiting_text = State()
    waiting_link = State()
    waiting_button_text = State()
    waiting_edit_text = State()
    waiting_edit_link = State()
    waiting_edit_button = State()
    waiting_freq_value = State()
    waiting_max_per_day = State()


# ============================================================
# МЕНЮ РЕКЛАМЫ
# ============================================================
@router.callback_query(F.data == "admin_ads")
async def admin_ads_menu(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    config = await get_ads_config()
    ads = await get_all_ads()
    stats = await get_all_ad_stats(days=7)

    status = "✅ ВКЛ" if config.get("enabled") else "❌ ВЫКЛ"
    freq_map = {
        "always": "Всегда",
        "daily": "1 раз в день",
        "every_n": f"Каждый {config.get('frequency_value', 5)}-й раз",
    }
    freq_text = freq_map.get(config.get("frequency", "daily"), "?")

    text = (
        f"📢 УПРАВЛЕНИЕ РЕКЛАМОЙ\n\n"
        f"Статус: {status}\n"
        f"Место: 🏠 Меню\n"
        f"Частота: {freq_text}\n"
        f"Лимит: {config.get('max_per_day', 3)} показов/день\n"
        f"Админам: {'показывать' if config.get('show_to_admins') else 'не показывать'}\n\n"
        f"📊 За 7 дней:\n"
        f"  • Показов: {stats['shows']}\n"
        f"  • Кликов: {stats['clicks']}\n"
        f"  • CTR: {stats['ctr']}%\n\n"
        f"Активных блоков: {len([a for a in ads if a['enabled']])} / {len(ads)}"
    )

    toggle_text = "❌ Выключить рекламу" if config.get("enabled") else "✅ Включить рекламу"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data="ads_toggle_all")],
        [InlineKeyboardButton(text="➕ Добавить блок", callback_data="ads_add")],
        [InlineKeyboardButton(text="📋 Список блоков", callback_data="ads_list")],
        [InlineKeyboardButton(text="⚙️ Настройки показа", callback_data="ads_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="ads_stats")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="ads_help")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ВКЛ/ВЫКЛ
# ============================================================
@router.callback_query(F.data == "ads_toggle_all")
async def ads_toggle_all(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    config = await get_ads_config()
    new_state = not config.get("enabled", False)
    await set_ads_config(enabled=new_state)
    await callback.answer(
        "✅ Реклама включена" if new_state else "❌ Реклама выключена",
        show_alert=True,
    )
    await admin_ads_menu(callback)


# ============================================================
# СПИСОК БЛОКОВ
# ============================================================
@router.callback_query(F.data == "ads_list")
async def ads_list(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ads = await get_all_ads()

    if not ads:
        text = "📋 СПИСОК БЛОКОВ\n\nПока пусто. Добавь первый блок!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить", callback_data="ads_add")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")],
        ])
    else:
        text = "📋 СПИСОК БЛОКОВ\n\n"
        buttons = []
        for a in ads:
            status = "✅" if a["enabled"] else "❌"
            short = a["text"][:30] + "..." if len(a["text"]) > 30 else a["text"]
            buttons.append([InlineKeyboardButton(
                text=f"{status} #{a['id']} {short}",
                callback_data=f"ads_view_{a['id']}"
            )])
        buttons.append([InlineKeyboardButton(text="➕ Добавить", callback_data="ads_add")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("ads_view_"))
async def ads_view(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_view_", ""))
    ad = await get_ad(ad_id)
    if not ad:
        await callback.answer("Не найден", show_alert=True)
        return

    stats = await get_ad_stats(ad_id, days=7)
    status = "✅ ВКЛ" if ad["enabled"] else "❌ ВЫКЛ"

    text = (
        f"📢 БЛОК #{ad['id']}\n\n"
        f"Статус: {status}\n"
        f"Вес: {ad.get('weight', 1)}\n\n"
        f"📝 Текст:\n{ad['text']}\n\n"
        f"🔗 Ссылка: {ad.get('link') or '(нет)'}\n"
        f"🔘 Кнопка: {ad.get('button_text', 'Подробнее')}\n\n"
        f"📊 За 7 дней:\n"
        f"  • Показов: {stats['shows']}\n"
        f"  • Кликов: {stats['clicks']}\n"
        f"  • CTR: {stats['ctr']}%"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="❌ Выключить" if ad["enabled"] else "✅ Включить",
            callback_data=f"ads_toggle_{ad_id}"
        )],
        [InlineKeyboardButton(text="✏️ Изменить текст", callback_data=f"ads_edit_text_{ad_id}")],
        [InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data=f"ads_edit_link_{ad_id}")],
        [InlineKeyboardButton(text="🔘 Кнопка", callback_data=f"ads_edit_button_{ad_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"ads_delete_{ad_id}")],
        [InlineKeyboardButton(text="🔙 Список", callback_data="ads_list")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ДОБАВИТЬ БЛОК
# ============================================================
@router.callback_query(F.data == "ads_add")
async def ads_add_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    await state.set_state(AdStates.waiting_text)
    await callback.message.edit_text(
        "➕ ДОБАВИТЬ БЛОК\n\nШаг 1/3\n\n"
        "Введите ТЕКСТ рекламы:\n\n"
        "/cancel — отмена"
    )


@router.message(AdStates.waiting_text)
async def ads_add_text(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    text = message.text.strip()
    if len(text) < 5:
        await message.answer("Слишком короткий текст (мин. 5 символов).")
        return
    await state.update_data(ad_text=text)
    await state.set_state(AdStates.waiting_link)
    await message.answer(
        "Шаг 2/3\n\n"
        "Введите ССЫЛКУ (URL) или /skip, если без ссылки:\n\n"
        "Пример: https://partner.com/promo"
    )


@router.message(AdStates.waiting_link)
async def ads_add_link(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    link = message.text.strip()
    if link == "/skip":
        link = None
    elif not (link.startswith("http://") or link.startswith("https://")):
        await message.answer("❌ Ссылка должна начинаться с http:// или https://")
        return
    await state.update_data(ad_link=link)
    await state.set_state(AdStates.waiting_button_text)
    await message.answer(
        "Шаг 3/3\n\n"
        "Введите текст кнопки (по умолчанию «Подробнее»):"
    )


@router.message(AdStates.waiting_button_text)
async def ads_add_button(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    btn_text = message.text.strip() or "Подробнее"
    data = await state.get_data()
    await state.clear()

    ad_id = await add_ad(
        text=data["ad_text"],
        link=data.get("ad_link"),
        button_text=btn_text,
    )
    await message.answer(f"✅ Блок #{ad_id} добавлен!")
    # Отправляем в меню
    from aiogram.types import CallbackQuery as FakeCallback
    # Просто вызываем меню админа через message
    await show_ads_after_action(message)


async def show_ads_after_action(target):
    """Показ меню рекламы после действия."""
    config = await get_ads_config()
    ads = await get_all_ads()
    stats = await get_all_ad_stats(days=7)

    status = "✅ ВКЛ" if config.get("enabled") else "❌ ВЫКЛ"
    freq_map = {
        "always": "Всегда",
        "daily": "1 раз в день",
        "every_n": f"Каждый {config.get('frequency_value', 5)}-й раз",
    }
    freq_text = freq_map.get(config.get("frequency", "daily"), "?")

    text = (
        f"📢 УПРАВЛЕНИЕ РЕКЛАМОЙ\n\n"
        f"Статус: {status}\n"
        f"Место: 🏠 Меню\n"
        f"Частота: {freq_text}\n"
        f"Лимит: {config.get('max_per_day', 3)} показов/день\n\n"
        f"📊 За 7 дней: показов {stats['shows']}, кликов {stats['clicks']}"
    )

    toggle_text = "❌ Выключить" if config.get("enabled") else "✅ Включить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data="ads_toggle_all")],
        [InlineKeyboardButton(text="➕ Добавить блок", callback_data="ads_add")],
        [InlineKeyboardButton(text="📋 Список блоков", callback_data="ads_list")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="ads_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="ads_stats")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="ads_help")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])

    if hasattr(target, "answer"):
        await target.answer(text, reply_markup=keyboard)


# ============================================================
# РЕДАКТИРОВАНИЕ
# ============================================================
@router.callback_query(F.data.startswith("ads_edit_text_"))
async def ads_edit_text_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_edit_text_", ""))
    await state.update_data(ad_id=ad_id)
    await state.set_state(AdStates.waiting_edit_text)
    await callback.message.edit_text(
        f"✏️ Новый ТЕКСТ для блока #{ad_id}:\n\n/cancel — отмена"
    )


@router.message(AdStates.waiting_edit_text)
async def ads_edit_text_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    data = await state.get_data()
    ad_id = data.get("ad_id")
    await update_ad(ad_id, text=message.text.strip())
    await state.clear()
    await message.answer(f"✅ Текст блока #{ad_id} обновлён")


@router.callback_query(F.data.startswith("ads_edit_link_"))
async def ads_edit_link_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_edit_link_", ""))
    await state.update_data(ad_id=ad_id)
    await state.set_state(AdStates.waiting_edit_link)
    await callback.message.edit_text(
        f"🔗 Новая ССЫЛКА для блока #{ad_id}:\n\n/skip — без ссылки\n/cancel — отмена"
    )


@router.message(AdStates.waiting_edit_link)
async def ads_edit_link_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    link = message.text.strip()
    if link == "/skip":
        link = None
    elif link and not (link.startswith("http://") or link.startswith("https://")):
        await message.answer("❌ Ссылка должна начинаться с http:// или https://")
        return
    data = await state.get_data()
    ad_id = data.get("ad_id")
    await update_ad(ad_id, link=link)
    await state.clear()
    await message.answer(f"✅ Ссылка блока #{ad_id} обновлена")


@router.callback_query(F.data.startswith("ads_edit_button_"))
async def ads_edit_button_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_edit_button_", ""))
    await state.update_data(ad_id=ad_id)
    await state.set_state(AdStates.waiting_edit_button)
    await callback.message.edit_text(
        f"🔘 Новый текст КНОПКИ для блока #{ad_id}:\n\n/cancel — отмена"
    )


@router.message(AdStates.waiting_edit_button)
async def ads_edit_button_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    data = await state.get_data()
    ad_id = data.get("ad_id")
    await update_ad(ad_id, button_text=message.text.strip() or "Подробнее")
    await state.clear()
    await message.answer(f"✅ Кнопка блока #{ad_id} обновлена")


# ============================================================
# УДАЛЕНИЕ / ВКЛ-ВЫКЛ
# ============================================================
@router.callback_query(F.data.startswith("ads_delete_"))
async def ads_delete(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_delete_", ""))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"ads_delete_do_{ad_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"ads_view_{ad_id}")],
    ])
    await callback.message.edit_text(
        f"⚠️ Удалить блок #{ad_id}?", reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("ads_delete_do_"))
async def ads_delete_do(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_delete_do_", ""))
    ok = await delete_ad(ad_id)
    await callback.answer("✅ Удалено" if ok else "❌ Не найден", show_alert=True)
    await ads_list(callback)


@router.callback_query(F.data.startswith("ads_toggle_"))
async def ads_toggle(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_toggle_", ""))
    new_state = await toggle_ad(ad_id)
    await callback.answer(
        "✅ Включен" if new_state else "❌ Выключен",
        show_alert=True,
    )
    # Обновляем страницу
    callback.data = f"ads_view_{ad_id}"
    await ads_view(callback)


# ============================================================
# НАСТРОЙКИ
# ============================================================
@router.callback_query(F.data == "ads_settings")
async def ads_settings(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    config = await get_ads_config()
    freq = config.get("frequency", "daily")

    text = (
        "⚙️ НАСТРОЙКИ ПОКАЗА\n\n"
        f"Частота: {freq}\n"
        f"Значение: {config.get('frequency_value', 5)}\n"
        f"Лимит в день: {config.get('max_per_day', 3)}\n"
        f"Показывать админам: {'Да' if config.get('show_to_admins') else 'Нет'}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Частота", callback_data="ads_set_freq")],
        [InlineKeyboardButton(text="🔢 Лимит в день", callback_data="ads_set_max")],
        [InlineKeyboardButton(
            text=f"👑 Админам: {'Да' if config.get('show_to_admins') else 'Нет'}",
            callback_data="ads_toggle_admins"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "ads_set_freq")
async def ads_set_freq(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    config = await get_ads_config()
    freq = config.get("frequency", "daily")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'✅' if freq == 'always' else '☐'} Всегда",
            callback_data="ads_freq_always"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if freq == 'daily' else '☐'} 1 раз в день",
            callback_data="ads_freq_daily"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if freq == 'every_n' else '☐'} Каждый N-й раз",
            callback_data="ads_freq_every_n"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="ads_settings")],
    ])
    await callback.message.edit_text(
        "📅 ЧАСТОТА ПОКАЗА\n\nКак часто показывать рекламу?",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("ads_freq_"))
async def ads_freq_set(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    freq = callback.data.replace("ads_freq_", "")
    if freq == "every_n":
        await state.set_state(AdStates.waiting_freq_value)
        await callback.message.edit_text(
            "🔢 Введите число N (каждый N-й раз):\n\n/cancel — отмена"
        )
        return
    await set_ads_config(frequency=freq)
    await callback.answer(f"✅ {freq}", show_alert=True)
    await ads_settings(callback)


@router.message(AdStates.waiting_freq_value)
async def ads_freq_value_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    try:
        n = int(message.text.strip())
        if n < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число ≥ 1")
        return
    await set_ads_config(frequency="every_n", frequency_value=n)
    await state.clear()
    await message.answer(f"✅ Каждый {n}-й раз")


@router.callback_query(F.data == "ads_set_max")
async def ads_set_max(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    await state.set_state(AdStates.waiting_max_per_day)
    await callback.message.edit_text(
        "🔢 Сколько показов в день максимум?\n\nВведите число (0 = без лимита):\n\n/cancel — отмена"
    )


@router.message(AdStates.waiting_max_per_day)
async def ads_max_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    try:
        n = int(message.text.strip())
        if n < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число ≥ 0")
        return
    await set_ads_config(max_per_day=n)
    await state.clear()
    await message.answer(f"✅ Лимит: {n} показов/день")


@router.callback_query(F.data == "ads_toggle_admins")
async def ads_toggle_admins(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    config = await get_ads_config()
    await set_ads_config(show_to_admins=not config.get("show_to_admins", False))
    await callback.answer("✅ Изменено", show_alert=True)
    await ads_settings(callback)


# ============================================================
# СТАТИСТИКА
# ============================================================
@router.callback_query(F.data == "ads_stats")
async def ads_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ads = await get_all_ads()

    text = "📊 СТАТИСТИКА РЕКЛАМЫ (7 дней)\n\n"
    for a in ads:
        st = await get_ad_stats(a["id"], days=7)
        short = a["text"][:40] + "..." if len(a["text"]) > 40 else a["text"]
        status = "✅" if a["enabled"] else "❌"
        text += f"{status} #{a['id']} {short}\n"
        text += f"   Показов: {st['shows']}, Кликов: {st['clicks']}, CTR: {st['ctr']}%\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="ads_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ИНСТРУКЦИЯ
# ============================================================
@router.callback_query(F.data == "ads_help")
async def ads_help(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    text = (
        "📖 ИНСТРУКЦИЯ ПО РЕКЛАМЕ\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 ЧТО ЭТО\n"
        "Реклама показывается пользователям в главном меню. "
        "Вы можете размещать партнёрские ссылки, промокоды, "
        "анонсы и получать доход.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "➕ КАК ДОБАВИТЬ БЛОК\n"
        "1. Нажмите «➕ Добавить блок»\n"
        "2. Введите текст рекламы\n"
        "3. Введите ссылку (https://...)\n"
        "4. Введите текст кнопки (по умолчанию «Подробнее»)\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚙️ НАСТРОЙКИ\n"
        "• Вкл/выкл — общий переключатель\n"
        "• Частота — как часто показывать\n"
        "  - Всегда — при каждом заходе\n"
        "  - 1 раз в день — не спамит\n"
        "  - Каждый N-й раз — промежуточный вариант\n"
        "• Лимит в день — максимум показов\n"
        "• Админам — показывать ли вам\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 СТАТИСТИКА\n"
        "Бот считает:\n"
        "• Показы — сколько раз видели\n"
        "• Клики — сколько нажали\n"
        "• CTR — процент кликов от показов\n\n"
        "Хороший CTR: 5-20%\n"
        "Отличный: >20%\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔗 ГДЕ БРАТЬ РЕКЛАМУ\n"
        "• Admitad — admitad.com\n"
        "• Ozon — партнёрка Ozon\n"
        "• Яндекс.Маркет — партнёрка\n"
        "• КупиКупон — купоны и скидки\n"
        "• Прямые партнёры (астро-сервисы, эзотерика)\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 СОВЕТЫ\n"
        "• Делайте короткий текст (1-2 строки)\n"
        "• Используйте эмодзи в начале\n"
        "• UTM-метки добавляются автоматически\n"
        "• Меняйте блоки раз в 1-2 недели\n"
        "• Не ставьте >3 показов в день\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ ПРАВИЛА\n"
        "• Запрещено: наркотики, оружие, взрослый контент\n"
        "• Запрещено: крипто-скам, финансовые пирамиды\n"
        "• Осторожно: букмекеры (могут забанить бота)\n"
        "• Telegram разрешает рекламу с пометкой #реклама\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🆘 ПОЛЕЗНЫЕ ССЫЛКИ\n"
        "• Документация Telegram: core.telegram.org\n"
        "• Admitad: admitad.com\n"
        "• Партнёрка Ozon: ozon.ru/partners\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)
'''


admin_ads_path = BASE / "handlers" / "admin_ads.py"
admin_ads_path.write_text(ADMIN_ADS_PY, encoding="utf-8")
print("  ✅ handlers/admin_ads.py — создан")


# ============================================================
# 3. Кнопка 📢 Реклама в admin_simple.py
# ============================================================
admin_path = BASE / "handlers" / "admin_simple.py"
backup(admin_path)
content = admin_path.read_text(encoding="utf-8")

if 'text="📢 Реклама"' in content:
    print("  ℹ️  Кнопка 📢 Реклама уже есть")
else:
    ANCHOR = '[InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu")],'
    if ANCHOR not in content:
        ANCHOR = '[InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],'
    if ANCHOR in content:
        content = content.replace(
            ANCHOR,
            '[InlineKeyboardButton(text="📢 Реклама", callback_data="admin_ads")],\n        ' + ANCHOR,
            1
        )
        admin_path.write_text(content, encoding="utf-8")
        print("  ✅ Кнопка 📢 Реклама добавлена")
    else:
        print("  ⚠️  Anchor не найден — добавь кнопку вручную")
        print('     [InlineKeyboardButton(text="📢 Реклама", callback_data="admin_ads")],')


# ============================================================
# 4. Подключить роутер в handlers/__init__.py
# ============================================================
init_path = BASE / "handlers" / "__init__.py"
backup(init_path)
content = init_path.read_text(encoding="utf-8")

if "admin_ads" not in content:
    lines = content.rstrip().split("\n")
    for i, line in enumerate(lines):
        if line.startswith("__all__"):
            lines.insert(i, "from .admin_ads import router as ads_router")
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "]":
                    lines.insert(j, "    'ads_router',")
                    break
            break
    content = "\n".join(lines) + "\n"
    init_path.write_text(content, encoding="utf-8")
    print("  ✅ handlers/__init__.py — ads_router подключён")
else:
    print("  ℹ️  handlers/__init__.py — ads_router уже есть")


# ============================================================
# 5. Патч webhook_bot.py и bot_prod.py
# ============================================================
for fname in ["webhook_bot.py", "bot_prod.py"]:
    fpath = BASE / fname
    if not fpath.exists():
        continue
    backup(fpath)
    content = fpath.read_text(encoding="utf-8")

    if "ads_router" in content:
        print(f"  ℹ️  {fname} — ads_router уже есть")
        continue

    # Импорт
    if "from handlers.mood_diary import router as mood_router" in content:
        content = content.replace(
            "from handlers.mood_diary import router as mood_router",
            "from handlers.mood_diary import router as mood_router\nfrom handlers.admin_ads import router as ads_router"
        )
    elif "from handlers.start import router as start_router" in content:
        content = content.replace(
            "from handlers.start import router as start_router",
            "from handlers.start import router as start_router\nfrom handlers.admin_ads import router as ads_router"
        )

    # Подключение
    if "dp.include_router(start_router)" in content:
        content = content.replace(
            "dp.include_router(start_router)",
            "dp.include_router(start_router)\ndp.include_router(ads_router)"
        )

    fpath.write_text(content, encoding="utf-8")
    print(f"  ✅ {fname} — ads_router подключён")


print()
print("=" * 60)
print("ГОТОВО! Часть D-1")
print("=" * 60)
print()
print("Что работает:")
print("  • Таблицы ads, ad_stats")
print("  • Кнопка 📢 Реклама в админке")
print("  • Добавление/редактирование/удаление блоков")
print("  • Настройки показа (частота, лимит, админы)")
print("  • Статистика (показы, клики, CTR)")
print("  • 📖 Инструкция с советами и ссылками")
print()
print("Дальше:")
print("  cd C:\\Users\\User\\Desktop\\AstroBot_clean")
print("  python webhook_bot.py")
print()
print("Проверь:")
print("  1. /admin → 📢 Реклама")
print("  2. Настройки → включи рекламу")
print("  3. Добавь блок")
print("  4. 📖 Инструкция — прочитай")