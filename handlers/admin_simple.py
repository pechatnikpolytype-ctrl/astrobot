from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import ADMINS, BOT_TOKEN
from locales import t
from database.postgres_db import (
    get_user, get_stats, set_subscription, is_paid, db,
    get_pricing, set_pricing,
    get_trial, set_trial,
    reset_all_trials, count_trial_used,
    get_ai_limits, set_ai_limits,
    reset_all_ai_usage, get_total_ai_usage_today, get_top_ai_users,
    get_ai_history, count_ai_history,
    clean_time_dependent_cache, clean_old_ai_history_v2, get_ai_cache_stats,
    is_admin,
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
    if hasattr(target, "from_user"):
        lang = await _admin_lang(target.from_user.id)
    else:
        lang = "ru"

    stats = await get_stats()
    pricing = await get_pricing()
    trial = await get_trial()
    ai_limits = await get_ai_limits()
    ai_usage = await get_total_ai_usage_today()

    trial_status = f"{t('ADMIN_TRIAL_ON', lang)} ({trial['days']} {t('ADMIN_TRIAL_DAYS', lang)})" if trial.get("enabled") else t("ADMIN_TRIAL_OFF", lang)

    text = (
        f"{t('ADMIN_PANEL_TITLE', lang)}\n"
        + t("ADMIN_STATS_HEADER", lang) + "\n"
        + f"  \u2022 {t('ADMIN_TOTAL_USERS', lang)}: {stats['total_users']}\n"
        + f"  \u2022 {t('ADMIN_PAID_USERS', lang)}: {stats['paid_users']}\n"
        + f"  \u2022 {t('ADMIN_FREE_USERS', lang)}: {stats['free_users']}\n\n"
        + f"\u2b50 {t('ADMIN_BALANCE_LABEL', lang)}: {stats['total_stars']} {t('ADMIN_STARS_SUFFIX', lang)}\n"
        + f"\U0001F4B3 {t('ADMIN_PAYMENTS_LABEL', lang)}: {stats['total_payments']}\n\n"
        + f"\U0001F381 {t('ADMIN_TRIAL_LABEL', lang)}: {trial_status}\n"
        f"🤖 AI: free={ai_limits['free']}, premium={ai_limits['premium']}\n"
        f"\U0001F4CA {t('ADMIN_AI_TODAY', lang)}: {ai_usage}\n\n"
        f"{t('ADMIN_TARIFFS_HEADER', lang)}\n"
    )
    for plan, info in pricing.items():
        text += "  " + t("ADMIN_TARIFF_LINE", lang, days=info['days'], stars=info['stars']) + "\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_PRICING", lang), callback_data="admin_pricing"),
         InlineKeyboardButton(text=t("ADMIN_BTN_BALANCE", lang), callback_data="admin_balance")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_TRIAL", lang), callback_data="admin_trial"),
         InlineKeyboardButton(text=t("ADMIN_BTN_AI", lang), callback_data="admin_ai")],
	 [InlineKeyboardButton(text=t("ADMIN_BTN_REMINDERS", lang), callback_data="admin_reminders"),
     InlineKeyboardButton(text=t("ADMIN_BTN_CLEANUP", lang), callback_data="admin_cleanup")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_AI_HISTORY", lang), callback_data="admin_ai_history"),
         InlineKeyboardButton(text=t("ADMIN_BTN_CACHE", lang), callback_data="admin_cache")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_STATS", lang), callback_data="admin_stats"),
         InlineKeyboardButton(text=t("ADMIN_BTN_USERS", lang), callback_data="admin_users")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_SUBS", lang), callback_data="admin_subs"),
         InlineKeyboardButton(text=t("ADMIN_BTN_BROADCAST", lang), callback_data="admin_broadcast")],
                [InlineKeyboardButton(text=t("ADMIN_BTN_DAILY_FACTS", lang), callback_data="admin_daily_facts")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_ADMINS", lang), callback_data="admin_manage_admins")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_ADS", lang), callback_data="admin_ads")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="main_menu")],
    ])

    if isinstance(target, Message):
        await target.answer(text, reply_markup=keyboard)
    else:
        try:
            await target.message.edit_text(text, reply_markup=keyboard)
        except Exception:
            await target.message.answer(text, reply_markup=keyboard)


async def _admin_lang(user_id: int) -> str:
    """Admin language (fallback ru)."""
    try:
        from config import MULTILANG_ENABLED
        if not MULTILANG_ENABLED:
            return "ru"
        from database.postgres_db import get_user_lang_cached
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


