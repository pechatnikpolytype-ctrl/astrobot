from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database.postgres_db import add_payment, set_subscription, get_user, get_pricing
from config import ADMINS, BOT_TOKEN
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("stars_balance"))
async def cmd_stars_balance(message: Message):
    if message.from_user.id not in ADMINS:
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
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    user_id = message.from_user.id
    stars_paid = payment.total_amount
    payload = payment.invoice_payload

    try:
        _, days_str, stars_str = payload.split("_")
        days = int(days_str)
        stars_expected = int(stars_str)

        if stars_paid != stars_expected:
            logger.error(f"Сумма не совпадает: {stars_paid} vs {stars_expected}")
            await message.answer("❌ Ошибка оплаты")
            return

        await set_subscription(user_id, days)
        await add_payment(user_id, stars_paid, payment.telegram_payment_charge_id, days)

        # Уведомление админам
        bot = Bot(token=BOT_TOKEN)
        user_data = await get_user(user_id)
        name = (user_data.get("first_name") or user_data.get("username") or str(user_id)) if user_data else str(user_id)
        for admin_id in ADMINS:
            try:
                await bot.send_message(
                    admin_id,
                    f"💎 Новая подписка!\n\n"
                    f"👤 {name} (ID: {user_id})\n"
                    f"📅 {days} дней\n"
                    f"⭐ {stars_paid} звёзд"
                )
            except Exception:
                pass
        await bot.session.close()

        await message.answer(
            f"✅ Подписка активирована на {days} дней!\n\n"
            f"Благодарим за использование AstroBot."
        )
        from keyboards.main import main_menu_keyboard
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard(user_id))
    except Exception as e:
        logger.error(f"Ошибка активации: {e}")
        await message.answer("❌ Ошибка. Администратор уведомлён.")


@router.message(Command("refund"))
async def cmd_refund(message: Message):
    await message.answer("Для возврата свяжитесь: @SupportBot")


@router.message(Command("paysupport"))
async def cmd_pay_support(message: Message):
    await message.answer("Проблемы с оплатой? Напишите @SupportBot")
