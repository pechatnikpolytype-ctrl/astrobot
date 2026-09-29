import httpx
import logging
import random
import asyncio
import re
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from config import (
    N1N_API_KEY, N1N_BASE_URL, N1N_MODEL, ADMINS
)
from database.postgres_db import (
    get_user, get_user_notes, add_user_note,
    get_ai_answer, save_ai_answer,
)

logger = logging.getLogger(__name__)


class N1NService:
    """AI-сервис на базе n1n.ai (OpenAI-совместимый API)."""

    def __init__(self):
        self.api_key = N1N_API_KEY
        self.base_url = N1N_BASE_URL or "https://api.n1n.ai/v1"
        self.model = N1N_MODEL or "gpt-4o-mini"

        # Модели по приоритету (fallback если основная недоступна)
        self.fallback_models = [
            self.model,
            "gpt-4o-mini",
            "gpt-4o",
        ]

        logger.info(f"🤖 N1N Service инициализирован. Модель: {self.model}")

    # ============================================================
    # ГЛАВНЫЙ МЕТОД
    # ============================================================
    async def process_question(self, user_id: int, question: str,
                                use_cache: bool = True) -> Dict[str, Any]:
        """
        Обрабатывает вопрос пользователя.
        Возвращает: {
            'message': str,
            'from_cache': bool,
            'model': str,
            'facts': List[str],
            'request_key': str,
        }
        """
        try:
            user_data = await get_user(user_id)
            if not user_data:
                user_data = {}

            # 1. Определяем тип вопроса
            qtype = self._detect_question_type(question)

            # 2. Строим ключ кэша
            if qtype == "personal":
                profile_hash = self._get_profile_hash(user_data)
                request_key = f"personal_{self._hash(question)}_{profile_hash}"
            else:
                request_key = f"general_{self._hash(question)}"

            # 3. Проверяем кэш
            if use_cache:
                cached = await get_ai_answer(request_key)
                if cached:
                    logger.info(f"✅ Кэш: {request_key}")
                    return {
                        "message": cached["answer"],
                        "from_cache": True,
                        "model": cached.get("model", self.model),
                        "facts": [],
                        "request_key": request_key,
                    }

            # 4. Строим контекст из профиля (для личных вопросов)
            context = ""
            if qtype == "personal":
                context = await self._build_context(user_id, user_data)

            # 5. Промпт
            system_prompt = self._get_system_prompt(qtype)
            user_prompt = self._build_user_prompt(question, context)

            # 6. Запрос к AI
            answer = await self._query_ai(system_prompt, user_prompt)

            if not answer:
                # AI упал — fallback
                await self._notify_admins_error(question, "AI не ответил")
                fallback = self._get_fallback_answer(question)
                return {
                    "message": fallback,
                    "from_cache": False,
                    "model": "fallback",
                    "facts": [],
                    "request_key": request_key,
                }

            # 7. Очистка ответа
            answer = self._clean_response(answer)

            # 8. Сохраняем в кэш
            await save_ai_answer(
                user_id=user_id,
                request_type="question",
                request_key=request_key,
                question=question,
                answer=answer,
                model=self.model,
            )

            # 9. Извлекаем факты (только для личных)
            facts = []
            if qtype == "personal":
                try:
                    facts = await self.extract_user_facts(question, answer)
                except Exception as e:
                    logger.warning(f"Ошибка извлечения фактов: {e}")

            return {
                "message": answer,
                "from_cache": False,
                "model": self.model,
                "facts": facts,
                "request_key": request_key,
            }

        except Exception as e:
            logger.error(f"❌ Ошибка process_question: {e}")
            await self._notify_admins_error(question, str(e))
            return {
                "message": self._get_fallback_answer(question),
                "from_cache": False,
                "model": "error",
                "facts": [],
                "request_key": "",
            }

    # ============================================================
    # ГОРОСКОП
    # ============================================================
    async def generate_horoscope(self) -> Optional[str]:
        """Генерирует общий гороскоп на день (один для всех)."""
        today = datetime.now().strftime("%d.%m.%Y")

        system_prompt = (
            "Ты — профессиональный астролог. Составь красивый астрологический гороскоп на сегодня.\n"
            "Требования:\n"
            "- НЕ используй markdown (**, __, `)\n"
            "- Используй эмодзи в начале блоков\n"
            "- Разделяй блоки пустой строкой\n"
            "- НЕ упоминай конкретные знаки зодиака (гороскоп общий)\n"
            "- НЕ упоминай числа и точные даты\n"
            "- Тон: дружелюбный, тёплый, поддерживающий\n"
        )

        user_prompt = f"""Составь астрологический гороскоп на {today}.

Структура (соблюдай блоки):

🌅 ОБЩИЙ ПРОГНОЗ
[3-4 предложения об энергетике дня]

💫 ПЛАНЕТАРНЫЕ ВЛИЯНИЯ
[2-3 предложения]

💖 ЛЮБОВЬ И ОТНОШЕНИЯ
[2-3 предложения]

💼 КАРЬЕРА И ФИНАНСЫ
[2-3 предложения]

🌿 ЗДОРОВЬЕ И ЭНЕРГИЯ
[2-3 предложения]

💡 СОВЕТ ДНЯ
[1-2 предложения]

✨ АСТРОЛОГИЧЕСКИЙ ФАКТ
[1 предложение]

Помни: без markdown, с эмодзи."""

        answer = await self._query_ai(system_prompt, user_prompt)
        if not answer:
            return None
        return self._clean_response(answer)

    # ============================================================
    # СОВМЕСТИМОСТЬ
    # ============================================================
    async def generate_compatibility(self, sign1: str, sign2: str) -> Optional[Dict[str, Any]]:
        """Генерирует совместимость пары знаков."""
        system_prompt = (
            "Ты — профессиональный астролог. Проанализируй совместимость двух знаков зодиака.\n"
            "Требования:\n"
            "- НЕ используй markdown\n"
            "- Используй эмодзи\n"
            "- Тон: дружелюбный, поддерживающий\n"
        )

        user_prompt = f"""Проанализируй совместимость: {sign1} и {sign2}.

Верни СТРОГО в таком формате:

SCORE: [число от 0 до 100]
LEVEL: [одно из: Идеальная совместимость / Отличная совместимость / Хорошая совместимость / Средняя совместимость / Сложная совместимость]
TEXT:
💕 АНАЛИЗ СОВМЕСТИМОСТИ

✨ АСТРОЛОГИЧЕСКИЕ ДАННЫЕ:
[стихии, планеты, качества]

🌊 ГАРМОНИЯ СТИХИЙ:
[1-2 предложения]

✅ СИЛЬНЫЕ СТОРОНЫ:
[список]

⚠️ СЛАБЫЕ СТОРОНЫ:
[список]

💫 РЕКОМЕНДАЦИЯ:
[1-2 предложения]

🔮 Помните: астрология — это руководство, а не приговор.

Не пиши ничего кроме указанного формата."""

        answer = await self._query_ai(system_prompt, user_prompt)
        if not answer:
            return None

        # Парсим ответ
        try:
            score = 75
            level = "Хорошая совместимость"
            text = answer

            for line in answer.split("\n"):
                if line.startswith("SCORE:"):
                    try:
                        score = int(re.search(r"\d+", line).group())
                    except Exception:
                        pass
                elif line.startswith("LEVEL:"):
                    level = line.replace("LEVEL:", "").strip()
                elif line.startswith("TEXT:"):
                    text = answer.split("TEXT:", 1)[1].strip()
                    break

            return {
                "score": score,
                "level": level,
                "text": self._clean_response(text),
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга совместимости: {e}")
            return {
                "score": 75,
                "level": "Совместимость",
                "text": self._clean_response(answer),
            }

    # ============================================================
    # НАТАЛЬНАЯ КАРТА
    # ============================================================
    async def generate_natal_interpretation(self, chart_data: Dict[str, Any]) -> Optional[str]:
        """Генерирует AI-интерпретацию натальной карты."""
        info = chart_data.get("birth_info", {})
        planets = chart_data.get("planets", [])

        planets_text = "\n".join([
            f"- {p.get('name', '?')} в {p.get('sign', '?')} ({p.get('house', '?')} дом)"
            for p in planets
        ])

        system_prompt = (
            "Ты — профессиональный астролог. Составь интерпретацию натальной карты.\n"
            "Требования:\n"
            "- 5-7 предложений\n"
            "- На основе РЕАЛЬНЫХ позиций планет (не выдумывай)\n"
            "- Без markdown\n"
            "- Тёплый, поддерживающий тон\n"
            "- Обращайся по имени\n"
        )

        user_prompt = f"""Пользователь: {info.get('name', 'Пользователь')}
Дата: {info.get('date', '?')} в {info.get('time', '?')}
Место: {info.get('place', '?')}
Солнце в {chart_data.get('sun_sign', '?')}
Стихия: {chart_data.get('element', '?')}
Качество: {chart_data.get('quality', '?')}
Асцендент: {chart_data.get('ascendant', '?')}

Планеты:
{planets_text}

Составь персональную интерпретацию натальной карты."""

        answer = await self._query_ai(system_prompt, user_prompt)
        if not answer:
            return None
        return self._clean_response(answer)

    # ============================================================
    # ИЗВЛЕЧЕНИЕ ФАКТОВ
    # ============================================================
    async def extract_user_facts(self, question: str, answer: str) -> List[str]:
        """
        Извлекает факты о пользователе из диалога.
        Возвращает список строк (максимум 3).
        """
        system_prompt = (
            "Ты — анализатор. Извлеки ТОЛЬКО те факты, которые ПОЛЬЗОВАТЕЛЬ утверждал о себе.\n"
            "НЕ включай:\n"
            "- вопросы пользователя\n"
            "- предположения AI\n"
            "- общие фразы\n\n"
            "Формат ответа: JSON-массив строк. Пример: [\"Работает в IT\", \"Любит кофе\"]\n"
            "Если фактов нет — верни [].\n"
            "Максимум 3 факта. Каждый до 100 символов."
        )

        user_prompt = f"""Диалог:
Пользователь: {question}
AI: {answer}

Извлеки факты о пользователе."""

        raw = await self._query_ai(system_prompt, user_prompt, max_tokens=200)
        if not raw:
            return []

        # Ищем JSON-массив в ответе
        try:
            match = re.search(r"\[.*?\]", raw, re.DOTALL)
            if match:
                facts = json.loads(match.group())
                if isinstance(facts, list):
                    return [str(f)[:100] for f in facts[:3]]
        except Exception as e:
            logger.debug(f"Ошибка парсинга фактов: {e}")

        return []

    # ============================================================
    # ВНУТРЕННИЕ
    # ============================================================
    def _detect_question_type(self, question: str) -> str:
        """Определяет тип вопроса: личный или общий."""
        q_lower = question.lower()
        words = re.findall(r"\b\w+\b", q_lower)

        personal_pronouns = {
            "я", "мне", "меня", "мой", "моя", "мои", "моё", "моего", "моей",
            "мной", "мною", "себя", "себе", "собой", "меня", "нам", "нас",
            "наш", "наша", "наши",
        }

        if any(w in personal_pronouns for w in words):
            return "personal"
        return "general"

    def _get_profile_hash(self, user: Dict[str, Any]) -> str:
        """Хеш профиля для ключа кэша."""
        parts = [
            str(user.get("birth_date", "")),
            str(user.get("birth_time", "")),
            str(user.get("birth_place", "")),
            str(user.get("gender", "")),
            str(user.get("bio", "")),
            str(user.get("interests", "")),
            str(user.get("goals", "")),
            str(user.get("relationship_status", "")),
        ]
        return self._hash("|".join(parts))

    def _hash(self, text: str) -> str:
        """MD5-хеш."""
        import hashlib
        return hashlib.md5(text.encode("utf-8")).hexdigest()[:16]

    async def _build_context(self, user_id: int, user: Dict[str, Any]) -> str:
        """Строит контекст из профиля и заметок."""
        parts = []

        if user.get("first_name"):
            parts.append(f"Имя: {user['first_name']}")

        if user.get("birth_date"):
            zodiac = ""
            try:
                from astrology_calculator import AstrologyCalculator
                birth_date = datetime.strptime(user["birth_date"], "%Y-%m-%d")
                zodiac = AstrologyCalculator.get_zodiac_sign(birth_date)
            except Exception:
                pass
            birth_line = f"Дата рождения: {user['birth_date']}"
            if user.get("birth_time"):
                birth_line += f" в {user['birth_time']}"
            if user.get("birth_place"):
                birth_line += f", {user['birth_place']}"
            if zodiac:
                birth_line += f" (знак: {zodiac})"
            parts.append(birth_line)

        if user.get("gender"):
            parts.append(f"Пол: {user['gender']}")
        if user.get("bio"):
            parts.append(f"О себе: {user['bio']}")
        if user.get("interests"):
            parts.append(f"Интересы: {user['interests']}")
        if user.get("goals"):
            parts.append(f"Цели: {user['goals']}")
        if user.get("relationship_status"):
            parts.append(f"Статус отношений: {user['relationship_status']}")

        # Заметки AI
        notes = await get_user_notes(user_id)
        if notes:
            parts.append("Важные факты о пользователе:")
            for n in notes[:10]:
                parts.append(f"  • {n['note']}")

        if not parts:
            return ""

        return "ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ:\n" + "\n".join(parts)

    def _get_system_prompt(self, qtype: str) -> str:
        base = (
            "Ты — профессиональный астролог с 20-летним опытом.\n"
            "Требования:\n"
            "- НЕ используй markdown (**, __, `)\n"
            "- Используй эмодзи для оформления\n"
            "- Тон: тёплый, дружелюбный, поддерживающий\n"
            "- Отвечай на русском\n"
            "- НЕ упоминай конкретные числа месяца\n"
        )
        if qtype == "personal":
            return base + (
                "\nУчитывай ИНФОРМАЦИЮ О ПОЛЬЗОВАТЕЛЕ, которую получишь ниже.\n"
                "Отвечай персонально, обращайся по имени, учитывай цели и интересы.\n"
                "4-6 предложений, но по делу."
            )
        return base + "\nОтвечай информативно, 4-6 предложений."

    def _build_user_prompt(self, question: str, context: str) -> str:
        if context:
            return f"{context}\n\nВопрос пользователя: {question}"
        return f"Вопрос пользователя: {question}"

    async def _query_ai(self, system_prompt: str, user_prompt: str,
                        max_tokens: int = 800) -> Optional[str]:
        """Отправляет запрос к n1n.ai."""
        if not self.api_key:
            logger.error("❌ N1N_API_KEY не установлен")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.8,
            "max_tokens": max_tokens,
        }

        for model_try in self.fallback_models:
            data["model"] = model_try
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=data,
                    )
                    if response.status_code == 200:
                        result = response.json()
                        content = result["choices"][0]["message"]["content"]
                        return content
                    else:
                        logger.warning(f"❌ AI {model_try} {response.status_code}: {response.text[:200]}")
            except httpx.TimeoutException:
                logger.warning(f"⏰ Таймаут {model_try}")
            except Exception as e:
                logger.warning(f"❌ Ошибка {model_try}: {e}")

        return None

    def _clean_response(self, text: str) -> str:
        """Убирает markdown из ответа AI."""
        if not text:
            return text
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **bold**
        text = re.sub(r"__(.+?)__", r"\1", text)       # __italic__
        text = re.sub(r"`(.+?)`", r"\1", text)         # `code`
        text = re.sub(r"\*(.+?)\*", r"\1", text)       # *italic*
        text = re.sub(r"#{1,6}\s*", "", text)          # ## headers
        text = re.sub(r"\n{3,}", "\n\n", text)         # лишние пустые строки
        return text.strip()

    def _get_fallback_answer(self, question: str) -> str:
        """Локальный ответ, если AI недоступен."""
        q_lower = question.lower()

        if any(w in q_lower for w in ["совместимость", "отношения", "любовь"]):
            return (
                "💕 Совместимость — сложная тема.\n\n"
                "Для точного анализа укажите знаки партнёров.\n\n"
                "Попробуйте переформулировать вопрос или попробуйте позже."
            )
        if any(w in q_lower for w in ["карьера", "работа", "деньги"]):
            return (
                "💼 Карьерный вопрос — важный.\n\n"
                "Сейчас AI временно недоступен.\n\n"
                "Попробуйте позже — я обязательно помогу."
            )
        if any(w in q_lower for w in ["здоровье"]):
            return (
                "🌿 О здоровье — важно.\n\n"
                "AI временно недоступен, попробуйте позже."
            )

        fallbacks = [
            "🌟 Сейчас звёзды дают мало сигналов — попробуйте задать вопрос позже.",
            "🔮 AI-астролог временно занят. Попробуйте через пару минут.",
            "✨ Вселенная готовит для вас ответ. Попробуйте ещё раз.",
        ]
        return random.choice(fallbacks)

    async def _notify_admins_error(self, question: str, error: str):
        """Уведомляет админов об ошибке AI."""
        if not ADMINS:
            return
        try:
            from loader import bot
            for admin_id in ADMINS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ AI-ошибка\n\n"
                        f"Вопрос: {question[:100]}\n"
                        f"Ошибка: {error[:200]}"
                    )
                except Exception:
                    pass
        except Exception:
            pass


# Создаём экземпляр
ai_service = N1NService()
