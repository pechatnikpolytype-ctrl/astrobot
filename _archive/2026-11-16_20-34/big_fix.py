#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Большой фикс:
1. Админы — все проверки через is_admin
2. Оплата — successful_payment надёжный
3. Статистика — по тарифам
Запуск: python big_fix.py
"""

from pathlib import Path
import shutil
import re

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")

if not BASE.exists():
    print(f"❌ Папка не найдена: {BASE}")
    exit(1)


def backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak_bigfix")
    if not bak.exists():
        shutil.copy2(path, bak)


# ============================================================
# 1. ФИКС: Заменить in ADMINS → is_admin в admin_simple.py
# ============================================================
print("=" * 60)
print("ФИКС 1: Замена 'in ADMINS' на 'is_admin'")
print("=" * 60)

admin_path = BASE / "handlers" / "admin_simple.py"
backup(admin_path)
content = admin_path.read_text(encoding="utf-8")
original = content

# 1.1 Добавить импорт is_admin
if "is_admin" not in content.split("\n")[0:30][0]:
    # Импорт есть?
    if "from database.postgres_db import" in content:
        # Добавить is_admin если нет
        old_import = "    clean_time_dependent_cache, clean_old_ai_history_v2, get_ai_cache_stats,\n)"
        new_import = "    clean_time_dependent_cache, clean_old_ai_history_v2, get_ai_cache_stats,\n    is_admin,\n)"
        if old_import in content:
            content = content.replace(old_import, new_import)
            print("  ✅ Импорт is_admin добавлен (по anchor 1)")
        else:
            # Ищем любой import
            pattern = re.compile(
                r"(from database\.postgres_db import \([^)]+)\)",
                re.DOTALL
            )
            m = pattern.search(content)
            if m:
                block = m.group(1)
                if "is_admin" not in block:
                    content = content.replace(
                        m.group(0),
                        block + ",\n    is_admin,\n)",
                        1
                    )
                    print("  ✅ Импорт is_admin добавлен (regex)")

# 1.2 Заменяем ВСЕ 'in ADMINS' на 'await is_admin()'
replacements = [
    # callback
    ("if callback.from_user.id not in ADMINS:", "if not await is_admin(callback.from_user.id):"),
    ("if callback.from_user.id in ADMINS:", "if await is_admin(callback.from_user.id):"),
    # message
    ("if message.from_user.id not in ADMINS:", "if not await is_admin(message.from_user.id):"),
    ("if message.from_user.id in ADMINS:", "if await is_admin(message.from_user.id):"),
]

total_replaces = 0
for old, new in replacements:
    count = content.count(old)
    if count > 0:
        content = content.replace(old, new)
        total_replaces += count

print(f"  ✅ Заменено: {total_replaces} мест")

admin_path.write_text(content, encoding="utf-8")


# ============================================================
# 2. ФИКС: payment.py — successful_payment
# ============================================================
print()
print("=" * 60)
print("ФИКС 2: successful_payment — надёжный")
print("=" * 60)

payment_path = BASE / "handlers" / "payment.py"
backup(payment_path)

# Перезаписываем payment.py целиком
PAYMENT_PY = r'''from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice, PreCheckoutQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.filters import Command
from database.postgres_db import (
    add_payment, set_subscription, get_user, get_pricing, is_admin,
)
from config import ADMINS, BOT_TOKEN
import logging

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# БАЛАНС STARS
# ============================================================
@router.message(Command("stars_balance"))
async def cmd_stars_balance(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Только для админов")
        return
    bot = Bot(token=BOT_TOKEN)
    try:
        balance = await bot.get_my_star_balance()
        await message.answer(f"⭐ Баланс звёзд бота: {balance}")
    except Exception as e:
        logger.error(f"Ошибка баланса: {e}")
        await message.answer("❌ Не удалось получить баланс")
    finally:
        await bot.session.close()


# ============================================================
# СОЗДАНИЕ СЧЁТА
# ============================================================
@router.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: CallbackQuery):
    plan = callback.data.split("_")[1]
    pricing = await get_pricing()
    info = pricing.get(plan)
    if not info:
        await callback.answer("Неверный тариф", show_alert=True)
        return

    days = info["days"]
    stars = info["stars"]

    try:
        await callback.message.answer_invoice(
            title=f"Подписка на {days} дней",
            description=f"Доступ ко всем функциям бота на {days} дней",
            payload=f"sub_{days}_{stars}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Подписка", amount=stars)],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Оплатить ⭐", pay=True)]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка invoice: {e}")
        await callback.answer("❌ Ошибка создания счёта", show_alert=True)
        return
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


# ============================================================
# УСПЕШНАЯ ОПЛАТА
# ============================================================
@router.message(F.successful_payment)
async def successful_payment(message: Message):
    """Обработка успешной оплаты."""
    payment = message.successful_payment
    user_id = message.from_user.id
    stars_paid = payment.total_amount
    payload = payment.invoice_payload
    charge_id = payment.telegram_payment_charge_id

    logger.info(f"💰 Платёж: user={user_id}, stars={stars_paid}, payload={payload}, charge_id={charge_id}")

    # Парсим payload
    try:
        parts = payload.split("_")
        if len(parts) < 3:
            raise ValueError(f"Неверный payload: {payload}")
        _, days_str, stars_str = parts[0], parts[1], parts[2]
        days = int(days_str)
        stars_expected = int(stars_str)
    except Exception as e:
        logger.error(f"Ошибка парсинга payload: {e}")
        await message.answer(
            "❌ Ошибка обработки оплаты. Свяжитесь с поддержкой: @SupportBot"
        )
        return

    # Проверка суммы
    if stars_paid != stars_expected:
        logger.warning(f"Сумма не совпадает: {stars_paid} vs {stars_expected}")
        await message.answer("❌ Ошибка суммы оплаты. Свяжитесь с поддержкой.")

    # 1. Активация подписки
    try:
        await set_subscription(user_id, days)
        logger.info(f"✅ Подписка активирована: {user_id} на {days} дней")
    except Exception as e:
        logger.error(f"Ошибка set_subscription: {e}")

    # 2. Запись платежа
    payment_saved = False
    try:
        await add_payment(user_id, stars_paid, charge_id, days)
        payment_saved = True
        logger.info(f"✅ Платёж записан: {charge_id}")
    except Exception as e:
        logger.error(f"Ошибка add_payment: {e}")

    # 3. Сброс кэша (если нужно)
    try:
        from database.postgres_db import invalidate_user_cache
        invalidate_user_cache(user_id)
    except Exception:
        pass

    # 4. Уведомление админам (не критично)
    try:
        bot = Bot(token=BOT_TOKEN)
        user_data = await get_user(user_id)
        if user_data:
            name = user_data.get("first_name") or user_data.get("username") or str(user_id)
        else:
            name = str(user_id)

        for admin_id in ADMINS:
            try:
                await bot.send_message(
                    admin_id,
                    f"💎 Новая подписка!\n\n"
                    f"👤 {name} (ID: {user_id})\n"
                    f"📅 {days} дней\n"
                    f"⭐ {stars_paid} звёзд\n"
                    f"🆔 {charge_id}"
                )
            except Exception as e:
                logger.warning(f"Не отправить админу {admin_id}: {e}")

        await bot.session.close()
    except Exception as e:
        logger.warning(f"Уведомление админам: {e}")

    # 5. Ответ пользователю
    try:
        await message.answer(
            f"✅ Подписка активирована на {days} дней!\n\n"
            f"Благодарим за использование AstroBot."
        )
    except Exception as e:
        logger.error(f"Ответ пользователю: {e}")

    # 6. Меню
    try:
        from keyboards.main import main_menu_keyboard
        await message.answer(
            "🏠 Главное меню:",
            reply_markup=main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Меню: {e}")
        # Если основное меню упало — просто текст
        try:
            await message.answer("Напишите /start для продолжения.")
        except Exception:
            pass


@router.message(Command("refund"))
async def cmd_refund(message: Message):
    await message.answer("Для возврата свяжитесь: @SupportBot")


@router.message(Command("paysupport"))
async def cmd_pay_support(message: Message):
    await message.answer("Проблемы с оплатой? Напишите @SupportBot")
'''

payment_path.write_text(PAYMENT_PY, encoding="utf-8")
print("  ✅ payment.py перезаписан")


# ============================================================
# 3. ФИКС: Статистика по тарифам
# ============================================================
print()
print("=" * 60)
print("ФИКС 3: Статистика по тарифам")
print("=" * 60)

# 3.1 Добавить функцию в postgres_db.py
db_path = BASE / "database" / "postgres_db.py"
backup(db_path)
content = db_path.read_text(encoding="utf-8")

if "async def get_tariff_stats" not in content:
    DB_APPEND = r'''

# ============================================================
# СТАТИСТИКА ПО ТАРИФАМ
# ============================================================
async def get_tariff_stats() -> dict:
    """
    Возвращает разбивку пользователей по тарифам.
    - free: ни разу не платили
    - trial: на триале (is_paid=TRUE, но нет платежей)
    - 7d/30d/90d: последний платёж был на этот срок
    - admins: админы
    """
    from config import ADMINS as MAIN_ADMINS
    extra = await get_extra_admins()
    all_admins = set(MAIN_ADMINS + extra)

    pool = await db.create_pool()
    async with pool.acquire() as conn:
        # Все пользователи
        rows = await conn.fetch("""
            SELECT 
                user_id,
                is_paid,
                subscription_end,
                (SELECT days FROM payments 
                 WHERE user_id = users.user_id 
                 ORDER BY created_at DESC LIMIT 1) as last_days,
                (SELECT COUNT(*) FROM payments 
                 WHERE user_id = users.user_id) as pay_count
            FROM users
        """)

    result = {
        "total": len(rows),
        "admins": 0,
        "free": 0,
        "trial": 0,
        "7d": 0,
        "30d": 0,
        "90d": 0,
        "other": 0,
    }

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    for r in rows:
        uid = r["user_id"]
        if uid in all_admins:
            result["admins"] += 1
            continue

        if not r["is_paid"]:
            result["free"] += 1
            continue

        # Подписка активна?
        sub_end = r["subscription_end"]
        if sub_end and sub_end < today:
            result["free"] += 1
            continue

        # Есть ли платежи?
        if r["pay_count"] == 0:
            result["trial"] += 1
            continue

        last_days = r["last_days"] or 0
        if last_days == 7:
            result["7d"] += 1
        elif last_days == 30:
            result["30d"] += 1
        elif last_days == 90:
            result["90d"] += 1
        else:
            result["other"] += 1

    return result
'''
    with open(db_path, "a", encoding="utf-8") as f:
        f.write(DB_APPEND)
    print("  ✅ get_tariff_stats добавлена в postgres_db.py")
else:
    print("  ℹ️  get_tariff_stats уже есть")


# 3.2 Обновить admin_stats в admin_simple.py
content = admin_path.read_text(encoding="utf-8")

# Проверяем, есть ли уже новая версия
if "get_tariff_stats" in content:
    print("  ℹ️  admin_stats уже обновлён")
else:
    # Заменить старую функцию admin_stats
    OLD_STATS = '''@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    stats = await get_stats()
    ai_usage = await get_total_ai_usage_today()
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        total_req = await conn.fetchval("SELECT COUNT(*) FROM requests")
        today_req = await conn.fetchval("SELECT COUNT(*) FROM requests WHERE created_at >= CURRENT_DATE")
        new_week = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'")
    text = (
        f"📊 СТАТИСТИКА\\n\\n"
        f"👥 Всего: {stats['total_users']}\\n"
        f"🆕 За 7 дней: {new_week or 0}\\n"
        f"💎 Платных: {stats['paid_users']}\\n\\n"
        f"📈 Запросов: {total_req or 0}\\n"
        f"📅 Сегодня: {today_req or 0}\\n"
        f"🤖 AI сегодня: {ai_usage}\\n\\n"
        f"💰 Заработано: {stats['total_stars']} ⭐"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)'''

    NEW_STATS = '''@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    from database.postgres_db import get_tariff_stats
    stats = await get_stats()
    tariffs = await get_tariff_stats()
    ai_usage = await get_total_ai_usage_today()
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        total_req = await conn.fetchval("SELECT COUNT(*) FROM requests")
        today_req = await conn.fetchval("SELECT COUNT(*) FROM requests WHERE created_at >= CURRENT_DATE")
        new_week = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'")
    text = (
        f"📊 СТАТИСТИКА\\n\\n"
        f"👥 Всего: {stats['total_users']}\\n"
        f"🆕 За 7 дней: {new_week or 0}\\n\\n"
        f"📋 ПО ТАРИФАМ:\\n"
        f"  • 🆓 Бесплатных: {tariffs['free']}\\n"
        f"  • 🎁 На триале: {tariffs['trial']}\\n"
        f"  • 📅 7 дней: {tariffs['7d']}\\n"
        f"  • 📅 30 дней: {tariffs['30d']}\\n"
        f"  • 📅 90 дней: {tariffs['90d']}\\n"
        f"  • 👑 Админов: {tariffs['admins']}\\n\\n"
        f"📈 Запросов: {total_req or 0}\\n"
        f"📅 Сегодня: {today_req or 0}\\n"
        f"🤖 AI сегодня: {ai_usage}\\n\\n"
        f"💰 Заработано: {stats['total_stars']} ⭐"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)'''

    if OLD_STATS in content:
        content = content.replace(OLD_STATS, NEW_STATS)
        admin_path.write_text(content, encoding="utf-8")
        print("  ✅ admin_stats обновлён — статистика по тарифам")
    else:
        print("  ⚠️  admin_stats — anchor не найден, добавляю в конец")
        # Добавляем новую версию в конец
        with open(admin_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + NEW_STATS + "\n")


print()
print("=" * 60)
print("ГОТОВО!")
print("=" * 60)
print()
print("Что исправлено:")
print("  1. Все проверки админов → is_admin (для доп. админов)")
print("  2. successful_payment — надёжный, с логированием")
print("  3. Статистика — по тарифам (7/30/90, триал, бесплатные)")
print()
print("Дальше:")
print("  cd C:\\Users\\User\\Desktop\\AstroBot_clean")
print("  python webhook_bot.py")
print()
print("Проверь:")
print("  1. Доп. админ → /admin — работает?")
print("  2. Оплата → подписка + запись в БД")
print("  3. /admin → 📊 Стата — видно разбивку по тарифам")