@router.message(Command("admin"))
async def admin_command(message: Message):
    lang = await _admin_lang(message.from_user.id)

    if not await is_admin(message.from_user.id):
        await message.answer(t("ADMIN_NO_ACCESS", lang))
        return
    await show_admin_panel(message)


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
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
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    stats = await get_ai_cache_stats()

    text = (
        f"{t('ADMIN_CACHE_TITLE', lang)}\n"
        f"{t('ADMIN_STATS_HEADER', lang)}\n"
        f"  \u2022 {t('ADMIN_CACHE_TOTAL', lang)}: {stats['total']}\n"
        f"  \u2022 {t('ADMIN_CACHE_PERMANENT', lang)}: {stats['permanent']}\n"
        f"  \u2022 {t('ADMIN_CACHE_TEMP', lang)}: {stats['time_dependent']}\n"
        f"  \u2022 {t('ADMIN_CACHE_PERSONAL', lang)}: {stats['personal']}\n"
        f"  \u2022 {t('ADMIN_CACHE_GENERAL', lang)}: {stats['general']}\n\n"
        f"{t('ADMIN_CACHE_HINT', lang)}\n"
        f"  \u2022 {t('ADMIN_CACHE_HINT_TEMP', lang)}\n"
        f"  \u2022 {t('ADMIN_CACHE_HINT_OLD', lang)}\n"
        f"  \u2022 {t('ADMIN_CACHE_HINT_ALL', lang)}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_CACHE_TEMP", lang), callback_data="cache_clear_temp")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_CACHE_OLD", lang), callback_data="cache_clear_old")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_CACHE_ALL", lang), callback_data="cache_clear_all")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "cache_clear_temp")
async def cache_clear_temp(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    await clean_time_dependent_cache()
    await callback.answer(t("ADMIN_CACHE_CLEARED_TEMP", lang), show_alert=True)
    await admin_cache(callback)


@router.callback_query(F.data == "cache_clear_old")
async def cache_clear_old(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    await clean_old_ai_history_v2(14)
    await callback.answer(t("ADMIN_CACHE_CLEARED_OLD", lang), show_alert=True)
    await admin_cache(callback)


@router.callback_query(F.data == "cache_clear_all")
async def cache_clear_all_confirm(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_YES_DO", lang), callback_data="cache_clear_all_do")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_CANCEL", lang), callback_data="admin_cache")],
    ])
    await callback.message.edit_text(
        t("ADMIN_CACHE_CLEAR_CONFIRM", lang),
        reply_markup=keyboard
    )


@router.callback_query(F.data == "cache_clear_all_do")
async def cache_clear_all_do(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM ai_history")
    await callback.answer(t("ADMIN_CACHE_CLEARED_ALL", lang), show_alert=True)
    await admin_cache(callback)


# ============================================================
# 📜 ИСТОРИЯ AI
# ============================================================
@router.callback_query(F.data == "admin_ai_history")
async def admin_ai_history(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    total = await count_ai_history()
    history = await get_ai_history(10)

    text = t("ADMIN_AI_HISTORY_TITLE", lang) + f"\n\n{t('ADMIN_AI_HISTORY_TOTAL', lang)}: {total}\n\n{t('ADMIN_AI_HISTORY_LAST10', lang)}\n\n"
    if not history:
        text += t("ADMIN_AI_HISTORY_EMPTY", lang)
    else:
        for i, h in enumerate(history, 1):
            q = (h.get("question") or "")[:40]
            date = str(h["created_at"])[:16] if h.get("created_at") else "?"
            text += f"{i}. [{h['request_type']}] {q} ({date})\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_CACHE_MGMT", lang), callback_data="admin_cache")],
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
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    limits = await get_ai_limits()
    usage = await get_total_ai_usage_today()
    top = await get_top_ai_users(5)

    text = (
        f"{t('ADMIN_AI_LIMITS_TITLE', lang)}\n"
        f"{t('ADMIN_AI_LIMITS_HEADER', lang)}\n"
        f"  {t('ADMIN_AI_LIMITS_FREE', lang, limit=limits['free'])}\n"
        f"  {t('ADMIN_AI_LIMITS_PREMIUM', lang, limit=limits['premium'])}\n\n"
        f"{t('ADMIN_AI_LIMITS_TODAY', lang, usage=usage)}\n\n"
    )
    if top:
        text += t("ADMIN_AI_LIMITS_TOP", lang) + "\n"
        for u in top:
            text += f"  • {u['user_id']}: {u['count']}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✏️ Free ({limits['free']})", callback_data="ai_set_free")],
        [InlineKeyboardButton(text=f"✏️ Premium ({limits['premium']})", callback_data="ai_set_premium")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_AI_RESET", lang), callback_data="ai_reset_all")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_AI_HISTORY", lang), callback_data="admin_ai_history")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "ai_set_free")
