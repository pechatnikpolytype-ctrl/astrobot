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
    get_ai_limits, set_ai_limits,
    reset_all_ai_usage, get_total_ai_usage_today, get_top_ai_users,
    get_ai_history, count_ai_history,
    clean_time_dependent_cache, clean_old_ai_history_v2, get_ai_cache_stats,
)
from datetime import datetime, timedelta
import logging
import asyncio

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
    waiting_ai_limit_free = State()
    waiting_ai_limit_premium = State()


async def show_admin_panel(target, edit: bool = True):
    stats = await get_stats()
    pricing = await get_pricing()
    trial = await get_trial()
    ai_limits = await get_ai_limits()
    ai_usage = await get_total_ai_usage_today()

    trial_status = f"✅ ВКЛ ({trial['days']} дн.)" if trial.get("enabled") else "❌ ВЫКЛ"

    text = (
        "👑 АДМИН-ПАНЕЛЬ\n\n"
        f"📊 Статистика:\n"
        f"  • Всего: {stats['total_users']}\n"
        f"  • Платных: {stats['paid_users']}\n"
        f"  • Бесплатных: {stats['free_users']}\n\n"
        f"⭐ Баланс: {stats['total_stars']} звёзд\n"
        f"💳 Платежей: {stats['total_payments']}\n\n"
        f"🎁 Триал: {trial_status}\n"
        f"🤖 AI: free={ai_limits['free']}, premium={ai_limits['premium']}\n"
        f"📊 AI сегодня: {ai_usage}\n\n"
        f"💰 Тарифы:\n"
    )
    for plan, info in pricing.items():
        text += f"  • {info['days']} дней — {info['stars']} ⭐\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Цены", callback_data="admin_pricing"),
         InlineKeyboardButton(text="⭐ Баланс", callback_data="admin_balance")],
        [InlineKeyboardButton(text="🎁 Триал", callback_data="admin_trial"),
         InlineKeyboardButton(text="🤖 AI-лимиты", callback_data="admin_ai")],
	 [InlineKeyboardButton(text="🔔 Напоминания", callback_data="admin_reminders"),
     InlineKeyboardButton(text="🧹 Автоочистка", callback_data="admin_cleanup")],
        [InlineKeyboardButton(text="📜 История AI", callback_data="admin_ai_history"),
         InlineKeyboardButton(text="🗑️ Кэш AI", callback_data="admin_cache")],
        [InlineKeyboardButton(text="📊 Стата", callback_data="admin_stats"),
         InlineKeyboardButton(text="👥 Юзеры", callback_data="admin_users")],
        [InlineKeyboardButton(text="💎 Подписки", callback_data="admin_subs"),
         InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
                [InlineKeyboardButton(text="✨ Утренние факты", callback_data="admin_daily_facts")],
        [InlineKeyboardButton(text="👑 Админы", callback_data="admin_manage_admins")],
        [InlineKeyboardButton(text="📢 Реклама", callback_data="admin_ads")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu")],
    ])

    if isinstance(target, Message):
        await target.answer(text, reply_markup=keyboard)
    else:
        try:
            await target.message.edit_text(text, reply_markup=keyboard)
        except Exception:
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
        return
    await show_admin_panel(callback)


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await show_admin_panel(callback)


