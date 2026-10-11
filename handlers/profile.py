"""Profile handler with multilang support."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.postgres_db import (
    get_user, update_user_field, update_birth_data,
    get_user_notes, delete_user_note, clear_user_notes,
    get_user_ai_limit, get_ai_usage,
    get_referral_settings, count_user_referrals,
    count_user_referrals_with_bonus,
    is_admin, get_user_lang_cached,
)
from keyboards.main import back_to_menu_keyboard
from config import ADMINS, MULTILANG_ENABLED
from astrology_calculator import sign_display
from locales import t
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = Router()


class ProfileEditStates(StatesGroup):
    waiting_birth_date = State()
    waiting_birth_time = State()
    waiting_birth_place = State()
    waiting_gender = State()
    waiting_bio = State()
    waiting_interests = State()
    waiting_goals = State()
    waiting_relationship = State()


async def _lang(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    user_data = await get_user(user_id)
    if not user_data:
        await callback.message.edit_text(
            t("PROFILE_NOT_FOUND", lang),
            reply_markup=back_to_menu_keyboard(lang)
        )
        return

    zodiac = t("PROFILE_EMPTY", lang)
    if user_data.get("birth_date"):
        try:
            from astrology_calculator import AstrologyCalculator
            birth_date = datetime.strptime(user_data["birth_date"], "%Y-%m-%d")
            zodiac_ru = AstrologyCalculator.get_zodiac_sign(birth_date)
            zodiac = sign_display(zodiac_ru, lang)
        except Exception:
            pass

    status = t("PROFILE_STATUS_PREMIUM", lang) if user_data.get("is_paid") else t("PROFILE_STATUS_FREE", lang)
    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)
    if limit == -1:
        ai_line = t("PROFILE_AI_UNLIMITED", lang)
    else:
        ai_line = t("PROFILE_AI_LIMITED", lang, usage=usage, limit=limit)

    empty = t("PROFILE_EMPTY", lang)
    empty_bio = t("PROFILE_EMPTY_BIO", lang)
    text = (
        f"{t('PROFILE_TITLE', lang)}\n\n"
        f"{t('PROFILE_SECTION_MAIN', lang)}:\n"
        f"  \u2022 {t('PROFILE_LABEL_NAME', lang)}: {user_data.get('first_name', empty)}\n"
        f"  \u2022 {t('PROFILE_LABEL_ZODIAC', lang)}: {zodiac}\n"
        f"  \u2022 {t('PROFILE_LABEL_BIRTH_DATE', lang)}: {user_data.get('birth_date', empty)}\n"
        f"  \u2022 {t('PROFILE_LABEL_BIRTH_TIME', lang)}: {user_data.get('birth_time', empty)}\n"
        f"  \u2022 {t('PROFILE_LABEL_BIRTH_PLACE', lang)}: {user_data.get('birth_place', empty)}\n"
        f"  \u2022 {t('PROFILE_LABEL_GENDER', lang)}: {user_data.get('gender', empty)}\n\n"
        f"{t('PROFILE_SECTION_ABOUT', lang)}:\n"
        f"  \u2022 Bio: {user_data.get('bio', empty_bio)}\n"
        f"  \u2022 {t('PROFILE_LABEL_INTERESTS', lang)}: {user_data.get('interests', empty_bio)}\n"
        f"  \u2022 {t('PROFILE_LABEL_GOALS', lang)}: {user_data.get('goals', empty_bio)}\n"
        f"  \u2022 {t('PROFILE_LABEL_RELATIONSHIP', lang)}: {user_data.get('relationship_status', empty)}\n\n"
        f"{ai_line}\n\n"
        f"\u2b50 {t('PROFILE_LABEL_STATUS', lang)}: {status}\n"
        f"\U0001F4C5 {t('PROFILE_LABEL_SUB_END', lang)}: {user_data.get('subscription_end', t('PROFILE_NO_SUB', lang))}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("PROFILE_BTN_EDIT", lang), callback_data="profile_edit")],
        [InlineKeyboardButton(text=t("PROFILE_BTN_NOTES", lang), callback_data="profile_notes")],
        [InlineKeyboardButton(text=t("PROFILE_BTN_REFERRAL", lang), callback_data="profile_referral")],
        [InlineKeyboardButton(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# REFERRAL
# ============================================================
@router.callback_query(F.data == "profile_referral")
async def profile_referral(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    settings = await get_referral_settings()

    if not settings.get("enabled", True):
        await callback.message.edit_text(
            t("PROFILE_REF_DISABLED", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("PROFILE_REF_BACK", lang), callback_data="profile")],
            ])
        )
        return

    bot_username = "alles_astro_bot"
    try:
        from loader import bot
        bot_info = await bot.get_me()
        bot_username = bot_info.username
    except Exception:
        pass

    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    invited = await count_user_referrals(user_id)
    bonuses = await count_user_referrals_with_bonus(user_id)
    max_bonuses = settings.get("max_bonuses", 10)
    bonus_days = settings.get("bonus_days", 3)

    text = (
        f"{t('PROFILE_REF_TITLE', lang)}\n\n"
        f"{t('PROFILE_REF_INVITE', lang, days=bonus_days)}\n\n"
        f"{t('PROFILE_REF_YOUR_LINK', lang)}\n{ref_link}\n\n"
        f"{t('PROFILE_REF_STATS', lang)}\n"
        f"  \u2022 {t('PROFILE_REF_INVITED', lang)}: {invited}\n"
        f"  \u2022 {t('PROFILE_REF_BONUSES', lang)}: {bonuses}\n"
    )
    if max_bonuses > 0:
        left = max(0, max_bonuses - bonuses)
        text += f"  \u2022 {t('PROFILE_REF_LEFT', lang)}: {left}/{max_bonuses}\n"

    text += "\n" + t("PROFILE_REF_HOW", lang, days=bonus_days)

    share_url = f"https://t.me/share/url?url={ref_link}&text={t('PROFILE_REF_SHARE_TEXT', lang)}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("PROFILE_REF_SHARE", lang), url=share_url)],
        [InlineKeyboardButton(text=t("PROFILE_REF_BACK", lang), callback_data="profile")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# PROFILE EDIT
# ============================================================
@router.callback_query(F.data == "profile_edit")
async def profile_edit_menu(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("PROFILE_EDIT_BTN_DATE", lang), callback_data="pe_birth_date")],
        [InlineKeyboardButton(text=t("PROFILE_EDIT_BTN_TIME", lang), callback_data="pe_birth_time")],
        [InlineKeyboardButton(text=t("PROFILE_EDIT_BTN_PLACE", lang), callback_data="pe_birth_place")],
        [InlineKeyboardButton(text=t("PROFILE_EDIT_BTN_GENDER", lang), callback_data="pe_gender")],
        [InlineKeyboardButton(text=t("PROFILE_EDIT_BTN_BIO", lang), callback_data="pe_bio")],
        [InlineKeyboardButton(text=t("PROFILE_EDIT_BTN_INTERESTS", lang), callback_data="pe_interests")],
        [InlineKeyboardButton(text=t("PROFILE_EDIT_BTN_GOALS", lang), callback_data="pe_goals")],
        [InlineKeyboardButton(text=t("PROFILE_EDIT_BTN_RELATIONSHIP", lang), callback_data="pe_relationship")],
        [InlineKeyboardButton(text=t("PROFILE_REF_BACK", lang), callback_data="profile")],
    ])
    await callback.message.edit_text(t("PROFILE_EDIT_TITLE", lang), reply_markup=keyboard)


@router.callback_query(F.data == "pe_birth_date")
async def pe_birth_date(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    await state.set_state(ProfileEditStates.waiting_birth_date)
    await callback.message.edit_text(t("PROFILE_ENTER_DATE", lang))


@router.message(ProfileEditStates.waiting_birth_date)
async def pe_birth_date_save(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("PROFILE_CANCELLED", lang))
        return
    from utils.date_parser import parse_date
    ok, iso_date, err = parse_date(message.text)
    if not ok:
        await message.answer(f"\u274c {err}\n\n/cancel")
        return
    await update_user_field(message.from_user.id, "birth_date", iso_date)
    await state.clear()
    await message.answer(t("PROFILE_SAVED_DATE", lang, date=iso_date))


@router.callback_query(F.data == "pe_birth_time")
async def pe_birth_time(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    await state.set_state(ProfileEditStates.waiting_birth_time)
    await callback.message.edit_text(t("PROFILE_ENTER_TIME", lang))


@router.message(ProfileEditStates.waiting_birth_time)
async def pe_birth_time_save(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("PROFILE_CANCELLED", lang))
        return
    try:
        datetime.strptime(message.text.strip(), "%H:%M")
    except ValueError:
        await message.answer(t("PROFILE_ERR_FORMAT", lang))
        return
    await update_user_field(message.from_user.id, "birth_time", message.text.strip())
    await state.clear()
    await message.answer(t("PROFILE_SAVED_TIME", lang))


@router.callback_query(F.data == "pe_birth_place")
async def pe_birth_place(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    await state.set_state(ProfileEditStates.waiting_birth_place)
    await callback.message.edit_text(t("PROFILE_ENTER_PLACE", lang))


@router.message(ProfileEditStates.waiting_birth_place)
async def pe_birth_place_save(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("PROFILE_CANCELLED", lang))
        return
    place = message.text.strip()
    if len(place) < 2:
        await message.answer(t("PROFILE_ERR_TOO_SHORT", lang))
        return
    await update_user_field(message.from_user.id, "birth_place", place)
    await state.clear()
    await message.answer(t("PROFILE_SAVED_PLACE", lang))


@router.callback_query(F.data == "pe_gender")
async def pe_gender(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("PROFILE_GENDER_MALE", lang), callback_data="pe_gender_male")],
        [InlineKeyboardButton(text=t("PROFILE_GENDER_FEMALE", lang), callback_data="pe_gender_female")],
        [InlineKeyboardButton(text=t("PROFILE_GENDER_NONE", lang), callback_data="pe_gender_none")],
        [InlineKeyboardButton(text=t("PROFILE_REF_BACK", lang), callback_data="profile_edit")],
    ])
    await callback.message.edit_text(t("PROFILE_GENDER_TITLE", lang), reply_markup=keyboard)


@router.callback_query(F.data.startswith("pe_gender_"))
async def pe_gender_save(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    value = callback.data.replace("pe_gender_", "")
    gender_map = {"male": "male", "female": "female", "none": None}
    await update_user_field(callback.from_user.id, "gender", gender_map.get(value))
    await callback.answer(t("PROFILE_SAVED", lang))
    await profile_handler(callback)


@router.callback_query(F.data == "pe_bio")
async def pe_bio(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    await state.set_state(ProfileEditStates.waiting_bio)
    await callback.message.edit_text(t("PROFILE_ENTER_BIO", lang))


@router.message(ProfileEditStates.waiting_bio)
async def pe_bio_save(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("PROFILE_CANCELLED", lang))
        return
    bio = message.text.strip()
    if len(bio) > 500:
        await message.answer(t("PROFILE_ERR_MAX_500", lang))
        return
    await update_user_field(message.from_user.id, "bio", bio)
    await state.clear()
    await message.answer(t("PROFILE_SAVED_BIO", lang))


@router.callback_query(F.data == "pe_interests")
async def pe_interests(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    await state.set_state(ProfileEditStates.waiting_interests)
    await callback.message.edit_text(t("PROFILE_ENTER_INTERESTS", lang))


@router.message(ProfileEditStates.waiting_interests)
async def pe_interests_save(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("PROFILE_CANCELLED", lang))
        return
    await update_user_field(message.from_user.id, "interests", message.text.strip())
    await state.clear()
    await message.answer(t("PROFILE_SAVED_INTERESTS", lang))


@router.callback_query(F.data == "pe_goals")
async def pe_goals(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    await state.set_state(ProfileEditStates.waiting_goals)
    await callback.message.edit_text(t("PROFILE_ENTER_GOALS", lang))


@router.message(ProfileEditStates.waiting_goals)
async def pe_goals_save(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("PROFILE_CANCELLED", lang))
        return
    await update_user_field(message.from_user.id, "goals", message.text.strip())
    await state.clear()
    await message.answer(t("PROFILE_SAVED_GOALS", lang))


@router.callback_query(F.data == "pe_relationship")
async def pe_relationship(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("PROFILE_REL_SINGLE", lang), callback_data="pe_rel_single")],
        [InlineKeyboardButton(text=t("PROFILE_REL_DATING", lang), callback_data="pe_rel_dating")],
        [InlineKeyboardButton(text=t("PROFILE_REL_MARRIED", lang), callback_data="pe_rel_married")],
        [InlineKeyboardButton(text=t("PROFILE_REL_DIVORCED", lang), callback_data="pe_rel_divorced")],
        [InlineKeyboardButton(text=t("PROFILE_REL_NONE", lang), callback_data="pe_rel_none")],
        [InlineKeyboardButton(text=t("PROFILE_REF_BACK", lang), callback_data="profile_edit")],
    ])
    await callback.message.edit_text(t("PROFILE_REL_TITLE", lang), reply_markup=keyboard)


@router.callback_query(F.data.startswith("pe_rel_"))
async def pe_relationship_save(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    value = callback.data.replace("pe_rel_", "")
    rel_map = {
        "single": "single", "dating": "dating",
        "married": "married", "divorced": "divorced", "none": None,
    }
    await update_user_field(callback.from_user.id, "relationship_status", rel_map.get(value))
    await callback.answer(t("PROFILE_SAVED", lang))
    await profile_handler(callback)


# ============================================================
# AI NOTES
# ============================================================
@router.callback_query(F.data == "profile_notes")
async def profile_notes(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    notes = await get_user_notes(callback.from_user.id)
    if not notes:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("PROFILE_REF_BACK", lang), callback_data="profile")],
        ])
        await callback.message.edit_text(t("PROFILE_NOTES_EMPTY", lang), reply_markup=keyboard)
        return

    text = t("PROFILE_NOTES_ABOUT", lang) + "\n\n"
    for i, note in enumerate(notes, 1):
        date = str(note["created_at"])[:10] if note.get("created_at") else "?"
        text += f"{i}. {note['note']} ({date})\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("PROFILE_NOTES_BTN_DELETE", lang), callback_data="notes_delete")],
        [InlineKeyboardButton(text=t("PROFILE_NOTES_BTN_CLEAR", lang), callback_data="notes_clear")],
        [InlineKeyboardButton(text=t("PROFILE_REF_BACK", lang), callback_data="profile")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "notes_delete")
async def notes_delete_menu(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    notes = await get_user_notes(callback.from_user.id)
    if not notes:
        await callback.answer(t("PROFILE_NOTES_NO", lang), show_alert=True)
        return
    buttons = []
    for note in notes:
        short = note["note"][:30] + "..." if len(note["note"]) > 30 else note["note"]
        buttons.append([InlineKeyboardButton(
            text=f"\U0001F5D1\ufe0f {short}",
            callback_data=f"note_del_{note['id']}"
        )])
    buttons.append([InlineKeyboardButton(text=t("PROFILE_REF_BACK", lang), callback_data="profile_notes")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(t("PROFILE_NOTES_CHOOSE", lang), reply_markup=keyboard)


@router.callback_query(F.data.startswith("note_del_"))
async def note_delete(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    note_id = int(callback.data.replace("note_del_", ""))
    await delete_user_note(note_id)
    await callback.answer(t("PROFILE_NOTES_DELETED", lang))
    await profile_notes(callback)


@router.callback_query(F.data == "notes_clear")
async def notes_clear_confirm(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("PROFILE_NOTES_YES", lang), callback_data="notes_clear_do")],
        [InlineKeyboardButton(text=t("PROFILE_NOTES_NO_BTN", lang), callback_data="profile_notes")],
    ])
    await callback.message.edit_text(t("PROFILE_NOTES_CLEAR_CONFIRM", lang), reply_markup=keyboard)


@router.callback_query(F.data == "notes_clear_do")
async def notes_clear_do(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    await clear_user_notes(callback.from_user.id)
    await callback.answer(t("PROFILE_NOTES_CLEARED", lang))
    await profile_handler(callback)
