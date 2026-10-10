import logging
import random
import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.main import back_to_menu_keyboard, main_menu_keyboard
from database.postgres_db import is_paid, get_setting, set_setting, is_admin
from config import ADMINS
from astrology_calculator import AstrologyCalculator
from ai_service_n1n import ai_service

logger = logging.getLogger(__name__)
router = Router()


ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]

# Для fallback
ELEMENTS = {
    "Овен": "Огонь", "Лев": "Огонь", "Стрелец": "Огонь",
    "Телец": "Земля", "Дева": "Земля", "Козерог": "Земля",
    "Близнецы": "Воздух", "Весы": "Воздух", "Водолей": "Воздух",
    "Рак": "Вода", "Скорпион": "Вода", "Рыбы": "Вода",
}

RULING_PLANETS = {
    "Овен": "Марс", "Телец": "Венера", "Близнецы": "Меркурий",
    "Рак": "Луна", "Лев": "Солнце", "Дева": "Меркурий",
    "Весы": "Венера", "Скорпион": "Плутон", "Стрелец": "Юпитер",
    "Козерог": "Сатурн", "Водолей": "Уран", "Рыбы": "Нептун",
}

QUALITIES = {
    "Овен": "Кардинальный", "Рак": "Кардинальный",
    "Весы": "Кардинальный", "Козерог": "Кардинальный",
    "Телец": "Фиксированный", "Лев": "Фиксированный",
    "Скорпион": "Фиксированный", "Водолей": "Фиксированный",
    "Близнецы": "Мутабельный", "Дева": "Мутабельный",
    "Стрелец": "Мутабельный", "Рыбы": "Мутабельный",
}

BASE_SCORES = {
    ("Овен", "Лев"): 95, ("Овен", "Стрелец"): 98, ("Овен", "Близнецы"): 75,
    ("Телец", "Дева"): 90, ("Телец", "Козерог"): 95, ("Телец", "Рак"): 70,
    ("Близнецы", "Весы"): 92, ("Близнецы", "Водолей"): 88,
    ("Рак", "Скорпион"): 96, ("Рак", "Рыбы"): 94,
    ("Лев", "Стрелец"): 97, ("Лев", "Овен"): 93,
    ("Дева", "Козерог"): 92, ("Дева", "Телец"): 88,
    ("Весы", "Водолей"): 91, ("Весы", "Близнецы"): 85,
    ("Скорпион", "Рыбы"): 95, ("Скорпион", "Рак"): 92,
    ("Стрелец", "Овен"): 96, ("Стрелец", "Лев"): 94,
    ("Козерог", "Телец"): 90, ("Козерог", "Дева"): 88,
    ("Водолей", "Весы"): 90, ("Водолей", "Близнецы"): 86,
    ("Рыбы", "Рак"): 94, ("Рыбы", "Скорпион"): 92,
}


class CompatibilityStates(StatesGroup):
    waiting_partner1 = State()
    waiting_partner2 = State()


# ============================================================
# ПАРСИНГ ВВОДА
# ============================================================
def parse_input(text: str) -> dict:
    """
    Возвращает: {
        'type': 'sign' | 'date' | None,
        'value': 'Овен' или '1990-05-15',
        'sign': 'Овен' (всегда если можно определить),
    }
    """
    text_clean = text.strip()

    # По названию знака
    for sign in ZODIAC_SIGNS:
        if sign.lower() in text_clean.lower():
            return {"type": "sign", "value": sign, "sign": sign}

    # По дате — используем универсальный парсер
    from utils.date_parser import parse_date
    ok, iso_date, _ = parse_date(text_clean)
    if ok:
        try:
            date_obj = datetime.strptime(iso_date, "%Y-%m-%d")
            sign = AstrologyCalculator.get_zodiac_sign(date_obj)
            return {"type": "date", "value": iso_date, "sign": sign}
        except Exception:
            pass

    return {"type": None, "value": None, "sign": None}


# ============================================================
# КЛЮЧ КЭША
# ============================================================
def build_cache_key(p1: dict, p2: dict) -> str:
    """Строит ключ кэша по введённым данным."""
    if p1["type"] == "date" and p2["type"] == "date":
        # Сортируем даты
        dates = sorted([p1["value"], p2["value"]])
        return f"compat_{dates[0]}_{dates[1]}"
    else:
        # По знакам (сортируем)
        signs = sorted([p1["sign"].lower(), p2["sign"].lower()])
        return f"compat_{signs[0]}_{signs[1]}"