# ============================================================
# 🗑️ КЭШ AI
# ============================================================
@router.callback_query(F.data == "admin_cache")
async def admin_cache(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    stats = await get_ai_cache_stats()

    text = (
        f"🗑️ УПРАВЛЕНИЕ КЭШЕМ AI\n\n"
        f"📊 Статистика:\n"
        f"  • Всего записей: {stats['total']}\n"
        f"  • Постоянных: {stats['permanent']}\n"
        f"  • Временных: {stats['time_dependent']}\n"
        f"  • Личных: {stats['personal']}\n"
        f"  • Общих: {stats['general']}\n\n"
        f"Что делают кнопки:\n"
        f"  • Очистить временные — удалит ответы на 'сегодня', 'завтра'\n"
        f"  • Очистить старые — удалит записи старше 14 дней\n"
        f"  • Очистить ВСЁ — полностью сбросит кэш"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧹 Очистить временные", callback_data="cache_clear_temp")],
        [InlineKeyboardButton(text="🗑️ Очистить старые (>14д)", callback_data="cache_clear_old")],
        [InlineKeyboardButton(text="⚠️ Очистить ВСЁ", callback_data="cache_clear_all")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "cache_clear_temp")
async def cache_clear_temp(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    await clean_time_dependent_cache()
    await callback.answer("✅ Временные удалены", show_alert=True)
    await admin_cache(callback)


@router.callback_query(F.data == "cache_clear_old")
async def cache_clear_old(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    await clean_old_ai_history_v2(14)
    await callback.answer("✅ Старые (>14д) удалены", show_alert=True)
    await admin_cache(callback)


@router.callback_query(F.data == "cache_clear_all")
async def cache_clear_all_confirm(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ ДА, ОЧИСТИТЬ ВСЁ", callback_data="cache_clear_all_do")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cache")],
    ])
    await callback.message.edit_text(
        "⚠️ ОЧИСТИТЬ ВЕСЬ КЭШ?\n\nЭто удалит ВСЕ сохранённые ответы AI.\nНельзя отменить.",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "cache_clear_all_do")
async def cache_clear_all_do(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM ai_history")
    await callback.answer("✅ Кэш полностью очищен", show_alert=True)
    await admin_cache(callback)


# ============================================================
# 📜 ИСТОРИЯ AI
# ============================================================
@router.callback_query(F.data == "admin_ai_history")
async def admin_ai_history(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    total = await count_ai_history()
    history = await get_ai_history(10)

    text = f"📜 ИСТОРИЯ AI\n\nВсего: {total}\n\nПоследние 10:\n\n"
    if not history:
        text += "(пусто)"
    else:
        for i, h in enumerate(history, 1):
            q = (h.get("question") or "")[:40]
            date = str(h["created_at"])[:16] if h.get("created_at") else "?"
            text += f"{i}. [{h['request_type']}] {q} ({date})\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Управление кэшем", callback_data="admin_cache")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ai")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# 🤖 AI-ЛИМИТЫ
# ============================================================
@router.callback_query(F.data == "admin_ai")
async def admin_ai(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    limits = await get_ai_limits()
    usage = await get_total_ai_usage_today()
    top = await get_top_ai_users(5)

    text = (
        f"🤖 AI-ЛИМИТЫ\n\n"
        f"📊 Настройки:\n"
        f"  • Бесплатные: {limits['free']} /день\n"
        f"  • Премиум: {limits['premium']} /день\n\n"
        f"📈 Сегодня: {usage} запросов\n\n"
    )
    if top:
        text += "🏆 Топ:\n"
        for u in top:
            text += f"  • {u['user_id']}: {u['count']}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✏️ Free ({limits['free']})", callback_data="ai_set_free")],
        [InlineKeyboardButton(text=f"✏️ Premium ({limits['premium']})", callback_data="ai_set_premium")],
        [InlineKeyboardButton(text="🔄 Сбросить счётчики", callback_data="ai_reset_all")],
        [InlineKeyboardButton(text="📜 История", callback_data="admin_ai_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "ai_set_free")
async def ai_set_free_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    limits = await get_ai_limits()
    await state.set_state(AdminStates.waiting_ai_limit_free)
    await callback.message.edit_text(
        f"✏️ Free: {limits['free']}\n\nВведите новое значение (0 = отключить, -1 = без лимита):\n\n/cancel — отмена"
    )


@router.message(AdminStates.waiting_ai_limit_free)
async def ai_set_free_save(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    if message.text == "/cancel":
        await state.clear()
        await show_admin_panel(message)
        return
    try:
        val = int(message.text.strip())
        if val < -1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Число >= -1")
        return
    limits = await get_ai_limits()
    await set_ai_limits(val, limits["premium"])
    await state.clear()
    await message.answer(f"✅ Free: {val}")
    await show_admin_panel(message)


@router.callback_query(F.data == "ai_set_premium")
async def ai_set_premium_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    limits = await get_ai_limits()
    await state.set_state(AdminStates.waiting_ai_limit_premium)
    await callback.message.edit_text(
        f"✏️ Premium: {limits['premium']}\n\nВведите новое (0 = отключить, -1 = без лимита):\n\n/cancel — отмена"
    )


@router.message(AdminStates.waiting_ai_limit_premium)
async def ai_set_premium_save(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    if message.text == "/cancel":
        await state.clear()
        await show_admin_panel(message)
        return
    try:
        val = int(message.text.strip())
        if val < -1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Число >= -1")
        return
    limits = await get_ai_limits()
    await set_ai_limits(limits["free"], val)
    await state.clear()
    await message.answer(f"✅ Premium: {val}")
    await show_admin_panel(message)


@router.callback_query(F.data == "ai_reset_all")
async def ai_reset_all_confirm(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="ai_reset_do")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="admin_ai")],
    ])
    await callback.message.edit_text(
        "🔄 Сбросить счётчики ВСЕМ?",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "ai_reset_do")
async def ai_reset_do(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    await reset_all_ai_usage()
    await callback.answer("✅ Сброшено", show_alert=True)
    await admin_ai(callback)


# ============================================================
# 🎁 ТРИАЛ
# ============================================================
@router.callback_query(F.data == "admin_trial")
async def admin_trial(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    trial = await get_trial()
    used_count = await count_trial_used()
    status = "✅ ВКЛ" if trial.get("enabled") else "❌ ВЫКЛ"
    text = f"🎁 ТРИАЛ\n\nСтатус: {status}\nСрок: {trial.get('days', 1)} дн.\nИспользовали: {used_count} чел."
    toggle = "❌ Выключить" if trial.get("enabled") else "✅ Включить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle, callback_data="trial_toggle")],
        [InlineKeyboardButton(text="✏️ Срок", callback_data="trial_change_days")],
        [InlineKeyboardButton(text="🔄 Сбросить флаг", callback_data="trial_reset")],
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
    await callback.answer("Переключено", show_alert=True)
    await admin_trial(callback)


@router.callback_query(F.data == "trial_change_days")
async def trial_change_days_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    trial = await get_trial()
    await state.set_state(AdminStates.waiting_trial_days)
    await callback.message.edit_text(
        f"✏️ Срок триала: {trial.get('days', 1)} дн.\n\nВведите новое (1-365):\n\n/cancel — отмена"
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
            raise ValueError
    except ValueError:
        await message.answer("❌ Число 1-365")
        return
    trial = await get_trial()
    await set_trial(trial.get("enabled", True), days)
    await state.clear()
    await message.answer(f"✅ Срок: {days} дн.")
    await show_admin_panel(message)


@router.callback_query(F.data == "trial_reset")
async def trial_reset_confirm(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    used = await count_trial_used()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="trial_reset_do")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="admin_trial")],
    ])
    await callback.message.edit_text(f"⚠️ Сбросить флаг у {used} пользователей?", reply_markup=keyboard)


