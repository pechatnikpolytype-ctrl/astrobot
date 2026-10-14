"""Language selection handler."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from locales import t, get_lang_name, SUPPORTED
from database.postgres_db import get_user, update_user_language, get_user_lang_cached

logger = logging.getLogger(__name__)
router = Router()


def _lang_keyboard(current: str, lang: str = None):
    """Языковая клавиатура с переводом кнопок."""
    if lang is None:
        lang = current
    buttons = []
    for code in SUPPORTED:
        mark = "✅ " if code == current else ""
        buttons.append([InlineKeyboardButton(
            text=f"{mark}{get_lang_name(code)}",
            callback_data=f"lang_set_{code}",
        )])
    buttons.append([InlineKeyboardButton(
        text=t("LANG_BUTTON_BACK", lang) if t("LANG_BUTTON_BACK", lang) != "LANG_BUTTON_BACK" else "🔙 Назад",
        callback_data="main_menu",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _get_user_lang(user_id: int) -> str:
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


@router.callback_query(F.data == "lang_menu")
async def lang_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _get_user_lang(user_id)

    text = t("LANG_TITLE", lang, current=get_lang_name(lang))
    try:
        await callback.message.edit_text(text, reply_markup=_lang_keyboard(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=_lang_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("lang_set_"))
async def lang_set(callback: CallbackQuery):
    user_id = callback.from_user.id
    new_lang = callback.data.replace("lang_set_", "")
    if new_lang not in SUPPORTED:
        await callback.answer("❌", show_alert=True)
        return

    try:
        await update_user_language(user_id, new_lang)
    except Exception as e:
        logger.error(f"save lang error: {e}")
        await callback.answer("❌", show_alert=True)
        return

    text = t("LANG_CHANGED", new_lang, name=get_lang_name(new_lang))
    try:
        await callback.message.edit_text(text, reply_markup=_lang_keyboard(new_lang))
    except Exception:
        await callback.message.answer(text, reply_markup=_lang_keyboard(new_lang))

    # Обновляем reply-клавиатуру через правильную функцию
    try:
        from handlers.menu_commands import show_main_menu_from_callback
        await show_main_menu_from_callback(callback, bot=callback.bot)
    except Exception as e:
        logger.warning(f"refresh menu after lang: {e}")

    await callback.answer()
