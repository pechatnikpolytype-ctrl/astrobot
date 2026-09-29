from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database.postgres_db import (
    create_user, is_paid, has_trial_used,
    set_trial_used, set_subscription, get_trial
)
from keyboards.main import welcome_keyboard, main_menu_keyboard, payment_keyboard
from config import ADMINS, FREE_MODE

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    await create_user(user_id, username, first_name)

    # Режим "всё бесплатно"
    if FREE_MODE:
        text = f"🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!"
        await message.answer(text, reply_markup=await welcome_keyboard())
        return

    trial_used = await has_trial_used(user_id)
    paid = await is_paid(user_id)
    trial = await get_trial()

    # Если триал выключен админом
    if not trial.get("enabled", True):
        if not paid:
            await message.answer(
                "🔒 Оформите подписку для доступа к функциям бота:",
                reply_markup=await payment_keyboard()
            )
            return
        # paid — пускаем дальше
        text = f"🌟 Добро пожаловать, {first_name}!"
        await message.answer(text, reply_markup=await welcome_keyboard())
        return

    # Триал включён
    trial_days = trial.get("days", 1)

    if not trial_used and not paid:
        await set_subscription(user_id, trial_days)
        await set_trial_used(user_id)
        await message.answer(
            f"🎁 Вам активирован пробный период на {trial_days} дн.!\n"
            f"Пользуйтесь всеми функциями бота бесплатно."
        )
    elif not paid and trial_used:
        await message.answer(
            "🔒 Пробный период закончился. Оформите подписку:",
            reply_markup=await payment_keyboard()
        )

    text = f"🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!"
    await message.answer(text, reply_markup=await welcome_keyboard())


@router.callback_query(F.data == "check_status")
async def check_status(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_paid_user = await is_paid(user_id)

    if is_paid_user or user_id in ADMINS:
        await callback.message.edit_text(
            "Главное меню AstroBot v2 PRO:",
            reply_markup=main_menu_keyboard(user_id)
        )
    else:
        await callback.message.edit_text(
            "🔒 Пробный период закончился. Выберите тариф:",
            reply_markup=await payment_keyboard()
        )


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not await is_paid(user_id) and user_id not in ADMINS:
        await callback.message.edit_text(
            "❌ Доступ запрещён.",
            reply_markup=await payment_keyboard()
        )
        return
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu_keyboard(user_id)
    )