@router.callback_query(F.data == "trial_reset_do")
async def trial_reset_do(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    await reset_all_trials()
    await callback.answer("✅ Сброшено", show_alert=True)
    await admin_trial(callback)


# ============================================================
# 💰 ЦЕНЫ
# ============================================================
@router.callback_query(F.data == "admin_pricing")
async def admin_pricing(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    pricing = await get_pricing()
    text = "💰 ЦЕНЫ\n\n"
    for plan, info in pricing.items():
        text += f"  • {info['days']} дней — {info['stars']} ⭐\n"
    buttons = []
    for plan, info in pricing.items():
        buttons.append([InlineKeyboardButton(
            text=f"✏️ {info['days']}д ({info['stars']}⭐)",
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
    await state.update_data(plan=plan)
    await state.set_state(AdminStates.waiting_price_days)
    await callback.message.edit_text("Введите новый СРОК в днях:\n\n/cancel — отмена")


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
            raise ValueError
    except ValueError:
        await message.answer("❌ 1-3650")
        return
    await state.update_data(days=days)
    await state.set_state(AdminStates.waiting_price_stars)
    await message.answer(f"✅ {days} дней\n\nВведите ЦЕНУ в звёздах:")


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
            raise ValueError
    except ValueError:
        await message.answer("❌ 1-1000000")
        return
    data = await state.get_data()
    pricing = await get_pricing()
    pricing[data["plan"]] = {"days": data["days"], "stars": stars}
    await set_pricing(pricing)
    await state.clear()
    await message.answer(f"✅ {data['days']} дней — {stars} ⭐")
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
        f"⭐ БАЛАНС\n\n"
        f"💎 Всего: {stats['total_stars']} ⭐\n"
        f"💳 Платежей: {stats['total_payments']}\n"
        f"👥 Платных: {stats['paid_users']}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Как вывести", callback_data="admin_withdraw")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_withdraw")
async def admin_withdraw(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    text = (
        "💸 ВЫВОД\n\n"
        "@BotFather → /mybots → бот → Payments → Stars → Withdraw\n\n"
        "Минимум: 1000 ⭐"
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
    ai_usage = await get_total_ai_usage_today()
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        total_req = await conn.fetchval("SELECT COUNT(*) FROM requests")
        today_req = await conn.fetchval("SELECT COUNT(*) FROM requests WHERE created_at >= CURRENT_DATE")
        new_week = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'")
    text = (
        f"📊 СТАТИСТИКА\n\n"
        f"👥 Всего: {stats['total_users']}\n"
        f"🆕 За 7 дней: {new_week or 0}\n"
        f"💎 Платных: {stats['paid_users']}\n\n"
        f"📈 Запросов: {total_req or 0}\n"
        f"📅 Сегодня: {today_req or 0}\n"
        f"🤖 AI сегодня: {ai_usage}\n\n"
        f"💰 Заработано: {stats['total_stars']} ⭐"
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
        users = await conn.fetch("""
            SELECT user_id, first_name, username, created_at, is_paid
            FROM users ORDER BY created_at DESC LIMIT 10
        """)
    if not users:
        await callback.message.edit_text("Нет пользователей")
        return
    text = "👥 Последние 10:\n\n"
    for i, u in enumerate(users, 1):
        st = "💎" if u["is_paid"] else "🆓"
        name = u["first_name"] or u["username"] or str(u["user_id"])
        c = str(u["created_at"])[:10] if u["created_at"] else "?"
        text += f"{i}. {st} {u['user_id']} — {name} ({c})\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search_user")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_search_user")
async def admin_search_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    await callback.message.edit_text("🔍 Введите ID:")
    await state.set_state(AdminStates.waiting_search)


@router.message(AdminStates.waiting_search)
async def process_user_search(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный ID")
        return
    u = await get_user(user_id)
    if not u:
        await message.answer("❌ Не найден")
        await state.clear()
        return
    text = (
        f"👤 {u['user_id']}\n"
        f"📝 {u.get('first_name', '?')}\n"
        f"👤 @{u.get('username', 'Нет')}\n"
        f"⭐ {'💎 Премиум' if u.get('is_paid') else '🆓 Бесплатный'}\n"
        f"📅 до {u.get('subscription_end', 'Не активна')}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Подписка", callback_data=f"add_sub_{user_id}")],
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
        await conn.execute("UPDATE users SET trial_used = FALSE WHERE user_id = $1", user_id)
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
        paid = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_paid = TRUE")
        expiring = await conn.fetch("""
            SELECT user_id, first_name, subscription_end FROM users
            WHERE is_paid = TRUE AND subscription_end BETWEEN $1 AND $2
            ORDER BY subscription_end LIMIT 5
        """, today, next_week)
    text = f"💎 ПОДПИСКИ\n\nАктивных: {paid}\n\n"
    if expiring:
        text += "⚠️ Истекают:\n"
        for u in expiring:
            text += f"  • {u['user_id']} — до {u['subscription_end']}\n"
    else:
        text += "✅ Нет истекающих"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выдать", callback_data="admin_give_sub")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_give_sub")
async def admin_give_sub_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    await callback.message.edit_text("➕ Введите ID:")
    await state.set_state(AdminStates.waiting_user_id)


@router.message(AdminStates.waiting_user_id)
async def process_user_id_for_sub(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный ID")
        return
    u = await get_user(user_id)
    if not u:
        await message.answer("❌ Не найден")
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
    await message.answer(f"👤 {u.get('first_name', user_id)}\n\nВыберите срок:", reply_markup=keyboard)


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
        await callback.message.edit_text(f"✅ {user_id} — {days} дней (до {end_date})")
        try:
            from loader import bot
            await bot.send_message(user_id, f"🎉 Подписка на {days} дней! До {end_date}")
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
    await callback.message.edit_text(f"👤 {user_id}\n\nВыберите срок:", reply_markup=keyboard)


# ============================================================
# РАССЫЛКА
# ============================================================
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    await callback.message.edit_text("📢 Введите текст рассылки:\n\n/cancel — отмена")
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
    msg = await message.answer("📢 Рассылка...")
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
    await msg.edit_text(f"✅ Отправлено: {success}\n❌ Не доставлено: {fail}")
    await show_admin_panel(message)


# ============================================================
# 🔔 НАПОМИНАНИЯ
# ============================================================
@router.callback_query(F.data == "admin_reminders")
async def admin_reminders(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    from database.postgres_db import get_reminder_settings
    settings = await get_reminder_settings()
    enabled = settings.get("enabled", True)
    status = "✅ ВКЛ" if enabled else "❌ ВЫКЛ"

    text = (
        f"🔔 НАПОМИНАНИЯ О ПРОФИЛЕ\n\n"
        f"Статус: {status}\n\n"
        f"Что делают напоминания:\n"
        f"  • Пользователям с пустым профилем\n"
        f"  • Не чаще раза в 7 дней\n"
        f"  • В 18:00 UTC\n"
        f"  • С кнопкой 'Заполнить профиль'\n\n"
        f"Неактивные (> 30 дней) — не получают.\n"
    )
    toggle = "❌ Выключить" if enabled else "✅ Включить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle, callback_data="reminders_toggle")],
        [InlineKeyboardButton(text="🧪 Тест (себе)", callback_data="reminders_test")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "reminders_toggle")
async def reminders_toggle(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    from database.postgres_db import get_reminder_settings, set_reminder_settings
    settings = await get_reminder_settings()
    new_enabled = not settings.get("enabled", True)
    await set_reminder_settings(new_enabled)
    await callback.answer("✅ Изменено", show_alert=True)
    await admin_reminders(callback)


@router.callback_query(F.data == "reminders_test")
async def reminders_test(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    try:
        from services.reminder import send_test_reminder
        from loader import bot
        ok = await send_test_reminder(bot, callback.from_user.id)
        if ok:
            await callback.answer("✅ Отправлено", show_alert=True)
        else:
            await callback.answer("❌ Ошибка", show_alert=True)
    except Exception as e:
        logger.error(f"Тест напоминаний: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


# ============================================================
# 🧹 АВТООЧИСТКА КЭША
# ============================================================
@router.callback_query(F.data == "admin_cleanup")
async def admin_cleanup(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    from database.postgres_db import get_cache_cleanup_settings, get_ai_cache_stats
    settings = await get_cache_cleanup_settings()
    stats = await get_ai_cache_stats()
    enabled = settings.get("enabled", True)
    status = "✅ ВКЛ" if enabled else "❌ ВЫКЛ"

    text = (
        f"🧹 АВТООЧИСТКА КЭША\n\n"
        f"Статус: {status}\n\n"
        f"Расписание: 03:00 UTC ежедневно\n"
        f"Удаляет:\n"
        f"  • Временные > 7 дней\n"
        f"  • Постоянные > 90 дней\n\n"
        f"📊 Текущее состояние:\n"
        f"  • Всего записей: {stats['total']}\n"
        f"  • Временных: {stats['time_dependent']}\n"
        f"  • Постоянных: {stats['permanent']}\n"
    )
    toggle = "❌ Выключить" if enabled else "✅ Включить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle, callback_data="cleanup_toggle")],
        [InlineKeyboardButton(text="🧪 Запустить сейчас", callback_data="cleanup_now")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "cleanup_toggle")
async def cleanup_toggle(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    from database.postgres_db import get_cache_cleanup_settings, set_cache_cleanup_settings
    settings = await get_cache_cleanup_settings()
    new_enabled = not settings.get("enabled", True)
    await set_cache_cleanup_settings(new_enabled)
    await callback.answer("✅ Изменено", show_alert=True)
    await admin_cleanup(callback)


@router.callback_query(F.data == "cleanup_now")
async def cleanup_now(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    try:
        from database.postgres_db import auto_clean_cache
        await auto_clean_cache()
        await callback.answer("✅ Очистка выполнена", show_alert=True)
    except Exception as e:
        logger.error(f"Очистка: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
    await admin_cleanup(callback)


# ============================================================
# ✨ УТРЕННИЕ ФАКТЫ
# ============================================================
@router.callback_query(F.data == "admin_daily_facts")
async def admin_daily_facts(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    from database.postgres_db import (
        get_daily_fact_settings, get_today_fact, get_fact_history,
        count_all_users,
    )
    settings = await get_daily_fact_settings()
    today = await get_today_fact()
    history = await get_fact_history()
    total = await count_all_users()

    enabled = settings.get("enabled", True)
    status = "✅ ВКЛ" if enabled else "❌ ВЫКЛ"

    text = (
        f"✨ УТРЕНИЕ ФАКТЫ\n\n"
        f"Статус: {status}\n"
        f"Время: {settings.get('hour_utc', 9):02d}:{settings.get('minute_utc', 0):02d} UTC\n"
        f"👥 Всего пользователей: {total}\n\n"
    )
    if today and today.get("text"):
        short = today["text"][:200] + "..." if len(today["text"]) > 200 else today["text"]
        text += f"📅 Факт на сегодня:\n{short}\n\n"

    text += f"📚 История: {len(history)} фактов"

    toggle = "❌ Выключить" if enabled else "✅ Включить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle, callback_data="daily_facts_toggle")],
        [InlineKeyboardButton(text="🧪 Отправить сейчас (себе)", callback_data="daily_facts_test")],
        [InlineKeyboardButton(text="🔄 Сгенерировать новый", callback_data="daily_facts_regen")],
        [InlineKeyboardButton(text="📚 История", callback_data="daily_facts_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "daily_facts_toggle")
async def daily_facts_toggle(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    from database.postgres_db import get_daily_fact_settings, set_daily_fact_settings
    settings = await get_daily_fact_settings()
    new = not settings.get("enabled", True)
    await set_daily_fact_settings(enabled=new)
    await callback.answer("✅ Изменено", show_alert=True)
    await admin_daily_facts(callback)


@router.callback_query(F.data == "daily_facts_test")
async def daily_facts_test(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    try:
        from services.daily_facts import send_test_fact
        from loader import bot
        ok = await send_test_fact(bot, callback.from_user.id)
        await callback.answer("✅ Отправлено" if ok else "❌ Ошибка", show_alert=True)
    except Exception as e:
        logger.error(f"Тест фактов: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@router.callback_query(F.data == "daily_facts_regen")
async def daily_facts_regen(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    try:
        from services.daily_facts import generate_fact
        from database.postgres_db import set_today_fact, save_fact_history
        new_fact = await generate_fact()
        if new_fact:
            await set_today_fact(new_fact)
            await save_fact_history(new_fact)
            await callback.answer("✅ Сгенерирован", show_alert=True)
        else:
            await callback.answer("❌ Не удалось", show_alert=True)
    except Exception as e:
        logger.error(f"Регенерация: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
    await admin_daily_facts(callback)


@router.callback_query(F.data == "daily_facts_history")
async def daily_facts_history(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    from database.postgres_db import get_fact_history
    history = await get_fact_history()
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return

    text = "📚 ИСТОРИЯ ФАКТОВ (7 дней)\n\n"
    for i, item in enumerate(history[:7], 1):
        short = item["text"][:150] + "..." if len(item["text"]) > 150 else item["text"]
        text += f"{i}. [{item['date']}]\n{short}\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_daily_facts")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


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
