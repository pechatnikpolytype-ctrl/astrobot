from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import ADMINS, BOT_TOKEN
from database.postgres_db import (
    get_user, get_stats, set_subscription, is_paid, db,
    get_pricing, set_pricing,
    get_trial, set_trial,
    reset_all_trials, count_trial_used,
)
from datetime import datetime, timedelta
import logging
import asyncio
import os

logger = logging.getLogger(__name__)
router = Router()


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_user_id = State()
    waiting_subscription_days = State()
    waiting_search = State()
    waiting_price_days = State()
    waiting_price_stars = State()
    waiting_trial_days = State()


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================
async def show_admin_panel(target, edit: bool = True):
    stats = await get_stats()
    pricing = await get_pricing()
    trial = await get_trial()

    trial_status = f"✅ ВКЛ ({trial['days']} дн.)" if trial.get("enabled") else "❌ ВЫКЛ"

    text = (
        "👑 АДМИН-ПАНЕЛЬ\n\n"
        f"📊 Статистика:\n"
        f"  • Всего: {stats['total_users']}\n"
        f"  • Платных: {stats['paid_users']}\n"
        f"  • Бесплатных: {stats['free_users']}\n\n"
        f"⭐ Баланс: {stats['total_stars']} звёзд\n"
        f"💳 Платежей: {stats['total_payments']}\n\n"
        f"🎁 Пробный период: {trial_status}\n\n"
        f"💰 Текущие тарифы:\n"
    )
    for plan, info in pricing.items():
        text += f"  • {info['days']} дней — {info['stars']} ⭐\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Цены и тарифы", callback_data="admin_pricing"),
         InlineKeyboardButton(text="⭐ Баланс", callback_data="admin_balance")],
        [InlineKeyboardButton(text="🎁 Пробный период", callback_data="admin_trial"),
         InlineKeyboardButton(text="💸 Вывод средств", callback_data="admin_withdraw")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="💎 Подписки", callback_data="admin_subs"),
         InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])

    if isinstance(target, Message):
        await target.answer(text, reply_markup=keyboard)
    else:
        if edit:
            try:
                await target.message.edit_text(text, reply_markup=keyboard)
            except Exception:
                await target.message.answer(text, reply_markup=keyboard)
        else:
            await target.message.answer(text, reply_markup=keyboard)


