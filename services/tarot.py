"""Логика раскладов Таро."""

import json
import random
import hashlib
import logging
from pathlib import Path
from datetime import date, datetime
from typing import Optional

from database.postgres_db import get_tarot_reading, save_tarot_reading

logger = logging.getLogger(__name__)

# Пути
BASE_DIR = Path(__file__).parent.parent
CARDS_DIR = BASE_DIR / "data" / "tarot_cards"
VALUES_FILE = BASE_DIR / "data" / "tarot_values.json"

# Загружаем базу значений
try:
    with open(VALUES_FILE, "r", encoding="utf-8") as f:
        TAROT_VALUES = json.load(f)
    logger.info(f"✅ Таро: загружено {len(TAROT_VALUES)} карт")
except Exception as e:
    logger.error(f"❌ Ошибка загрузки tarot_values.json: {e}")
    TAROT_VALUES = {}


# ============================================================
# КЛЮЧИ И ВЫБОР КАРТ
# ============================================================
def _make_cache_key(user_id: int, question: str) -> str:
    """Ключ кэша: user_id + вопрос + дата (сброс раз в день)."""
    today = date.today().isoformat()
    raw = f"{user_id}|{question.lower().strip()}|{today}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _make_card_seed(user_id: int, question: str) -> int:
    """Seed для генерации карт. Меняется раз в день."""
    today = date.today().isoformat()
    raw = f"{user_id}|{question.lower().strip()}|{today}"
    return int(hashlib.md5(raw.encode("utf-8")).hexdigest()[:8], 16)


def _draw_cards(seed: int, count: int = 3) -> list:
    """Выбирает count случайных карт по seed."""
    all_keys = list(TAROT_VALUES.keys())
    if not all_keys:
        return []

    rnd = random.Random(seed)
    cards = rnd.sample(all_keys, min(count, len(all_keys)))
    return cards


def _get_card_image_path(card_key: str) -> Optional[Path]:
    """Возвращает путь к картинке карты."""
    card = TAROT_VALUES.get(card_key)
    if not card:
        return None
    img_rel = card.get("image")
    if not img_rel:
        return None
    p = CARDS_DIR / img_rel
    return p if p.exists() else None


def _get_card_data(card_key: str) -> dict:
    """Возвращает данные карты (ru, upright, love, career, advice)."""
    return TAROT_VALUES.get(card_key, {})


# ============================================================
# AI-ТОЛКОВАНИЕ
# ============================================================
async def _generate_ai_reading(user_id: int, question: str, cards: list) -> str:
    """AI-толкование расклада."""
    from ai_service_n1n import ai_service
    from database.postgres_db import get_user

    # Карты для промпта
    cards_info = []
    for i, key in enumerate(cards, 1):
        data = _get_card_data(key)
        cards_info.append(
            f"{i}. {data.get('ru', key)} — {data.get('upright', '')}"
        )
    cards_text = "\n".join(cards_info)

    # Профиль пользователя
    user = await get_user(user_id) or {}
    zodiac = ""
    if user.get("birth_date"):
        try:
            from astrology_calculator import AstrologyCalculator
            bd = datetime.strptime(user["birth_date"], "%Y-%m-%d")
            zodiac = AstrologyCalculator.get_zodiac_sign(bd)
        except Exception:
            pass

    context_parts = []
    if user.get("first_name"):
        context_parts.append(f"Имя: {user['first_name']}")
    if zodiac:
        context_parts.append(f"Знак зодиака: {zodiac}")
    if user.get("bio"):
        context_parts.append(f"О себе: {user['bio']}")
    if user.get("goals"):
        context_parts.append(f"Цели: {user['goals']}")

    # Семейное положение — ВАЖНО
    rel = (user.get("relationship_status") or "").strip()
    if rel:
        context_parts.append(f"Семейное положение: {rel}")
    else:
        context_parts.append("Семейное положение: НЕ УКАЗАНО (не предполагай наличие партнёра)")

    context = "\n".join(context_parts) if context_parts else ""

    system_prompt = (
        "Ты — опытный таролог с 20-летним стажем.\n"
        "Требования:\n"
        "- Отвечай тёпло, поддерживающе\n"
        "- НЕ используй markdown (**, __, `)\n"
        "- Используй эмодзи\n"
        "- 5-7 предложений\n"
        "- Ссылайся на выпавшие карты\n"
        "- НЕ предсказывай точные даты\n"
        "- НЕ давай медицинских/юридических советов\n"
        "- В конце — небольшой совет\n"
        "ВАЖНО:\n"
        "- Учитывай СЕМЕЙНОЕ ПОЛОЖЕНИЕ из контекста\n"
        "- Если у пользователя НЕТ партнёра — НЕ говори про 'партнёра', "
        "говори про 'будущие отношения' или 'потенциального партнёра'\n"
        "- Если партнёр ЕСТЬ — говори про отношения\n"
        "- Если НЕ УКАЗАНО — пиши нейтрально (без предположений)\n"
    )

    context_block = ""
    if context:
        context_block = "Контекст о пользователе:\n" + context

    user_prompt = (
        f"Вопрос пользователя: {question}\n\n"
        f"Выпавшие карты:\n{cards_text}\n\n"
        f"{context_block}\n\n"
        f"Дай развёрнутое толкование расклада для этого вопроса."
    )

    answer = await ai_service._query_ai(system_prompt, user_prompt, max_tokens=800)
    if answer:
        answer = ai_service._clean_response(answer)
        return answer
    return "✨ Карты дают вам важный знак. Прислушайтесь к своей интуиции — ответ уже внутри вас."


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================