async def ai_set_free_start(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    limits = await get_ai_limits()
    await state.set_state(AdminStates.waiting_ai_limit_free)
    await callback.message.edit_text(
        t("ADMIN_AI_FREE_EDIT", lang, limit=limits['free'])
    )


@router.message(AdminStates.waiting_ai_limit_free)
async def ai_set_free_save(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)

    if not await is_admin(message.from_user.id):
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
        await message.answer(t("ADMIN_ERR_NUMBER_MINUS1", lang))
        return
    limits = await get_ai_limits()
    await set_ai_limits(val, limits["premium"])
    await state.clear()
    await message.answer(f"✅ Free: {val}")
    await show_admin_panel(message)


@router.callback_query(F.data == "ai_set_premium")
async def ai_set_premium_start(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    limits = await get_ai_limits()
    await state.set_state(AdminStates.waiting_ai_limit_premium)
    await callback.message.edit_text(
        t("ADMIN_AI_PREMIUM_EDIT", lang, limit=limits['premium'])
    )


@router.message(AdminStates.waiting_ai_limit_premium)
async def ai_set_premium_save(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)

    if not await is_admin(message.from_user.id):
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
        await message.answer(t("ADMIN_ERR_NUMBER_MINUS1", lang))
        return
    limits = await get_ai_limits()
    await set_ai_limits(limits["free"], val)
    await state.clear()
    await message.answer(f"✅ Premium: {val}")
    await show_admin_panel(message)


@router.callback_query(F.data == "ai_reset_all")
async def ai_reset_all_confirm(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="ai_reset_do")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="admin_ai")],
    ])
    await callback.message.edit_text(
        t("ADMIN_AI_RESET_CONFIRM", lang),
        reply_markup=keyboard
    )


@router.callback_query(F.data == "ai_reset_do")
async def ai_reset_do(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    await reset_all_ai_usage()
    await callback.answer(t("ADMIN_AI_RESET_DONE", lang), show_alert=True)
    await admin_ai(callback)


# ============================================================
# 🎁 ТРИАЛ
# ============================================================
@router.callback_query(F.data == "admin_trial")
async def admin_trial(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    trial = await get_trial()
    used_count = await count_trial_used()
    status = t("ADMIN_TRIAL_ON", lang) if trial.get("enabled") else t("ADMIN_TRIAL_OFF", lang)
    text = t("ADMIN_TRIAL_TITLE", lang) + "\n\n" + t("ADMIN_TRIAL_STATUS", lang, status=status) + "\n" + t("ADMIN_TRIAL_DURATION", lang, days=trial.get('days', 1)) + "\n" + t("ADMIN_TRIAL_USED", lang, count=used_count)
    toggle = t("ADMIN_TRIAL_TOGGLE_OFF", lang) if trial.get("enabled") else t("ADMIN_TRIAL_TOGGLE_ON", lang)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle, callback_data="trial_toggle")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_TRIAL_DURATION", lang), callback_data="trial_change_days")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_TRIAL_RESET", lang), callback_data="trial_reset")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "trial_toggle")
async def trial_toggle(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    trial = await get_trial()
    new_enabled = not trial.get("enabled", True)
    await set_trial(new_enabled, trial.get("days", 1))
    await callback.answer(t("ADMIN_TRIAL_TOGGLED", lang), show_alert=True)
    await admin_trial(callback)


@router.callback_query(F.data == "trial_change_days")
async def trial_change_days_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    trial = await get_trial()
    await state.set_state(AdminStates.waiting_trial_days)
    await callback.message.edit_text(
        f"✏️ Срок триала: {trial.get('days', 1)} дн.\n\nВведите новое (1-365):\n\n/cancel — отмена"
    )


@router.message(AdminStates.waiting_trial_days)
async def trial_set_days(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)

    if not await is_admin(message.from_user.id):
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
        await message.answer(t("ADMIN_ERR_NUMBER_1_365", lang))
        return
    trial = await get_trial()
    await set_trial(trial.get("enabled", True), days)
    await state.clear()
    await message.answer(t("ADMIN_TRIAL_DURATION_SAVED", lang, days=days))
    await show_admin_panel(message)


@router.callback_query(F.data == "trial_reset")
async def trial_reset_confirm(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    used = await count_trial_used()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="trial_reset_do")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="admin_trial")],
    ])
    await callback.message.edit_text(t("ADMIN_TRIAL_RESET_CONFIRM", lang, used=used), reply_markup=keyboard)


