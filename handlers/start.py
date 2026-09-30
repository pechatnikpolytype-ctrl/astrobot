from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from database.postgres_db import (
    create_user, is_paid, has_trial_used,
    set_trial_used, set_subscription, get_trial,
    get_user, add_referral, get_referral_settings,
    count_user_referrals_with_bonus, mark_referral_bonus_paid,
    set_last_menus, get_last_menus,
)
from keyboards.main import (
    welcome_keyboard, main_menu_keyboard, payment_keyboard, main_reply_keyboard,
)
from config import ADMINS, FREE_MODE
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
        await bot.send_message(
            referrer_id,
            f"🎉 По вашей ссылке зарегистрировался новый пользователь!\n\n"
            f"Вам начислено {bonus_days} дней Премиум."
        )
    except Exception:
        pass


@router.message(Command("start"))
async def start_handler(message: Message, command: CommandObject = None):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

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

    # Отправляем меню с фактом через menu_commands
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
    if not is_paid_user and not admin_flag:
        await callback.message.edit_text(
            "❌ Доступ запрещён.",
            reply_markup=await payment_keyboard()
        )
        return
    await callback.message.edit_text(
        "🏠 Главное меню:",
        reply_markup=main_menu_keyboard(user_id)
    )
