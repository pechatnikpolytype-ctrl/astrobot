from aiogram import Router, F, Bot
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


@router.callback_query(F.data == "subscription_info")
async def subscription_info(callback: CallbackQuery):
    from database.postgres_db import get_subscription_days_left, get_pricing, is_trial_active
    from keyboards.main import payment_keyboard
    from locales import t
    import logging
    _log = logging.getLogger(__name__)
    user_id = callback.from_user.id
    lang = "ru"
    try:
        from database.postgres_db import get_user_lang_cached
        lang = await get_user_lang_cached(user_id) or "ru"
    except Exception:
        pass
    days_left = await get_subscription_days_left(user_id)
    trial = await is_trial_active(user_id)
    pricing = await get_pricing()
    if days_left > 0 and not trial:
        text = f"⭐ Ваша подписка активна\n\nОсталось дней: {days_left}\n\nХотите продлить? Дни будут добавлены к текущему сроку."
    elif trial:
        text = f"🎁 Пробный период\n\nОсталось дней: {days_left}\n\nОформите подписку, чтобы продолжить без ограничений."
    else:
        text = "⭐ Подписка\n\nВыберите тариф:"
    try:
        await callback.message.edit_text(text, reply_markup=await payment_keyboard(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=await payment_keyboard(lang))
    await callback.answer()

