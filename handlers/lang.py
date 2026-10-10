"""Обработчик выбора языка."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from locales import t, get_lang_name, SUPPORTED
from database.postgres_db import get_user, update_user_language

logger = logging.getLogger(__name__)
router = Router()


def _lang_keyboard(current: str):
    """Кнопки выбора языка."""
    buttons = []
    for code in SUPPORTED:
        mark = "✅ " if code == current else ""
        buttons.append([InlineKeyboardButton(
            text=f"{mark}{get_lang_name(code)}",
            callback_data=f"lang_set_{code}",
        )])
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="main_menu",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _get_user_lang(user_id: int) -> str:
    try:
        user = await get_user(user_id)
        return (user or {}).get("language") or "ru"
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
        logger.error(f"Ошибка сохранения языка: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)
        return

    text = t("LANG_CHANGED", new_lang, name=get_lang_name(new_lang))
    try:
        await callback.message.edit_text(text, reply_markup=_lang_keyboard(new_lang))
    except Exception:
        await callback.message.answer(text, reply_markup=_lang_keyboard(new_lang))
    await callback.answer()
