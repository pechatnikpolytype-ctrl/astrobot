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
def get_positions(question: str, lang: str = "ru") -> list:
    """Return card positions depending on question and language."""
    from locales import t
    q = question.lower()

    def L(key):
        return t(key, lang)

    if any(w in q for w in ["\u043b\u044e\u0431\u043e\u0432", "\u043e\u0442\u043d\u043e\u0448\u0435\u043d\u0438",
                              "love", "relationship", "liebe", "beziehung",
                              "\u043f\u0430\u0440\u0442\u043d\u0451\u0440", "\u043f\u0430\u0440\u0442\u043d\u0435\u0440",
                              "partner", "\u0434\u0435\u0432\u0443\u0448\u043a", "\u043f\u0430\u0440\u043d",
                              "\u0436\u0435\u043d", "\u043c\u0443\u0436", "\u0431\u0440\u0430\u043a", "\u0441\u0432\u0438\u0434\u0430\u043d",
                              "girl", "boy", "wife", "husband", "marriage", "date",
                              "frau", "mann", "ehe", "verabredung"]):
        return [L("TAROT_POS_LOVE_1").format(block=L("TAROT_LABEL_BLOCK")),
                L("TAROT_POS_LOVE_2").format(help=L("TAROT_LABEL_HELP")),
                L("TAROT_POS_LOVE_3").format(prospect=L("TAROT_LABEL_PROSPECT"))]

    if any(w in q for w in ["\u0440\u0430\u0431\u043e\u0442", "\u043a\u0430\u0440\u044c\u0435\u0440", "\u0434\u0435\u043d\u044c\u0433",
                              "\u0431\u0438\u0437\u043d\u0435\u0441", "\u043f\u0440\u043e\u0435\u043a\u0442", "\u043d\u0430\u0447\u0430\u043b\u044c\u043d\u0438\u043a",
                              "\u043a\u043e\u043b\u043b\u0435\u0433", "\u0437\u0430\u0440\u043f\u043b\u0430\u0442",
                              "work", "career", "money", "business", "project", "boss", "salary",
                              "arbeit", "karriere", "geld", "gesch\u00e4ft", "projekt", "chef", "gehalt"]):
        return [L("TAROT_POS_WORK_1").format(past=L("TAROT_LABEL_PAST")),
                L("TAROT_POS_WORK_2").format(now=L("TAROT_LABEL_NOW")),
                L("TAROT_POS_WORK_3").format(future=L("TAROT_LABEL_FUTURE"))]

    if any(w in q for w in ["\u0437\u0434\u043e\u0440\u043e\u0432", "\u0441\u0430\u043c\u043e\u0447\u0443\u0432\u0441\u0442\u0432",
                              "\u0431\u043e\u043b\u0435\u0437\u043d", "\u044d\u043d\u0435\u0440\u0433",
                              "health", "sick", "energy", "gesundheit", "krank", "energie"]):
        return [L("TAROT_POS_HEALTH_1").format(worries=L("TAROT_LABEL_WORRIES")),
                L("TAROT_POS_HEALTH_2").format(helps=L("TAROT_LABEL_HELPS")),
                L("TAROT_POS_HEALTH_3").format(prospect=L("TAROT_LABEL_PROSPECT"))]

    if any(w in q for w in ["\u0436\u0434\u0451\u0442", "\u0436\u0434\u0435\u0442", "\u0431\u0443\u0434\u0435\u0442",
                              "\u0431\u0443\u0434\u0443\u0449", "\u043f\u0435\u0440\u0441\u043f\u0435\u043a\u0442\u0438\u0432",
                              "\u0441\u043b\u0443\u0447\u0438\u0442", "\u043f\u0440\u043e\u0438\u0437\u043e\u0439\u0434",
                              "\u0432\u043f\u0435\u0440\u0435\u0434\u0438",
                              "await", "future", "will happen", "prospect", "zukunft",
                              "was kommt", "aussicht"]):
        return [L("TAROT_POS_FUTURE_1").format(near=L("TAROT_LABEL_NEAR")),
                L("TAROT_POS_FUTURE_2").format(mid=L("TAROT_LABEL_MID")),
                L("TAROT_POS_FUTURE_3").format(far=L("TAROT_LABEL_FAR"))]

    if any(w in q for w in ["\u0441\u043e\u0432\u0435\u0442", "\u043f\u043e\u0441\u0442\u0443\u043f",
                              "\u0440\u0435\u0448\u0435\u043d", "\u0441\u0442\u043e\u0438\u0442 \u043b\u0438",
                              "\u043a\u0430\u043a \u0431\u044b\u0442\u044c", "\u0447\u0442\u043e \u0434\u0435\u043b\u0430\u0442\u044c",
                              "\u043f\u043e\u043c\u043e\u0433",
                              "advice", "should", "decision", "what to do",
                              "rat", "entscheidung"]):
        return [L("TAROT_POS_ADVICE_1").format(now=L("TAROT_LABEL_NOW")),
                L("TAROT_POS_ADVICE_2").format(advice=L("TAROT_LABEL_ADVICE")),
                L("TAROT_POS_ADVICE_3").format(total=L("TAROT_LABEL_TOTAL"))]

    return [L("TAROT_POS_GENERIC_1").format(past=L("TAROT_LABEL_PAST")),
            L("TAROT_POS_GENERIC_2").format(now=L("TAROT_LABEL_NOW")),
            L("TAROT_POS_GENERIC_3").format(future=L("TAROT_LABEL_FUTURE"))]

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
