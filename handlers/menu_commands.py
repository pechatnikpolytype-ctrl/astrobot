import logging
import random
import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from keyboards.main import main_menu_keyboard, main_reply_keyboard
from database.postgres_db import (
    is_paid, is_admin, get_last_menus, set_last_menus,
    get_ads_config, should_show_ad, pick_random_ad, log_ad_action,
)
from config import FREE_MODE

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# КЭШИ (в памяти)
# ============================================================
# Кэш последних меню: {user_id: {"chat_id": X, "fact_id": Y, "inline_id": Z}}
_last_menus_cache: dict = {}

# Локи для защиты от двойного нажатия: {user_id: asyncio.Lock}
_user_locks: dict = {}


def _get_lock(user_id: int) -> asyncio.Lock:
    if user_id not in _user_locks:
        _user_locks[user_id] = asyncio.Lock()
    return _user_locks[user_id]


# ============================================================
# ФАКТЫ
# ============================================================
MENU_FACTS = [
    "🔮 Астрология — это язык звёзд. Каждая планета говорит с вами.",
    "✨ Луна меняет знак каждые 2-3 дня. Настроение — тоже.",
    "🌟 Ваш знак зодиака — только начало. Вселенная говорит символами.",
    "💫 Солнце, Луна и планеты — ваши космические спутники.",
    "🌙 Полнолуние — время отпустить старое и впустить новое.",
    "🪐 Сатурн учит терпению. Юпитер дарит удачу.",
    "⭐ Асцендент — ваша визитная карточка для мира.",
    "🌞 Стихии — 4 языка, на которых говорит ваша душа.",
    "🔭 Астрология старше пирамид. Ей больше 4000 лет.",
    "✨ Меркурий управляет общением. В ретроград — будьте внимательны.",
    "💫 Венера — планета любви. Она знает ваши желания.",
    "🌙 Луна — ваш внутренний мир. Слушайте её.",
    "🌟 Марс даёт энергию. Используйте её мудро.",
    "⭐ 12 домов — 12 сфер жизни.",
    "🪐 Плутон — планета трансформации. Перемены — это рост.",
    "🌞 Солнце в карте — ваша суть. Луна — ваши чувства.",
    "💫 Кометы приносят перемены. Следите за знаками.",
    "🔮 Интуиция — ваш личный астролог. Доверяйте ей.",
    "✨ Звёзды не решают за вас. Они лишь показывают путь.",
    "🌙 Новолуние — лучшее время для новых начинаний.",
    "🌟 Юпитер в вашем доме — там ждёт удача.",
    "⭐ Меркурий, Венера, Марс — три ключа к действию.",
    "🪐 Сатурн не наказывает — он учит.",
    "💫 Лунные узлы показывают путь души.",
    "🌞 Стихия Огня — страсть. Земли — стабильность. Воздуха — идеи. Воды — чувства.",
    "🔮 Ретроградный Меркурий — время пересмотреть, а не начинать.",
    "✨ Каждая планета в вашей карте — часть пазла.",
    "🌙 Луна в Раке — время заботы. В Овне — время действий.",
    "🌟 Астрология — не магия. Это язык Вселенной.",
    "⭐ Ваша натальная карта уникальна. Как отпечаток пальца.",
]


def get_menu_fact() -> str:
    return random.choice(MENU_FACTS)


# ============================================================
# УДАЛЕНИЕ МЕНЮ
# ============================================================
async def _delete_previous_menus(bot: Bot, user_id: int):
    """Удаляет предыдущие меню (из кэша или БД)."""
    if not bot:
        return
    try:
        data = _last_menus_cache.get(user_id)
        if not data:
            data = await get_last_menus(user_id) or {}
            _last_menus_cache[user_id] = data

        chat_id = data.get("chat_id")
        if not chat_id:
            return

        for key in ("fact_id", "inline_id"):
            mid = data.get(key)
            if mid:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=mid)
                except Exception as e:
                    logger.debug(f"Не удалить {mid}: {e}")

        # Очищаем кэш (удалённые ID больше не нужны)
        _last_menus_cache[user_id] = {"chat_id": chat_id}
    except Exception as e:
        logger.debug(f"_delete_previous_menus: {e}")


async def _save_menus_bg(user_id: int, chat_id: int, fact_id: int, inline_id: int):
    """Сохраняет ID меню в БД в фоне."""
    try:
        await set_last_menus(user_id, chat_id, fact_id=fact_id, inline_id=inline_id)
    except Exception as e:
        logger.debug(f"_save_menus_bg: {e}")


