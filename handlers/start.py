from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery

from database.postgres_db import (
    create_user, is_paid, has_trial_used,
    set_trial_used, set_subscription, get_trial,
    get_user, get_referral_settings, get_user_lang_cached,
    add_referral, count_user_referrals_with_bonus, mark_referral_bonus_paid,
)
from keyboards.main import (
    welcome_keyboard, main_menu_keyboard, payment_keyboard, main_reply_keyboard,
)
from config import ADMINS, FREE_MODE, MULTILANG_ENABLED
from locales import t
import logging

logger = logging.getLogger(__name__)
router = Router()


async def _process_referral(new_user_id: int, referrer_id: int):
    if new_user_id == referrer_id:
        return
    settings = await get_referral_settings()
    if not settings.get("enabled", True):
        return
    max_bonuses = settings.get("max_bonuses", 10)
    if max_bonuses > 0:
        count = await count_user_referrals_with_bonus(referrer_id)
        if count >= max_bonuses:
            return
    bonus_days = settings.get("bonus_days", 3)
    added = await add_referral(referrer_id, new_user_id, bonus_days)
    if not added:
        return
    await set_subscription(new_user_id, bonus_days)
    await set_subscription(referrer_id, bonus_days)
    await mark_referral_bonus_paid(new_user_id)
    try:
        from loader import bot
        await bot.send_message(referrer_id, f"🎉 По вашей ссылке зарегистрировался новый! Вам начислено {bonus_days} дней.")
    except Exception:
        pass


@router.message(Command("start"))
async def start_handler(message: Message, command: CommandObject = None):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    # Реферальная ссылка
    if command and command.args and command.args.startswith("ref_"):
        try:
            referrer_id = int(command.args.replace("ref_", ""))
            existing = await get_user(user_id)
            if not existing:
                await create_user(user_id, username, first_name)
                await _process_referral(user_id, referrer_id)
        except Exception as e:
            logger.warning(f"Ошибка реферальной ссылки: {e}")

    await create_user(user_id, username, first_name)

    # === ТРИАЛ ===
    if not FREE_MODE:
        trial_used = await has_trial_used(user_id)
        paid = await is_paid(user_id)
        trial = await get_trial()

        # Триал включён и юзер ещё не использовал и не оплачивал
        if trial.get("enabled", True) and not trial_used and not paid:
            trial_days = trial.get("days", 3)
            await set_subscription(user_id, trial_days)
            await set_trial_used(user_id)
            await message.answer(
                f"🎁 Вам активирован пробный период на {trial_days} дн.!\n"
                f"Пользуйтесь всеми функциями бота бесплатно."
            )
        elif not paid and trial_used:
            await message.answer(
                "🔒 Пробный период закончился. Оформите подписку:",
                reply_markup=await payment_keyboard(),
            )
            return

    # Выбор языка (если включена мультиязычность)
    if MULTILANG_ENABLED:
        try:
            user_data = await get_user(user_id)
            if not user_data or not user_data.get("language"):
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                from locales import get_lang_name
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=get_lang_name("ru"), callback_data="lang_first_ru")],
                    [InlineKeyboardButton(text=get_lang_name("en"), callback_data="lang_first_en")],
                    [InlineKeyboardButton(text=get_lang_name("de"), callback_data="lang_first_de")],
                ])
                await message.answer("🌍 Выберите язык:", reply_markup=kb)
                return
        except Exception as e:
            logger.warning(f"lang check: {e}")

    # Показ главного меню
    from handlers.menu_commands import show_main_menu_from_start
    await show_main_menu_from_start(message, bot=None)


@router.callback_query(F.data == "check_status")
async def check_status(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_paid_user = await is_paid(user_id)
    admin_flag = user_id in ADMINS
    if is_paid_user or admin_flag:
        await callback.message.edit_text(
            "🏠 Главное меню:",
            reply_markup=main_menu_keyboard(user_id)
        )
    else:
        await callback.message.edit_text(
            "🔒 Пробный период закончился. Выберите тариф:",
            reply_markup=await payment_keyboard()
        )


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_paid_user = await is_paid(user_id)
    admin_flag = user_id in ADMINS
    if not is_paid_user and not admin_flag and not FREE_MODE:
        await callback.message.edit_text(
            "❌ Доступ запрещён.",
            reply_markup=await payment_keyboard()
        )
        return
    await callback.message.edit_text(
        "🏠 Главное меню:",
        reply_markup=main_menu_keyboard(user_id)
    )