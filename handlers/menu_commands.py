"""Menu commands handler with multilang support."""
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
    get_user_lang_cached,
)
from config import FREE_MODE, MULTILANG_ENABLED
from locales import t

logger = logging.getLogger(__name__)
router = Router()


_last_menus_cache: dict = {}
_user_locks: dict = {}


def _get_lock(user_id: int) -> asyncio.Lock:
    if user_id not in _user_locks:
        _user_locks[user_id] = asyncio.Lock()
    return _user_locks[user_id]


async def _lang(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


# 30 facts loaded via t()
MENU_FACT_KEYS = [f"MENU_FACT_{i}" for i in range(1, 31)]


def get_menu_fact(lang: str) -> str:
    key = random.choice(MENU_FACT_KEYS)
    return t(key, lang)


async def _delete_previous_menus(bot: Bot, user_id: int):
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
                    logger.debug(f"delete {mid}: {e}")
        _last_menus_cache[user_id] = {"chat_id": chat_id}
    except Exception as e:
        logger.debug(f"_delete_previous_menus: {e}")


async def _save_menus_bg(user_id: int, chat_id: int, fact_id: int, inline_id: int):
    try:
        await set_last_menus(user_id, chat_id, fact_id=fact_id, inline_id=inline_id)
    except Exception as e:
        logger.debug(f"_save_menus_bg: {e}")


async def _show_main_menu(message: Message, bot: Bot = None):
    user_id = message.from_user.id
    chat_id = message.chat.id
    lang = await _lang(user_id)

    try:
        paid, admin = await asyncio.gather(is_paid(user_id), is_admin(user_id))
    except Exception:
        paid, admin = False, False

    fact_text = get_menu_fact(lang)
    fact_msg = await message.answer(fact_text, reply_markup=main_reply_keyboard(lang))

    if not paid and not admin and not FREE_MODE:
        from keyboards.main import payment_keyboard
        inline_msg = await message.answer(
            t("SUBSCRIPTION_INACTIVE", lang),
            reply_markup=await payment_keyboard(lang),
        )
    else:
        inline_msg = await message.answer(
            t("MENU_TITLE", lang),
            reply_markup=main_menu_keyboard(user_id, lang),
        )

    _last_menus_cache[user_id] = {
        "chat_id": chat_id,
        "fact_id": fact_msg.message_id,
        "inline_id": inline_msg.message_id,
    }

    asyncio.create_task(_save_menus_bg(
        user_id, chat_id, fact_msg.message_id, inline_msg.message_id
    ))

    try:
        await _maybe_show_ad(message, user_id, chat_id)
    except Exception as e:
        logger.warning(f"[AD ERROR] {e}")


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lock = _get_lock(user_id)
    if lock.locked():
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


@router.message(F.text.in_(["🏠 Меню", "🏠 Menu", "🏠 Menü"]))
async def reply_menu(message: Message, state: FSMContext, bot: Bot):
    """Reply кнопка '🏠 Меню' / 'Menu' / 'Menü'."""
    user_id = message.from_user.id
    lock = _get_lock(user_id)

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
    lang = await _lang(user_id)
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
            await message.answer(t("CANCELLED", lang))
        else:
            await message.answer(t("NOTHING_TO_CANCEL", lang))
        await _delete_previous_menus(bot, user_id)
        await _show_main_menu(message, bot)


async def show_main_menu_from_start(message: Message, bot: Bot = None):
    user_id = message.from_user.id
    lock = _get_lock(user_id)
    async with lock:
        await _show_main_menu(message, bot)


async def show_main_menu_from_callback(callback, bot: Bot = None):
    """Показ меню из callback — с ПРАВИЛЬНЫМ user_id."""
    user_id = callback.from_user.id  # callback.from_user, не message.from_user!
    chat_id = callback.message.chat.id
    lock = _get_lock(user_id)
    async with lock:
        # Явно используем callback.from_user.id
        await _show_main_menu_from_ids(user_id, chat_id, callback.message, bot)


async def _show_main_menu_from_ids(user_id: int, chat_id: int, message_ref, bot: Bot = None):
    """Внутренний helper — работает с явными user_id и chat_id."""
    import asyncio as _asyncio
    from config import FREE_MODE
    from keyboards.main import main_menu_keyboard, main_reply_keyboard

    lang = await _lang(user_id)

    try:
        paid, admin = await _asyncio.gather(is_paid(user_id), is_admin(user_id))
    except Exception:
        paid, admin = False, False

    fact_text = get_menu_fact(lang)
    fact_msg = await message_ref.answer(fact_text, reply_markup=main_reply_keyboard(lang))

    if not paid and not admin and not FREE_MODE:
        from keyboards.main import payment_keyboard
        inline_msg = await message_ref.answer(
            t("SUBSCRIPTION_INACTIVE", lang),
            reply_markup=await payment_keyboard(lang),
        )
    else:
        inline_msg = await message_ref.answer(
            t("MENU_TITLE", lang),
            reply_markup=main_menu_keyboard(user_id, lang),
        )

    _last_menus_cache[user_id] = {
        "chat_id": chat_id,
        "fact_id": fact_msg.message_id,
        "inline_id": inline_msg.message_id,
    }

    _asyncio.create_task(_save_menus_bg(
        user_id, chat_id, fact_msg.message_id, inline_msg.message_id
    ))

    try:
        await _maybe_show_ad(message_ref, user_id, chat_id)
    except Exception as e:
        logger.warning(f"[AD ERROR] {e}")


async def _maybe_show_ad(message: Message, user_id: int, chat_id: int):
    logger.info(f"[AD] should_show_ad({user_id})")
    try:
        show = await should_show_ad(user_id)
    except Exception as e:
        logger.warning(f"[AD ERROR] should_show_ad: {e}")
        return
    if not show:
        return
    try:
        ad = await pick_random_ad()
    except Exception as e:
        logger.warning(f"[AD ERROR] pick_random_ad: {e}")
        return
    if not ad:
        return

    divider = "\u2501" * 24
    text = f"{divider}\n\U0001F4E2\n\n{ad['text']}"

    button_text = ad.get("button_text", "Details")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"\U0001F525 {button_text}",
            callback_data=f"ad_click_{ad['id']}"
        )],
    ])

    try:
        ad_msg = await message.answer(text, reply_markup=keyboard)
        await log_ad_action(ad["id"], user_id, "show")
    except Exception as e:
        logger.warning(f"[AD ERROR] {e}")