# ============================================================
# FALLBACK (старая логика)
# ============================================================
def fallback_compatibility(sign1: str, sign2: str) -> dict:
    """Локальный расчёт совместимости."""
    key = (sign1, sign2)
    score = BASE_SCORES.get(key, BASE_SCORES.get((sign2, sign1), random.randint(55, 90)))

    if score >= 90:
        level = "Идеальная совместимость"
    elif score >= 80:
        level = "Отличная совместимость"
    elif score >= 70:
        level = "Хорошая совместимость"
    elif score >= 60:
        level = "Средняя совместимость"
    else:
        level = "Сложная совместимость"

    element1 = ELEMENTS.get(sign1, "?")
    element2 = ELEMENTS.get(sign2, "?")
    planet1 = RULING_PLANETS.get(sign1, "?")
    planet2 = RULING_PLANETS.get(sign2, "?")
    quality1 = QUALITIES.get(sign1, "?")
    quality2 = QUALITIES.get(sign2, "?")

    text = (
        f"💕 АНАЛИЗ СОВМЕСТИМОСТИ\n\n"
        f"✨ АСТРОЛОГИЧЕСКИЕ ДАННЫЕ:\n"
        f"• Стихии: {element1} и {element2}\n"
        f"• Планеты: {planet1} и {planet2}\n"
        f"• Качества: {quality1} и {quality2}\n\n"
        f"🌊 ГАРМОНИЯ СТИХИЙ:\n"
        f"Сочетание {element1} и {element2} создаёт уникальную динамику.\n\n"
        f"💫 РЕКОМЕНДАЦИЯ:\n"
        f"Учитесь слушать друг друга. Ваш союз — это сила!\n\n"
        f"🔮 Помните: астрология — это руководство, а не приговор."
    )

    return {"score": score, "level": level, "text": text}


# ============================================================
# ГЛАВНЫЙ ОБРАБОТЧИК
# ============================================================
@router.callback_query(F.data == "compatibility")
async def compatibility_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in ADMINS and not await is_paid(user_id):
        try:
            await callback.message.edit_text(
                "❌ Функция «Совместимость» доступна только по подписке.\n\n"
                "Оформите подписку, чтобы пользоваться.",
                reply_markup=back_to_menu_keyboard()
            )
        except Exception:
            await callback.message.answer(
                "❌ Доступно только по подписке.",
                reply_markup=back_to_menu_keyboard()
            )
        return

    text = (
        "💕 АНАЛИЗ СОВМЕСТИМОСТИ\n\n"
        "Введите знак зодиака первого партнёра:\n"
        "Например: Овен, Телец, Лев\n\n"
        "Или укажите дату рождения в формате ГГГГ-ММ-ДД.\n\n"
        "/cancel — отмена"
    )
    try:
        await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_menu_keyboard())
    await state.set_state(CompatibilityStates.waiting_partner1)


@router.message(CompatibilityStates.waiting_partner1)
async def process_partner1(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено", reply_markup=back_to_menu_keyboard())
        return

    p1 = parse_input(message.text)
    if not p1["sign"]:
        await message.answer(
            "❌ Не удалось определить знак зодиака.\n\n"
            "Напишите название знака (Овен, Телец...) "
            "или дату в формате ГГГГ-ММ-ДД."
        )
        return

    await state.update_data(p1=p1)
    await state.set_state(CompatibilityStates.waiting_partner2)

    await message.answer(
        f"✅ Первый партнёр: {p1['sign']}\n\n"
        f"Теперь введите знак или дату второго партнёра:\n\n"
        f"/cancel — отмена"
    )


@router.message(CompatibilityStates.waiting_partner2)
async def process_partner2(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено", reply_markup=back_to_menu_keyboard())
        return

    p2 = parse_input(message.text)
    if not p2["sign"]:
        await message.answer(
            "❌ Не удалось определить знак. Попробуйте ещё раз."
        )
        return

    data = await state.get_data()
    p1 = data["p1"]
    await state.clear()

    processing_msg = await message.answer("🔮 Астролог анализирует совместимость...")

    # Ключ кэша
    cache_key = build_cache_key(p1, p2)

    # Проверка кэша
    result = None
    from_cache = False

    try:
        cached = await get_setting(cache_key)
        if cached and isinstance(cached, dict) and cached.get("text"):
            result = cached
            from_cache = True
            logger.info(f"✅ Совместимость из кэша: {cache_key}")
    except Exception as e:
        logger.warning(f"Ошибка кэша совместимости: {e}")

    # Запрос к AI
    if not result:
        try:
            ai_result = await ai_service.generate_compatibility(p1["sign"], p2["sign"])
            if ai_result:
                result = ai_result
                await set_setting(cache_key, ai_result)
                logger.info(f"✅ Новая совместимость сохранена: {cache_key}")
        except Exception as e:
            logger.error(f"Ошибка AI-совместимости: {e}")

    # Fallback
    if not result:
        logger.warning("⚠️ Fallback совместимости")
        result = fallback_compatibility(p1["sign"], p2["sign"])

    # Форматируем вывод
    score = result.get("score", 75)
    level = result.get("level", "Совместимость")
    text = result.get("text", "")

    stars = "⭐" * (score // 10) + "☆" * (10 - (score // 10))

    final_text = (
        f"💕 АНАЛИЗ СОВМЕСТИМОСТИ\n\n"
        f"{p1['sign']} 💞 {p2['sign']}\n\n"
        f"{stars}\n"
        f"{score}% — {level}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{text}"
    )

    try:
        await processing_msg.delete()
    except Exception:
        pass

    await message.answer(final_text, reply_markup=main_menu_keyboard(message.from_user.id))