# ============================================================
# УМНЫЕ ПОЗИЦИИ ПО ТИПУ ВОПРОСА
# ============================================================
def get_positions(question: str) -> list:
    """Возвращает список позиций карт в зависимости от вопроса."""
    q = question.lower()

    # Любовь / отношения
    if any(w in q for w in ["любов", "отношени", "партнёр", "партнер",
                              "девушк", "парн", "жен", "муж", "брак", "свидан"]):
        return ["💔 Что мешает", "💖 Что поможет", "✨ Перспектива"]

    # Работа / карьера / деньги
    if any(w in q for w in ["работ", "карьер", "деньг", "бизнес",
                              "проект", "начальник", "коллег", "зарплат"]):
        return ["📉 Прошлое", "📊 Настоящее", "🚀 Будущее"]

    # Здоровье
    if any(w in q for w in ["здоров", "самочувств", "болезн", "энерг"]):
        return ["🌿 Что беспокоит", "💊 Что поможет", "✨ Перспектива"]

    # Что ждёт / будущее (общий)
    if any(w in q for w in ["ждёт", "ждет", "будет", "будущ", "перспектив",
                              "случит", "произойд", "впереди"]):
        return ["🕐 Ближайшее", "📅 Среднесрочное", "🔮 Дальнее"]

    # Совет / как поступить
    if any(w in q for w in ["совет", "поступ", "решен", "стоит ли", "как быть",
                              "что делать", "помог"]):
        return ["⚡ Сейчас", "💡 Совет", "🌟 Итог"]

    # По умолчанию
    return ["🕐 Прошлое", "🕐 Настоящее", "🕐 Будущее"]


async def get_or_create_reading(user_id: int, question: str, count: int = 3) -> dict:
    """
    Возвращает расклад для вопроса.
    - Одинаковый вопрос в один день = один и тот же расклад.
    - На следующий день — новый.
    """
    question = question.strip()
    if not question:
        return {"error": "Пустой вопрос"}

    # Ключ кэша
    cache_key = _make_cache_key(user_id, question)

    # Проверяем кэш
    existing = await get_tarot_reading(cache_key)
    if existing:
        import json as _json
        cards_cached = existing["cards"]
        # Если карты пришли как строка — декодируем
        if isinstance(cards_cached, str):
            try:
                cards_cached = _json.loads(cards_cached)
            except Exception:
                cards_cached = []
        return {
            "from_cache": True,
            "cards": cards_cached,
            "ai_answer": existing["ai_answer"],
            "question": question,
        }

    # Генерируем новый расклад
    seed = _make_card_seed(user_id, question)
    cards = _draw_cards(seed, count)
    if not cards:
        return {"error": "Нет карт в базе"}

    # AI-толкование
    ai_answer = await _generate_ai_reading(user_id, question, cards)

    # Сохраняем
    try:
        await save_tarot_reading(user_id, question, cache_key, cards, ai_answer)
    except Exception as e:
        logger.warning(f"Не сохранить расклад: {e}")

    return {
        "from_cache": False,
        "cards": cards,
        "ai_answer": ai_answer,
        "question": question,
    }


# ============================================================
# ХЕЛПЕРЫ ДЛЯ HANDLER
# ============================================================
def get_card_caption(card_key: str) -> str:
    """Краткое описание карты для подписи к фото."""
    data = _get_card_data(card_key)
    if not data:
        return card_key
    return f"🃏 {data.get('ru', card_key)}"


def get_card_full_text(card_key: str, position: str = "") -> str:
    """Полный текст карты для сообщения."""
    data = _get_card_data(card_key)
    if not data:
        return f"🃏 {card_key}"

    text = f"🃏 {data.get('ru', card_key)}"
    if position:
        text = f"{position}: {text}"
    text += f"\n{data.get('upright', '')}"
    return text


def get_card_image(card_key: str) -> Optional[Path]:
    return _get_card_image_path(card_key)


def get_total_cards() -> int:
    return len(TAROT_VALUES)