@router.callback_query(F.data == "trial_reset_do")
async def trial_reset_do(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    await reset_all_trials()
    await callback.answer(t("ADMIN_AI_RESET_DONE", lang), show_alert=True)
    await admin_trial(callback)


# ============================================================
# 💰 ЦЕНЫ
# ============================================================
@router.callback_query(F.data == "admin_pricing")
async def admin_pricing(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    pricing = await get_pricing()
    text = f"{t('ADMIN_PRICING_TITLE', lang)}\n\n"
    for plan, info in pricing.items():
        text += "  " + t("ADMIN_PRICING_LINE", lang, days=info['days'], stars=info['stars']) + "\n"
    buttons = []
    for plan, info in pricing.items():
        buttons.append([InlineKeyboardButton(
            text=t("ADMIN_PRICING_EDIT_BTN", lang, days=info['days'], stars=info['stars']),
            callback_data=f"price_edit_{plan}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("price_edit_"))
async def price_edit_start(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    plan = callback.data.replace("price_edit_", "")
    await state.update_data(plan=plan)
    await state.set_state(AdminStates.waiting_price_days)
    await callback.message.edit_text(t("ADMIN_PRICING_ENTER_DAYS", lang))


@router.message(AdminStates.waiting_price_days)
async def price_edit_days(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if not await is_admin(message.from_user.id):
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
    await message.answer(t("ADMIN_PRICING_DAYS_SAVED", lang, days=days))


@router.message(AdminStates.waiting_price_stars)
async def price_edit_stars(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if not await is_admin(message.from_user.id):
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
    await message.answer(t("ADMIN_PRICING_BOTH_SAVED", lang, days=data['days'], stars=stars))
    await show_admin_panel(message)


# ============================================================
# ⭐ БАЛАНС
# ============================================================
@router.callback_query(F.data == "admin_balance")
async def admin_balance(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    stats = await get_stats()
    text = (
        f"{t('ADMIN_BALANCE_TITLE', lang)}\n\n"
        f"{t('ADMIN_BALANCE_TOTAL', lang, stars=stats['total_stars'])}\n"
        f"{t('ADMIN_BALANCE_PAYMENTS', lang, count=stats['total_payments'])}\n"
        f"{t('ADMIN_BALANCE_PAID', lang, count=stats['paid_users'])}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_WITHDRAW", lang), callback_data="admin_withdraw")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_withdraw")
async def admin_withdraw(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    text = (
        f"{t('ADMIN_WITHDRAW_TITLE', lang)}\n\n"
        f"{t('ADMIN_WITHDRAW_INSTRUCTIONS', lang)}\n\n"
        f"{t('ADMIN_WITHDRAW_MINIMUM', lang)}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_BALANCE", lang), callback_data="admin_balance")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
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
    lang = await _admin_lang(callback.from_user.id)
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
        f"{t('ADMIN_STATS_TITLE', lang)}\n\n"
        f"{t('ADMIN_STATS_TOTAL', lang, count=stats['total_users'])}\n"
        f"{t('ADMIN_STATS_WEEK', lang, count=new_week or 0)}\n"
        f"{t('ADMIN_STATS_BY_TARIFF', lang)}\n"
        f"{t('ADMIN_STATS_FREE', lang, count=tariffs['free'])}\n"
        f"{t('ADMIN_STATS_TRIAL', lang, count=tariffs['trial'])}\n"
        f"{t('ADMIN_STATS_7D', lang, count=tariffs['7d'])}\n"
        f"{t('ADMIN_STATS_30D', lang, count=tariffs['30d'])}\n"
        f"{t('ADMIN_STATS_90D', lang, count=tariffs['90d'])}\n"
        f"{t('ADMIN_STATS_ADMINS', lang, count=tariffs['admins'])}\n"
        f"{t('ADMIN_STATS_REQUESTS', lang, count=total_req or 0)}\n"
        f"{t('ADMIN_STATS_TODAY', lang, count=today_req or 0)}\n"
        f"{t('ADMIN_STATS_AI', lang, count=ai_usage)}\n"
        f"{t('ADMIN_STATS_EARNED', lang, stars=stats['total_stars'])}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_REFRESH", lang), callback_data="admin_stats")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
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
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("""
            SELECT user_id, first_name, username, created_at, is_paid
            FROM users ORDER BY created_at DESC LIMIT 10
        """)
    if not users:
        await callback.message.edit_text(t("ADMIN_USERS_NO_USERS", lang))
        return
    text = t("ADMIN_USERS_LAST10", lang) + "\n\n"
    for i, u in enumerate(users, 1):
        st = "💎" if u["is_paid"] else "🆓"
        name = u["first_name"] or u["username"] or str(u["user_id"])
        c = str(u["created_at"])[:10] if u["created_at"] else "?"
        text += f"{i}. {st} {u['user_id']} — {name} ({c})\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_SEARCH", lang), callback_data="admin_search_user")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_search_user")
async def admin_search_user(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(t("ADMIN_USERS_ENTER_ID", lang))
    await state.set_state(AdminStates.waiting_search)


@router.message(AdminStates.waiting_search)
async def process_user_search(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if not await is_admin(message.from_user.id):
        return
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(t("ADMIN_USERS_INVALID_ID", lang))
        return
    u = await get_user(user_id)
    if not u:
        await message.answer(t("ADMIN_USERS_NOT_FOUND", lang))
        await state.clear()
        return
    text = (
        f"👤 {u['user_id']}\n"
        f"📝 {u.get('first_name', '?')}\n"
        f"{t('ADMIN_USER_USERNAME', lang, username=u.get('username', t('ADMIN_USER_NO_USERNAME', lang)))}\n"
        f"{(t('ADMIN_USER_PREMIUM', lang) if u.get('is_paid') else t('ADMIN_USER_FREE', lang))}\n"
        f"{t('ADMIN_USER_UNTIL', lang, date=u.get('subscription_end', t('ADMIN_USER_NOT_ACTIVE', lang)))}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_ADD_SUB", lang), callback_data=f"add_sub_{user_id}")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_RESET_TRIAL", lang), callback_data=f"reset_trial_{user_id}")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    await message.answer(text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data.startswith("reset_trial_"))
async def reset_user_trial(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    user_id = int(callback.data.split("_")[2])
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET trial_used = FALSE WHERE user_id = $1", user_id)
    await callback.answer(t("ADMIN_TRIAL_RESET_DONE", lang, user_id=user_id), show_alert=True)


# ============================================================
# ПОДПИСКИ
# ============================================================
@router.callback_query(F.data == "admin_subs")
async def admin_subs(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
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
    text = t("ADMIN_SUBS_TITLE", lang) + "\n\n" + t("ADMIN_SUBS_ACTIVE", lang, count=paid) + "\n\n"
    if expiring:
        text += t("ADMIN_SUBS_EXPIRING", lang) + "\n"
        for u in expiring:
            text += "  " + t("ADMIN_SUBS_EXPIRING_LINE", lang, user_id=u['user_id'], date=u['subscription_end']) + "\n"
    else:
        text += t("ADMIN_SUBS_NO_EXPIRING", lang)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_BTN_GIVE_SUB", lang), callback_data="admin_give_sub")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_give_sub")
async def admin_give_sub_start(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(t("ADMIN_SUBS_ENTER_ID", lang))
    await state.set_state(AdminStates.waiting_user_id)


@router.message(AdminStates.waiting_user_id)
async def process_user_id_for_sub(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if not await is_admin(message.from_user.id):
        return
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(t("ADMIN_USERS_INVALID_ID", lang))
        return
    u = await get_user(user_id)
    if not u:
        await message.answer(t("ADMIN_USERS_NOT_FOUND", lang))
        await state.clear()
        return
    await state.update_data(user_id=user_id)
    await state.set_state(AdminStates.waiting_subscription_days)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_SUBS_DAYS_7", lang), callback_data="sub_7")],
        [InlineKeyboardButton(text=t("ADMIN_SUBS_DAYS_30", lang), callback_data="sub_30")],
        [InlineKeyboardButton(text=t("ADMIN_SUBS_DAYS_90", lang), callback_data="sub_90")],
        [InlineKeyboardButton(text=t("ADMIN_SUBS_DAYS_365", lang), callback_data="sub_365")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_CANCEL_BACK", lang), callback_data="admin_back")],
    ])
    await message.answer(f"\U0001F464 {u.get('first_name', user_id)}\n\n{t('ADMIN_SUBS_CHOOSE_DAYS', lang)}", reply_markup=keyboard)


@router.callback_query(F.data.startswith("sub_"))
async def process_subscription_days(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    days_map = {"sub_7": 7, "sub_30": 30, "sub_90": 90, "sub_365": 365}
    days = days_map.get(callback.data, 7)
    data = await state.get_data()
    user_id = data.get("user_id")
    if user_id:
        await set_subscription(user_id, days)
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        await callback.message.edit_text(t("ADMIN_SUBS_GIVEN", lang, user_id=user_id, days=days, date=end_date))
        try:
            from loader import bot
            await bot.send_message(user_id, t("ADMIN_SUBS_NOTIFY", lang, days=days, date=end_date))
        except Exception:
            pass
    await state.clear()
    await show_admin_panel(callback)


@router.callback_query(F.data.startswith("add_sub_"))
async def add_sub_from_user(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    user_id = int(callback.data.split("_")[2])
    await state.update_data(user_id=user_id)
    await state.set_state(AdminStates.waiting_subscription_days)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("ADMIN_SUBS_DAYS_7", lang), callback_data="sub_7")],
        [InlineKeyboardButton(text=t("ADMIN_SUBS_DAYS_30", lang), callback_data="sub_30")],
        [InlineKeyboardButton(text=t("ADMIN_SUBS_DAYS_90", lang), callback_data="sub_90")],
        [InlineKeyboardButton(text=t("ADMIN_SUBS_DAYS_365", lang), callback_data="sub_365")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_CANCEL_BACK", lang), callback_data="admin_back")],
    ])
    await callback.message.edit_text(f"\U0001F464 {user_id}\n\n{t('ADMIN_SUBS_CHOOSE_DAYS', lang)}", reply_markup=keyboard)


# ============================================================
# РАССЫЛКА
# ============================================================
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(t("ADMIN_BROADCAST_ENTER", lang))
    await state.set_state(AdminStates.waiting_broadcast)


@router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if not await is_admin(message.from_user.id):
        return
    if message.text == "/cancel":
        await state.clear()
        await show_admin_panel(message)
        return
    await state.clear()
    msg = await message.answer(t("ADMIN_BROADCAST_SENDING", lang))
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
    await msg.edit_text(t("ADMIN_BROADCAST_DONE", lang, success=success, fail=fail))
    await show_admin_panel(message)


# ============================================================
# 🔔 НАПОМИНАНИЯ
# ============================================================
@router.callback_query(F.data == "admin_reminders")
async def admin_reminders(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    from database.postgres_db import get_reminder_settings
    settings = await get_reminder_settings()
    enabled = settings.get("enabled", True)
    status = t("ADMIN_TRIAL_ON", lang) if enabled else t("ADMIN_TRIAL_OFF", lang)

    text = (
        f"{t('ADMIN_REMINDERS_TITLE', lang)}\n\n"
        f"{t('ADMIN_REMINDERS_STATUS', lang, status=status)}\n"
        f"{t('ADMIN_REMINDERS_WHAT', lang)}\n"
        f"{t('ADMIN_REMINDERS_WHO', lang)}\n"
        f"{t('ADMIN_REMINDERS_FREQ', lang)}\n"
        f"{t('ADMIN_REMINDERS_TIME', lang)}\n"
        f"{t('ADMIN_REMINDERS_BUTTON', lang)}\n"
        f"{t('ADMIN_REMINDERS_INACTIVE', lang)}\n"
    )
    toggle = t("ADMIN_BTN_TOGGLE_OFF", lang) if enabled else t("ADMIN_BTN_TOGGLE_ON", lang)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle, callback_data="reminders_toggle")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_TEST_SELF", lang), callback_data="reminders_test")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "reminders_toggle")
async def reminders_toggle(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    from database.postgres_db import get_reminder_settings, set_reminder_settings
    settings = await get_reminder_settings()
    new_enabled = not settings.get("enabled", True)
    await set_reminder_settings(new_enabled)
    await callback.answer(t("ADMIN_TOGGLED", lang), show_alert=True)
    await admin_reminders(callback)


@router.callback_query(F.data == "reminders_test")
async def reminders_test(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    try:
        from services.reminder import send_test_reminder
        from loader import bot
        ok = await send_test_reminder(bot, callback.from_user.id)
        if ok:
            await callback.answer(t("ADMIN_SENT", lang), show_alert=True)
        else:
            await callback.answer(t("ADMIN_ERR", lang), show_alert=True)
    except Exception as e:
        logger.error(f"Тест напоминаний: {e}")
        await callback.answer(t("ADMIN_ERR_DETAIL", lang, err=e), show_alert=True)


# ============================================================
# 🧹 АВТООЧИСТКА КЭША
# ============================================================
@router.callback_query(F.data == "admin_cleanup")
async def admin_cleanup(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    from database.postgres_db import get_cache_cleanup_settings, get_ai_cache_stats
    settings = await get_cache_cleanup_settings()
    stats = await get_ai_cache_stats()
    enabled = settings.get("enabled", True)
    status = t("ADMIN_TRIAL_ON", lang) if enabled else t("ADMIN_TRIAL_OFF", lang)

    text = (
        f"{t('ADMIN_CLEANUP_TITLE', lang)}\n\n"
        f"{t('ADMIN_REMINDERS_STATUS', lang, status=status)}\n"
        f"{t('ADMIN_CLEANUP_SCHEDULE', lang)}\n"
        f"{t('ADMIN_CLEANUP_DELETES', lang)}\n"
        f"{t('ADMIN_CLEANUP_DEL_TEMP', lang)}\n"
        f"{t('ADMIN_CLEANUP_DEL_PERM', lang)}\n\n"
        f"{t('ADMIN_CLEANUP_STATE', lang)}\n"
        f"  \u2022 {t('ADMIN_CACHE_TOTAL', lang)}: {stats['total']}\n"
        f"  \u2022 {t('ADMIN_CACHE_TEMP', lang)}: {stats['time_dependent']}\n"
        f"  \u2022 {t('ADMIN_CACHE_PERMANENT', lang)}: {stats['permanent']}\n"
    )
    toggle = t("ADMIN_BTN_TOGGLE_OFF", lang) if enabled else t("ADMIN_BTN_TOGGLE_ON", lang)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle, callback_data="cleanup_toggle")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_RUN_NOW", lang), callback_data="cleanup_now")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "cleanup_toggle")
async def cleanup_toggle(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if not await is_admin(callback.from_user.id):
        return
    from database.postgres_db import get_cache_cleanup_settings, set_cache_cleanup_settings
    settings = await get_cache_cleanup_settings()
    new_enabled = not settings.get("enabled", True)
    await set_cache_cleanup_settings(new_enabled)
    await callback.answer(t("ADMIN_TOGGLED", lang), show_alert=True)
    await admin_cleanup(callback)


@router.callback_query(F.data == "cleanup_now")
async def cleanup_now(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    try:
        from database.postgres_db import auto_clean_cache
        await auto_clean_cache()
        await callback.answer(t("ADMIN_CLEANUP_DONE", lang), show_alert=True)
    except Exception as e:
        logger.error(f"Очистка: {e}")
        await callback.answer(t("ADMIN_ERR_DETAIL", lang, err=e), show_alert=True)
    await admin_cleanup(callback)


# ============================================================
# ✨ УТРЕННИЕ ФАКТЫ
# ============================================================
@router.callback_query(F.data == "admin_daily_facts")
async def admin_daily_facts(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
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
    status = t("ADMIN_TRIAL_ON", lang) if enabled else t("ADMIN_TRIAL_OFF", lang)

    text = (
        f"{t('ADMIN_DAILY_FACTS_TITLE', lang)}\n\n"
        f"{t('ADMIN_DAILY_FACTS_STATUS', lang, status=status)}\n"
        f"{t('ADMIN_DAILY_FACTS_TIME', lang, h=settings.get('hour_utc', 9), m=settings.get('minute_utc', 0))}\n"
        f"{t('ADMIN_DAILY_FACTS_TOTAL_USERS', lang, count=total)}\n\n"
    )
    if today and today.get("text"):
        short = today["text"][:200] + "..." if len(today["text"]) > 200 else today["text"]
        text += t("ADMIN_DAILY_FACTS_TODAY", lang, text=short) + "\n\n"

    text += t("ADMIN_DAILY_FACTS_HISTORY", lang, count=len(history))

    toggle = t("ADMIN_BTN_TOGGLE_OFF", lang) if enabled else t("ADMIN_BTN_TOGGLE_ON", lang)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle, callback_data="daily_facts_toggle")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_SEND_NOW", lang), callback_data="daily_facts_test")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_REGEN", lang), callback_data="daily_facts_regen")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_HISTORY", lang), callback_data="daily_facts_history")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_BACK", lang), callback_data="admin_back")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "daily_facts_toggle")
async def daily_facts_toggle(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    from database.postgres_db import get_daily_fact_settings, set_daily_fact_settings
    settings = await get_daily_fact_settings()
    new = not settings.get("enabled", True)
    await set_daily_fact_settings(enabled=new)
    await callback.answer(t("ADMIN_TOGGLED", lang), show_alert=True)
    await admin_daily_facts(callback)


@router.callback_query(F.data == "daily_facts_test")
async def daily_facts_test(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    try:
        from services.daily_facts import send_test_fact
        from loader import bot
        ok = await send_test_fact(bot, callback.from_user.id)
        await callback.answer("✅ Отправлено" if ok else "❌ Ошибка", show_alert=True)
    except Exception as e:
        logger.error(f"Тест фактов: {e}")
        await callback.answer(t("ADMIN_ERR_DETAIL", lang, err=e), show_alert=True)


@router.callback_query(F.data == "daily_facts_regen")
async def daily_facts_regen(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    try:
        from services.daily_facts import generate_fact
        from database.postgres_db import set_today_fact, save_fact_history
        new_fact = await generate_fact()
        if new_fact:
            await set_today_fact(new_fact)
            await save_fact_history(new_fact)
            await callback.answer(t("ADMIN_FACTS_REGEN_OK", lang), show_alert=True)
        else:
            await callback.answer(t("ADMIN_FACTS_REGEN_FAIL", lang), show_alert=True)
    except Exception as e:
        logger.error(f"Регенерация: {e}")
        await callback.answer(t("ADMIN_ERR_DETAIL", lang, err=e), show_alert=True)
    await admin_daily_facts(callback)


@router.callback_query(F.data == "daily_facts_history")
async def daily_facts_history(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        return
    from database.postgres_db import get_fact_history
    history = await get_fact_history()
    if not history:
        await callback.answer(t("ADMIN_FACTS_HISTORY_EMPTY", lang), show_alert=True)
        return

    text = t("ADMIN_FACTS_HISTORY_TITLE", lang) + "\n\n"
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
    lang = await _admin_lang(callback.from_user.id)

    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    from database.postgres_db import is_main_admin, get_extra_admins
    from config import ADMINS as MAIN_ADMINS

    is_main = await is_main_admin(callback.from_user.id)
    main_list = "\n".join([f"  • {a}" for a in MAIN_ADMINS]) or "  (нет)"
    extra = await get_extra_admins()
    extra_list = "\n".join([f"  • {a}" for a in extra]) if extra else "  (нет)"

    text = (
        f"{t('ADMIN_ADMINS_TITLE', lang)}\n\n"
        f"{t('ADMIN_ADMINS_MAIN', lang)}\n{main_list}\n\n"
        f"{t('ADMIN_ADMINS_EXTRA', lang)}\n{extra_list}\n\n"
    )

    if is_main:
        text += t("ADMIN_ADMINS_HINT", lang)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("ADMIN_BTN_ADD", lang), callback_data="admins_add")],
            [InlineKeyboardButton(text=t("ADMIN_BTN_REMOVE", lang), callback_data="admins_remove")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
        ])
    else:
        text += t("ADMIN_ADMINS_ONLY_MAIN", lang)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
        ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "admins_add")
async def admins_add_start(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)

    from database.postgres_db import is_main_admin
    if not await is_main_admin(callback.from_user.id):
        await callback.answer(t("ADMIN_ADMINS_ONLY_MAIN_ALERT", lang), show_alert=True)
        return
    await state.set_state(AdminManageStates.waiting_new_admin_id)
    await callback.message.edit_text(
        f"{t('ADMIN_ADMINS_ADD_TITLE', lang)}\n\n"
        f"{t('ADMIN_ADMINS_ADD_HINT', lang)}\n"
        f"{t('ADMIN_ADMINS_ADD_EXAMPLE', lang)}\n\n"
        f"{t('ADMIN_ADMINS_ADD_WARNING', lang)}\n\n"
        "/cancel — отмена"
    )


@router.message(AdminManageStates.waiting_new_admin_id)
async def admins_add_save(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)

    from database.postgres_db import is_main_admin, add_extra_admin
    if not await is_main_admin(message.from_user.id):
        await state.clear()
        return
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("ADMIN_CANCELLED", lang))
        return
    try:
        new_id = int(message.text.strip())
        if new_id <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t("ADMIN_ADMINS_ERR_NUMBER", lang))
        return

    from config import ADMINS as MAIN_ADMINS
    if new_id in MAIN_ADMINS:
        await message.answer(t("ADMIN_ADMINS_ALREADY_MAIN", lang))
        await state.clear()
        return

    success = await add_extra_admin(new_id)
    if success:
        await message.answer(t("ADMIN_ADMINS_ADDED", lang, new_id=new_id))
        try:
            from loader import bot
            await bot.send_message(
                new_id,
                t("ADMIN_ADMINS_NOTIFY", lang)
            )
        except Exception:
            pass
    else:
        await message.answer(t("ADMIN_ADMINS_ALREADY", lang, new_id=new_id))
    await state.clear()
    await show_admin_panel(message)


@router.callback_query(F.data == "admins_remove")
async def admins_remove_menu(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    from database.postgres_db import is_main_admin, get_extra_admins
    if not await is_main_admin(callback.from_user.id):
        await callback.answer(t("ADMIN_ADMINS_ONLY_MAIN_ALERT", lang), show_alert=True)
        return
    extra = await get_extra_admins()
    if not extra:
        await callback.answer(t("ADMIN_ADMINS_NO_EXTRA", lang), show_alert=True)
        return
    buttons = []
    for admin_id in extra:
        buttons.append([InlineKeyboardButton(
            text=f"🗑️ {admin_id}",
            callback_data=f"admin_rm_{admin_id}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_manage_admins")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(t("ADMIN_ADMINS_CHOOSE_REMOVE", lang), reply_markup=keyboard)


# ВАЖНО: сначала более специфичный фильтр (do_), потом общий (rm_)
@router.callback_query(F.data.startswith("admin_rm_do_"))
async def admins_remove_do(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    from database.postgres_db import is_main_admin, remove_extra_admin
    if not await is_main_admin(callback.from_user.id):
        await callback.answer(t("ADMIN_NO_ACCESS", lang), show_alert=True)
        return
    target_id = int(callback.data.replace("admin_rm_do_", ""))
    success = await remove_extra_admin(target_id)
    if success:
        await callback.answer(t("ADMIN_ADMINS_REMOVED_ALERT", lang, target_id=target_id), show_alert=True)
        try:
            from loader import bot
            await bot.send_message(
                target_id,
                f"{t('ADMIN_ADMINS_REVOKED', lang)}\n"
            )
        except Exception:
            pass
    else:
        await callback.answer(t("ADMIN_ADMINS_NOT_FOUND", lang), show_alert=True)
    await admin_manage_admins(callback)


@router.callback_query(F.data.startswith("admin_rm_"))
async def admins_remove_confirm(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)

    from database.postgres_db import is_main_admin
    if not await is_main_admin(callback.from_user.id):
        await callback.answer(t("ADMIN_NO_ACCESS", lang), show_alert=True)
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
        [InlineKeyboardButton(text=t("ADMIN_BTN_YES", lang), callback_data=f"admin_rm_do_{target_id}")],
        [InlineKeyboardButton(text=t("ADMIN_BTN_CANCEL", lang), callback_data="admin_manage_admins")],
    ])
    await callback.message.edit_text(
        t("ADMIN_ADMINS_REMOVE_CONFIRM", lang, target_id=target_id),
        reply_markup=keyboard
    )