@router.message(Command("admin"))
async def admin_command(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Нет доступа")
        return
    await show_admin_panel(message)


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        await callback.answer("Нет доступа")
        return
    await show_admin_panel(callback)


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await show_admin_panel(callback)


# ============================================================
# 🎁 ПРОБНЫЙ ПЕРИОД
# ============================================================
@router.callback_query(F.data == "admin_trial")
async def admin_trial(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    trial = await get_trial()
    used_count = await count_trial_used()

    status = "✅ ВКЛЮЧЁН" if trial.get("enabled") else "❌ ВЫКЛЮЧЕН"

    text = (
        f"🎁 ПРОБНЫЙ ПЕРИОД\n\n"
        f"Текущий статус: {status}\n"
        f"Срок: {trial.get('days', 1)} дн.\n\n"
        f"👥 Уже использовали: {used_count} чел.\n\n"
        f"Что это:\n"
        f"• Новые пользователи получают бесплатный доступ на N дней\n"
        f"• После окончания — просят оплатить подписку\n"
        f"• Флаг 'использован' ставится один раз на пользователя\n\n"
        f"Если триал выключен — сразу просим оплатить."
    )

    toggle_text = "❌ Выключить" if trial.get("enabled") else "✅ Включить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data="trial_toggle")],
        [InlineKeyboardButton(text="✏️ Изменить срок", callback_data="trial_change_days")],
        [InlineKeyboardButton(text="🔄 Сбросить флаг у всех", callback_data="trial_reset")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "trial_toggle")
async def trial_toggle(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    trial = await get_trial()
    new_enabled = not trial.get("enabled", True)
    await set_trial(new_enabled, trial.get("days", 1))

    status = "✅ ВКЛЮЧЁН" if new_enabled else "❌ ВЫКЛЮЧЕН"
    await callback.answer(f"Триал {status}", show_alert=True)

    # Обновляем страницу
    await admin_trial(callback)


@router.callback_query(F.data == "trial_change_days")
async def trial_change_days_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return

    trial = await get_trial()
    await state.set_state(AdminStates.waiting_trial_days)

    await callback.message.edit_text(
        f"✏️ ИЗМЕНЕНИЕ СРОКА ТРИАЛА\n\n"
        f"Текущий срок: {trial.get('days', 1)} дн.\n\n"
        f"Введите новый срок в днях (например: 3):\n\n"
        f"Чтобы отменить — /cancel"
    )


@router.message(AdminStates.waiting_trial_days)
async def trial_set_days(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    if message.text == "/cancel":
        await state.clear()
        await show_admin_panel(message)
        return

    try:
        days = int(message.text.strip())
        if days < 1 or days > 365:
            raise ValueError("out of range")
    except ValueError:
        await message.answer("❌ Введите целое число от 1 до 365")
        return

    trial = await get_trial()
    await set_trial(trial.get("enabled", True), days)
    await state.clear()

    await message.answer(f"✅ Срок триала обновлён: {days} дн.")
    await show_admin_panel(message)


@router.callback_query(F.data == "trial_reset")
async def trial_reset_confirm(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    used = await count_trial_used()

    text = (
        f"⚠️ СБРОС ФЛАГА ТРИАЛА\n\n"
        f"Будет сброшен флаг 'trial_used' у {used} пользователей.\n\n"
        f"После этого:\n"
        f"• Все снова смогут получить бесплатный триал\n"
        f"• Даже те, кто уже использовал\n\n"
        f"⚠️ Это действие нельзя отменить!"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, сбросить", callback_data="trial_reset_do")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_trial")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "trial_reset_do")
async def trial_reset_do(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    await reset_all_trials()
    await callback.answer("✅ Флаг сброшен у всех пользователей", show_alert=True)
    await admin_trial(callback)


# ============================================================
# 💰 ЦЕНЫ
# ============================================================
@router.callback_query(F.data == "admin_pricing")
async def admin_pricing(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    pricing = await get_pricing()
    text = "💰 ЦЕНЫ И ТАРИФЫ\n\nТекущие тарифы:\n"
    for plan, info in pricing.items():
        text += f"  • {info['days']} дней — {info['stars']} ⭐\n"
    text += "\nВыберите тариф для редактирования:"

    buttons = []
    for plan, info in pricing.items():
        buttons.append([InlineKeyboardButton(
            text=f"✏️ {info['days']} дней ({info['stars']} ⭐)",
            callback_data=f"price_edit_{plan}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("price_edit_"))
async def price_edit_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return

    plan = callback.data.replace("price_edit_", "")
    pricing = await get_pricing()
    info = pricing.get(plan, {})

    await state.update_data(plan=plan)
    await state.set_state(AdminStates.waiting_price_days)

    await callback.message.edit_text(
        f"✏️ РЕДАКТИРОВАНИЕ ТАРИФА\n\n"
        f"Текущий:\n"
        f"  • Срок: {info.get('days', '?')} дней\n"
        f"  • Цена: {info.get('stars', '?')} ⭐\n\n"
        f"Введите новый СРОК в днях (например: 14):\n\n"
        f"Чтобы отменить — /cancel"
    )


@router.message(AdminStates.waiting_price_days)
async def price_edit_days(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    if message.text == "/cancel":
        await state.clear()
        await show_admin_panel(message)
        return

    try:
        days = int(message.text.strip())
        if days < 1 or days > 3650:
            raise ValueError("out of range")
    except ValueError:
        await message.answer("❌ Введите целое число от 1 до 3650")
        return

    await state.update_data(days=days)
    await state.set_state(AdminStates.waiting_price_stars)
    await message.answer(f"✅ Срок: {days} дней\n\nВведите новую ЦЕНУ в звёздах:")


@router.message(AdminStates.waiting_price_stars)
async def price_edit_stars(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    if message.text == "/cancel":
        await state.clear()
        await show_admin_panel(message)
        return

    try:
        stars = int(message.text.strip())
        if stars < 1 or stars > 1000000:
            raise ValueError("out of range")
    except ValueError:
        await message.answer("❌ Введите целое число от 1 до 1 000 000")
        return

    data = await state.get_data()
    plan = data["plan"]
    days = data["days"]

    pricing = await get_pricing()
    pricing[plan] = {"days": days, "stars": stars}
    await set_pricing(pricing)

    await state.clear()
    await message.answer(
        f"✅ Тариф обновлён!\n\n"
        f"  • Срок: {days} дней\n"
        f"  • Цена: {stars} ⭐"
    )
    await show_admin_panel(message)


# ============================================================
# ⭐ БАЛАНС
# ============================================================
@router.callback_query(F.data == "admin_balance")
async def admin_balance(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    stats = await get_stats()

    text = (
        f"⭐ БАЛАНС ЗВЁЗД\n\n"
        f"💎 Всего заработано: {stats['total_stars']} ⭐\n"
        f"💳 Платежей: {stats['total_payments']}\n"
        f"👥 Платных: {stats['paid_users']}\n\n"
        f"📊 Откуда берутся звёзды:\n"
        f"  • Пользователи покупают подписки\n"
        f"  • Telegram переводит звёзды боту\n"
        f"  • Вывести можно через @BotFather"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Как вывести", callback_data="admin_withdraw")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_balance")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# 💸 ВЫВОД
# ============================================================
@router.callback_query(F.data == "admin_withdraw")
async def admin_withdraw(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    text = (
        "💸 ВЫВОД СРЕДСТВ\n\n"
        "⚠️ Telegram не позволяет выводить звёзды через API.\n"
        "Вывод делается вручную.\n\n"
        "📋 Как вывести:\n\n"
        "1. Открой @BotFather\n"
        "2. /mybots → выбери бота\n"
        "3. Bot Settings → Payments → Stars\n"
        "4. Нажми Withdraw\n"
        "5. Звёзды конвертируются в TON\n"
        "6. TON придут на кошелёк Fragment\n\n"
        "🔗 Ссылки:\n"
        "• Fragment: https://fragment.com\n"
        "• Документация: https://core.telegram.org/bots/payments-stars\n\n"
        "💰 Курс: 1 ⭐ ≈ $0.013\n\n"
        "💡 Минимум для вывода: 1000 ⭐"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Баланс", callback_data="admin_balance")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# СТАТИСТИКА
# ============================================================
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    stats = await get_stats()
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        total_requests = await conn.fetchval("SELECT COUNT(*) FROM requests")
        today_requests = await conn.fetchval(
            "SELECT COUNT(*) FROM requests WHERE created_at >= CURRENT_DATE"
        )
        new_last_week = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'"
        )

    text = (
        f"📊 СТАТИСТИКА\n\n"
        f"👥 Пользователи:\n"
        f"  • Всего: {stats['total_users']}\n"
        f"  • Новых за 7 дней: {new_last_week or 0}\n"
        f"  • Платных: {stats['paid_users']}\n"
        f"  • Бесплатных: {stats['free_users']}\n\n"
        f"📈 Запросы:\n"
        f"  • Всего: {total_requests or 0}\n"
        f"  • За сегодня: {today_requests or 0}\n\n"
        f"💰 Финансы:\n"
        f"  • Заработано звёзд: {stats['total_stars']}\n"
        f"  • Платежей: {stats['total_payments']}\n\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ПОЛЬЗОВАТЕЛИ
# ============================================================
@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    pool = await db.create_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch(
            "SELECT user_id, first_name, username, created_at, is_paid "
            "FROM users ORDER BY created_at DESC LIMIT 10"
        )

    if not users:
        await callback.message.edit_text("Нет пользователей")
        return

    text = "👥 Последние 10 пользователей:\n\n"
    for i, u in enumerate(users, 1):
        status = "💎" if u["is_paid"] else "🆓"
        name = u["first_name"] or u["username"] or str(u["user_id"])
        created = str(u["created_at"])[:10] if u["created_at"] else "?"
        text += f"{i}. {status} {u['user_id']} — {name} ({created})\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по ID", callback_data="admin_search_user")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_search_user")
async def admin_search_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    await callback.message.edit_text("🔍 Введите ID пользователя:")
    await state.set_state(AdminStates.waiting_search)


@router.message(AdminStates.waiting_search)
async def process_user_search(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный формат ID")
        return

    user_data = await get_user(user_id)
    if not user_data:
        await message.answer("❌ Пользователь не найден")
        await state.clear()
        return

    text = (
        f"👤 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ\n\n"
        f"🆔 ID: {user_data['user_id']}\n"
        f"📝 Имя: {user_data.get('first_name', 'Не указано')}\n"
        f"👤 Username: @{user_data.get('username', 'Нет')}\n"
        f"⭐ Статус: {'💎 Премиум' if user_data.get('is_paid') else '🆓 Бесплатный'}\n"
        f"📅 Подписка до: {user_data.get('subscription_end', 'Не активна')}\n"
        f"🎁 Триал использован: {'Да' if user_data.get('trial_used') else 'Нет'}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выдать подписку", callback_data=f"add_sub_{user_id}")],
        [InlineKeyboardButton(text="🔄 Сбросить триал", callback_data=f"reset_trial_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    await message.answer(text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data.startswith("reset_trial_"))
async def reset_user_trial(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    user_id = int(callback.data.split("_")[2])
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET trial_used = FALSE WHERE user_id = $1", user_id
        )
    await callback.answer(f"✅ Триал сброшен для {user_id}", show_alert=True)


# ============================================================
# ПОДПИСКИ
# ============================================================
@router.callback_query(F.data == "admin_subs")
async def admin_subs(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    pool = await db.create_pool()
    async with pool.acquire() as conn:
        paid_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_paid = TRUE")
        expiring = await conn.fetch(
            "SELECT user_id, first_name, username, subscription_end "
            "FROM users WHERE is_paid = TRUE AND subscription_end BETWEEN $1 AND $2 "
            "ORDER BY subscription_end LIMIT 5",
            today, next_week
        )

    text = f"💎 УПРАВЛЕНИЕ ПОДПИСКАМИ\n\n👥 Активных: {paid_count}\n\n"
    if expiring:
        text += "⚠️ Истекают в ближайшие 7 дней:\n"
        for u in expiring:
            name = u["first_name"] or u["username"] or str(u["user_id"])
            text += f"  • {u['user_id']} — {name} (до {u['subscription_end']})\n"
    else:
        text += "✅ Нет истекающих в ближайшие 7 дней"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выдать подписку", callback_data="admin_give_sub")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_give_sub")
async def admin_give_sub_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    await callback.message.edit_text("➕ Введите ID пользователя:")
    await state.set_state(AdminStates.waiting_user_id)


@router.message(AdminStates.waiting_user_id)
async def process_user_id_for_sub(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный формат ID")
        return

    user_data = await get_user(user_id)
    if not user_data:
        await message.answer("❌ Пользователь не найден")
        await state.clear()
        return

    await state.update_data(user_id=user_id)
    await state.set_state(AdminStates.waiting_subscription_days)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней", callback_data="sub_7")],
        [InlineKeyboardButton(text="30 дней", callback_data="sub_30")],
        [InlineKeyboardButton(text="90 дней", callback_data="sub_90")],
        [InlineKeyboardButton(text="365 дней", callback_data="sub_365")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back")],
    ])
    await message.answer(
        f"👤 Пользователь: {user_data.get('first_name', user_id)}\n\nВыберите срок:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("sub_"))
async def process_subscription_days(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    days_map = {"sub_7": 7, "sub_30": 30, "sub_90": 90, "sub_365": 365}
    days = days_map.get(callback.data, 7)
    data = await state.get_data()
    user_id = data.get("user_id")
    if user_id:
        await set_subscription(user_id, days)
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        await callback.message.edit_text(
            f"✅ Подписка активирована!\n\n"
            f"👤 {user_id}\n"
            f"📅 {days} дней\n"
            f"🗓️ До: {end_date}"
        )
        try:
            from loader import bot
            await bot.send_message(
                user_id,
                f"🎉 Подписка активирована на {days} дней!\n"
                f"Действует до: {end_date}"
            )
        except Exception:
            pass
    await state.clear()
    await show_admin_panel(callback)


@router.callback_query(F.data.startswith("add_sub_"))
async def add_sub_from_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    user_id = int(callback.data.split("_")[2])
    await state.update_data(user_id=user_id)
    await state.set_state(AdminStates.waiting_subscription_days)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней", callback_data="sub_7")],
        [InlineKeyboardButton(text="30 дней", callback_data="sub_30")],
        [InlineKeyboardButton(text="90 дней", callback_data="sub_90")],
        [InlineKeyboardButton(text="365 дней", callback_data="sub_365")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back")],
    ])
    await callback.message.edit_text(
        f"👤 Пользователь: {user_id}\n\nВыберите срок:",
        reply_markup=keyboard
    )


# ============================================================
# РАССЫЛКА
# ============================================================
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    await callback.message.edit_text(
        "📢 РАССЫЛКА\n\n"
        "Введите текст сообщения для рассылки.\n\n"
        "Чтобы отменить — /cancel"
    )
    await state.set_state(AdminStates.waiting_broadcast)


@router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    if message.text == "/cancel":
        await state.clear()
        await show_admin_panel(message)
        return

    await state.clear()
    msg = await message.answer("📢 Начинаю рассылку...")

    pool = await db.create_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT user_id FROM users")

    success = 0
    fail = 0
    from loader import bot
    for u in users:
        try:
            await bot.send_message(u["user_id"], message.text)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await msg.edit_text(
        f"✅ Рассылка завершена\n\n"
        f"📤 Отправлено: {success}\n"
        f"❌ Не доставлено: {fail}\n"
        f"📊 Всего: {success + fail}"
    )
    await show_admin_panel(message)