# ============================================================
# ПОКАЗ ГЛАВНОГО МЕНЮ
# ============================================================
async def _show_main_menu(message: Message, bot: Bot = None):
    """Быстрый показ главного меню."""
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        paid, admin = await asyncio.gather(
            is_paid(user_id),
            is_admin(user_id),
        )
    except Exception:
        paid, admin = False, False

    fact_text = get_menu_fact()

    # Параллельно: факт + inline-меню
    fact_msg = await message.answer(fact_text, reply_markup=main_reply_keyboard())

    if not paid and not admin and not FREE_MODE:
        from keyboards.main import payment_keyboard
        inline_msg = await message.answer(
            "🔒 Подписка не активна.\n\nВыберите тариф:",
            reply_markup=await payment_keyboard(),
        )
    else:
        inline_msg = await message.answer(
            "🏠 Главное меню:",
            reply_markup=main_menu_keyboard(user_id),
        )

    # Сохраняем в кэш (мгновенно)
    _last_menus_cache[user_id] = {
        "chat_id": chat_id,
        "fact_id": fact_msg.message_id,
        "inline_id": inline_msg.message_id,
    }

    # Сохраняем в БД в фоне (не ждём)
    asyncio.create_task(_save_menus_bg(
        user_id, chat_id, fact_msg.message_id, inline_msg.message_id
    ))

    # Показ рекламы
    try:
        await _maybe_show_ad(message, user_id, chat_id)
    except Exception as e:
        logger.warning(f"[AD ERROR] Вызов: {e}")

# ============================================================
# ОБРАБОТЧИКИ С ЗАЩИТОЙ ОТ ДВОЙНОГО НАЖАТИЯ
# ============================================================
@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lock = _get_lock(user_id)

    if lock.locked():
        # Уже обрабатывается — игнорируем
        try:
            await message.delete()
        except Exception:
            pass
        return

    async with lock:
        await state.clear()
        try:
            await message.delete()
        except Exception:
            pass
        await _delete_previous_menus(bot, user_id)
        await _show_main_menu(message, bot)


@router.message(F.text == "🏠 Меню")
async def reply_menu(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lock = _get_lock(user_id)

    # Если уже обрабатывается — удалить сообщение и выйти
    try:
        await message.delete()
    except Exception:
        pass

    if lock.locked():
        return

    async with lock:
        await state.clear()
        await _delete_previous_menus(bot, user_id)
        await _show_main_menu(message, bot)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lock = _get_lock(user_id)

    try:
        await message.delete()
    except Exception:
        pass

    if lock.locked():
        return

    async with lock:
        current_state = await state.get_state()
        if current_state:
            await state.clear()
            await message.answer("✅ Действие отменено.")
        else:
            await message.answer("Нечего отменять.")

        await _delete_previous_menus(bot, user_id)
        await _show_main_menu(message, bot)


# ============================================================
# ХЕЛПЕР для start.py
# ============================================================
async def show_main_menu_from_start(message: Message, bot: Bot = None):
    """Обёртка для /start — с блокировкой."""
    user_id = message.from_user.id
    lock = _get_lock(user_id)
    async with lock:
        await _show_main_menu(message, bot)



# ============================================================
# ПОКАЗ РЕКЛАМЫ
# ============================================================
async def _maybe_show_ad(message: Message, user_id: int, chat_id: int):
    """Показывает рекламу, если нужно."""
    logger.info(f"[AD] Проверка should_show_ad({user_id})")
    try:
        show = await should_show_ad(user_id)
    except Exception as e:
        logger.warning(f"[AD ERROR] should_show_ad: {e}")
        return

    if not show:
        logger.info(f"[AD] should_show_ad вернул False")
        return

    logger.info(f"[AD] Выбор блока")
    try:
        ad = await pick_random_ad()
    except Exception as e:
        logger.warning(f"[AD ERROR] pick_random_ad: {e}")
        return

    if not ad:
        logger.info(f"[AD] Нет активных блоков")
        return

    logger.info(f"[AD] Выбран блок #{ad['id']}")

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📢 РЕКЛАМА\n\n"
        f"{ad['text']}"
    )

    button_text = ad.get("button_text", "Подробнее")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🔥 {button_text}",
            callback_data=f"ad_click_{ad['id']}"
        )],
    ])

    try:
        logger.info(f"[AD] Отправка сообщения...")
        ad_msg = await message.answer(text, reply_markup=keyboard)
        logger.info(f"[AD] ✅ Отправлено msg_id={ad_msg.message_id}")
        await log_ad_action(ad["id"], user_id, "show")
        logger.info(f"[AD] ✅ Показ залогирован")
    except Exception as e:
        logger.warning(f"[AD ERROR] не отправлено: {type(e).__name__}: {e}")
        import traceback
        logger.warning(traceback.format_exc())
