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
    is_admin,
)
from keyboards.main import back_to_menu_keyboard
from config import ADMINS
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


@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await get_user(user_id)
    if not user_data:
        await callback.message.edit_text(
            "❌ Профиль не найден. Нажмите /start.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    zodiac = "Не определён"
    if user_data.get("birth_date"):
        try:
            from astrology_calculator import AstrologyCalculator
            birth_date = datetime.strptime(user_data["birth_date"], "%Y-%m-%d")
            zodiac = AstrologyCalculator.get_zodiac_sign(birth_date)
        except Exception:
            pass

    status = "💎 Премиум" if user_data.get("is_paid") else "🆓 Бесплатный"
    limit = await get_user_ai_limit(user_id)
    usage = await get_ai_usage(user_id)
    if limit == -1:
        ai_line = "🔮 Осталось вопросов: ♾️ без лимита"
    else:
        left = max(0, limit - usage)
        ai_line = f"🔮 Осталось вопросов: {usage}/{limit}"

    text = f"""👤 ВАШ ПРОФИЛЬ

🌟 Основное:
  • Имя: {user_data.get('first_name', 'Не указано')}
  • Знак зодиака: {zodiac}
  • Дата рождения: {user_data.get('birth_date', 'Не указано')}
  • Время рождения: {user_data.get('birth_time', 'Не указано')}
  • Место рождения: {user_data.get('birth_place', 'Не указано')}
  • Пол: {user_data.get('gender', 'Не указано')}

📝 О себе:
  • Bio: {user_data.get('bio', 'Не заполнено')}
  • Интересы: {user_data.get('interests', 'Не заполнено')}
  • Цели: {user_data.get('goals', 'Не заполнено')}
  • Отношения: {user_data.get('relationship_status', 'Не указано')}

{ai_line}

⭐ Статус: {status}
📅 Подписка до: {user_data.get('subscription_end', 'Нет активной')}"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="profile_edit")],
        [InlineKeyboardButton(text="🧠 Заметки астролога", callback_data="profile_notes")],
        [InlineKeyboardButton(text="🔗 Пригласи друга", callback_data="profile_referral")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# РЕФЕРАЛЬНАЯ (в профиле)
# ============================================================
@router.callback_query(F.data == "profile_referral")
async def profile_referral(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_referral_settings()

    if not settings.get("enabled", True):
        await callback.message.edit_text(
            "🔗 РЕФЕРАЛЬНАЯ ПРОГРАММА\n\nВременно недоступна.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")],
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
        f"🔗 РЕФЕРАЛЬНАЯ ПРОГРАММА\n\n"
        f"Пригласи друга — оба получите {bonus_days} дня Премиум! 🎁\n\n"
        f"📎 Ваша ссылка:\n"
        f"{ref_link}\n\n"
        f"📊 Статистика:\n"
        f"  • Приглашено: {invited}\n"
        f"  • Бонусов получено: {bonuses}\n"
    )

    if max_bonuses > 0:
        left = max(0, max_bonuses - bonuses)
        text += f"  • Осталось бонусов: {left}/{max_bonuses}\n"

    text += (
        f"\n💡 Как работает:\n"
        f"1. Отправьте ссылку другу\n"
        f"2. Друг регистрируется\n"
        f"3. Оба получаете {bonus_days} дня Премиум\n\n"
        f"⚠️ Бонус — только за новых пользователей."
    )

    share_url = f"https://t.me/share/url?url={ref_link}&text=Попробуй этого астролога!"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться ссылкой", url=share_url)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# РЕДАКТИРОВАНИЕ ПРОФИЛЯ
# ============================================================
@router.callback_query(F.data == "profile_edit")
async def profile_edit_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎂 Дата рождения", callback_data="pe_birth_date")],
        [InlineKeyboardButton(text="⏰ Время рождения", callback_data="pe_birth_time")],
        [InlineKeyboardButton(text="📍 Место рождения", callback_data="pe_birth_place")],
        [InlineKeyboardButton(text="👤 Пол", callback_data="pe_gender")],
        [InlineKeyboardButton(text="📝 Bio", callback_data="pe_bio")],
        [InlineKeyboardButton(text="🎯 Интересы", callback_data="pe_interests")],
        [InlineKeyboardButton(text="🏆 Цели", callback_data="pe_goals")],
        [InlineKeyboardButton(text="💕 Отношения", callback_data="pe_relationship")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")],
    ])
    await callback.message.edit_text("✏️ РЕДАКТИРОВАНИЕ ПРОФИЛЯ", reply_markup=keyboard)


@router.callback_query(F.data == "pe_birth_date")
async def pe_birth_date(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditStates.waiting_birth_date)
    await callback.message.edit_text("🎂 Введите дату рождения:\n\nФорматы: 15.05.1990, 15/05/1990, 1990-05-15\n\n/cancel — отмена")


@router.message(ProfileEditStates.waiting_birth_date)
async def pe_birth_date_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    from utils.date_parser import parse_date
    ok, iso_date, err = parse_date(message.text)
    if not ok:
        await message.answer(f"❌ {err}\n\nПопробуйте снова или /cancel")
        return
    await update_user_field(message.from_user.id, "birth_date", iso_date)
    await state.clear()
    await message.answer(f"✅ Дата обновлена: {iso_date}")


@router.callback_query(F.data == "pe_birth_time")
async def pe_birth_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditStates.waiting_birth_time)
    await callback.message.edit_text("⏰ Введите время (ЧЧ:ММ):\n\n/cancel — отмена")


@router.message(ProfileEditStates.waiting_birth_time)
async def pe_birth_time_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    try:
        datetime.strptime(message.text.strip(), "%H:%M")
    except ValueError:
        await message.answer("❌ Неверный формат")
        return
    await update_user_field(message.from_user.id, "birth_time", message.text.strip())
    await state.clear()
    await message.answer("✅ Время обновлено!")


@router.callback_query(F.data == "pe_birth_place")
async def pe_birth_place(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditStates.waiting_birth_place)
    await callback.message.edit_text("📍 Введите место рождения:\n\n/cancel — отмена")


@router.message(ProfileEditStates.waiting_birth_place)
async def pe_birth_place_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    place = message.text.strip()
    if len(place) < 2:
        await message.answer("❌ Слишком коротко")
        return
    await update_user_field(message.from_user.id, "birth_place", place)
    await state.clear()
    await message.answer("✅ Место обновлено!")


@router.callback_query(F.data == "pe_gender")
async def pe_gender(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Мужской", callback_data="pe_gender_male")],
        [InlineKeyboardButton(text="👩 Женский", callback_data="pe_gender_female")],
        [InlineKeyboardButton(text="🚫 Не указывать", callback_data="pe_gender_none")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile_edit")],
    ])
    await callback.message.edit_text("👤 ВЫБЕРИТЕ ПОЛ", reply_markup=keyboard)


@router.callback_query(F.data.startswith("pe_gender_"))
async def pe_gender_save(callback: CallbackQuery):
    value = callback.data.replace("pe_gender_", "")
    gender_map = {"male": "Мужской", "female": "Женский", "none": None}
    await update_user_field(callback.from_user.id, "gender", gender_map.get(value))
    await callback.answer("✅ Сохранено")
    await profile_handler(callback)


@router.callback_query(F.data == "pe_bio")
async def pe_bio(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditStates.waiting_bio)
    await callback.message.edit_text("📝 Расскажите о себе (2-3 предложения):\n\n/cancel — отмена")


@router.message(ProfileEditStates.waiting_bio)
async def pe_bio_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    bio = message.text.strip()
    if len(bio) > 500:
        await message.answer("❌ Максимум 500 символов")
        return
    await update_user_field(message.from_user.id, "bio", bio)
    await state.clear()
    await message.answer("✅ Bio обновлено!")


@router.callback_query(F.data == "pe_interests")
async def pe_interests(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditStates.waiting_interests)
    await callback.message.edit_text("🎯 Ваши интересы (через запятую):\n\n/cancel — отмена")


@router.message(ProfileEditStates.waiting_interests)
async def pe_interests_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    await update_user_field(message.from_user.id, "interests", message.text.strip())
    await state.clear()
    await message.answer("✅ Интересы обновлены!")


@router.callback_query(F.data == "pe_goals")
async def pe_goals(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditStates.waiting_goals)
    await callback.message.edit_text("🏆 Ваши цели:\n\n/cancel — отмена")


@router.message(ProfileEditStates.waiting_goals)
async def pe_goals_save(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено")
        return
    await update_user_field(message.from_user.id, "goals", message.text.strip())
    await state.clear()
    await message.answer("✅ Цели обновлены!")


@router.callback_query(F.data == "pe_relationship")
async def pe_relationship(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💚 Свободен(а)", callback_data="pe_rel_single")],
        [InlineKeyboardButton(text="💛 В отношениях", callback_data="pe_rel_dating")],
        [InlineKeyboardButton(text="💍 Женат/Замужем", callback_data="pe_rel_married")],
        [InlineKeyboardButton(text="💔 В разводе", callback_data="pe_rel_divorced")],
        [InlineKeyboardButton(text="🚫 Не указывать", callback_data="pe_rel_none")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile_edit")],
    ])
    await callback.message.edit_text("💕 СТАТУС ОТНОШЕНИЙ", reply_markup=keyboard)


@router.callback_query(F.data.startswith("pe_rel_"))
async def pe_relationship_save(callback: CallbackQuery):
    value = callback.data.replace("pe_rel_", "")
    rel_map = {
        "single": "Свободен", "dating": "В отношениях",
        "married": "Женат/Замужем", "divorced": "В разводе", "none": None,
    }
    await update_user_field(callback.from_user.id, "relationship_status", rel_map.get(value))
    await callback.answer("✅ Сохранено")
    await profile_handler(callback)


# ============================================================
# AI-ЗАМЕТКИ
# ============================================================
@router.callback_query(F.data == "profile_notes")
async def profile_notes(callback: CallbackQuery):
    notes = await get_user_notes(callback.from_user.id)
    if not notes:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")],
        ])
        await callback.message.edit_text("🧠 ЗАМЕТКИ АСТРОЛОГА\n\nПока пусто.", reply_markup=keyboard)
        return

    text = "🧠 ЗАМЕТКИ АСТРОЛОГА О ВАС\n\n"
    for i, note in enumerate(notes, 1):
        date = str(note["created_at"])[:10] if note.get("created_at") else "?"
        text += f"{i}. {note['note']} ({date})\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data="notes_delete")],
        [InlineKeyboardButton(text="🧹 Очистить", callback_data="notes_clear")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "notes_delete")
async def notes_delete_menu(callback: CallbackQuery):
    notes = await get_user_notes(callback.from_user.id)
    if not notes:
        await callback.answer("Нет заметок", show_alert=True)
        return
    buttons = []
    for note in notes:
        short = note["note"][:30] + "..." if len(note["note"]) > 30 else note["note"]
        buttons.append([InlineKeyboardButton(
            text=f"🗑️ {short}",
            callback_data=f"note_del_{note['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="profile_notes")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Выберите для удаления:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("note_del_"))
async def note_delete(callback: CallbackQuery):
    note_id = int(callback.data.replace("note_del_", ""))
    await delete_user_note(note_id)
    await callback.answer("✅ Удалено")
    await profile_notes(callback)


@router.callback_query(F.data == "notes_clear")
async def notes_clear_confirm(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="notes_clear_do")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="profile_notes")],
    ])
    await callback.message.edit_text("🧹 Очистить ВСЕ заметки?", reply_markup=keyboard)


@router.callback_query(F.data == "notes_clear_do")
async def notes_clear_do(callback: CallbackQuery):
    await clear_user_notes(callback.from_user.id)
    await callback.answer("✅ Заметки удалены")
    await profile_handler(callback)
