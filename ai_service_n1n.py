import httpx
import logging
import random
import asyncio
import re
import json
import hashlib
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


# Слова, обозначающие время
TIME_WORDS = {
    "сегодня", "завтра", "вчера", "послезавтра",
    "неделя", "неделю", "неделе", "недели", "недель",
    "месяц", "месяца", "месяце", "месяцев",
    "год", "года", "году", "лет",
    "этот", "эта", "это", "эти", "этом", "этой",
    "следующий", "следующая", "следующее", "следующие",
    "прошлый", "прошлая", "прошлое", "прошлые",
    "будущий", "будущая", "будущее", "будущие",
    "сейчас", "скоро", "потом",
    "понедельник", "вторник", "среда", "четверг",
    "пятница", "суббота", "воскресенье",
}


class N1NService:

    def __init__(self):
        self.api_key = N1N_API_KEY
        self.base_url = N1N_BASE_URL or "https://api.n1n.ai/v1"
        self.model = N1N_MODEL or "gpt-4o-mini"
        self.fallback_models = [self.model, "gpt-4o-mini", "gpt-4o"]
        logger.info(f"🤖 N1N Service инициализирован. Модель: {self.model}")

    # ============================================================
    # ГЛАВНЫЙ МЕТОД
    # ============================================================
    async def process_question(self, user_id: int, question: str,
                                use_cache: bool = True) -> Dict[str, Any]:
        try:
            user_data = await get_user(user_id) or {}
            qtype = self._detect_question_type(question)
            is_time_dep = self._is_time_dependent(question)

            request_key = self._build_cache_key(
                question=question,
                qtype=qtype,
                user_data=user_data,
                is_time_dependent=is_time_dep,
            )

            # Кэш
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

            # Контекст
            context = ""
            if qtype == "personal":
                context = await self._build_context(user_id, user_data)

            system_prompt = self._get_system_prompt(qtype)
            user_prompt = self._build_user_prompt(question, context)

            answer = await self._query_ai(system_prompt, user_prompt)

            if not answer:
                await self._notify_admins_error(question, "AI не ответил")
                return {
                    "message": self._get_fallback_answer(question),
                    "from_cache": False,
                    "model": "fallback",
                    "facts": [],
                    "request_key": request_key,
                }

            answer = self._clean_response(answer)

            await save_ai_answer(
                user_id=user_id,
                request_type="question",
                request_key=request_key,
                question=question,
                answer=answer,
                model=self.model,
            )

            # Извлечение фактов — для ВСЕХ личных
            facts = []
            if qtype == "personal":
                try:
                    facts = await self.extract_user_facts(question, answer)
                    logger.info(f"📝 Извлечено фактов: {len(facts)}")
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
    # КЛЮЧ КЭША
    # ============================================================
    def _build_cache_key(self, question: str, qtype: str,
                         user_data: Dict, is_time_dependent: bool) -> str:
        q_hash = self._hash(question)
        today = datetime.now().strftime("%Y-%m-%d")

        if qtype == "personal":
            profile_hash = self._get_profile_hash(user_data)
            if is_time_dependent:
                return f"personal_{q_hash}_{profile_hash}_{today}"
            return f"personal_{q_hash}_{profile_hash}"
        else:
            if is_time_dependent:
                return f"general_{q_hash}_{today}"
            return f"general_{q_hash}"

    def _is_time_dependent(self, question: str) -> bool:
        q_lower = question.lower()
        words = re.findall(r"\b\w+\b", q_lower)
        return any(w in TIME_WORDS for w in words)

    # ============================================================
    # ОПРЕДЕЛЕНИЕ ТИПА ВОПРОСА
    # ============================================================
    def _detect_question_type(self, question: str) -> str:
        """Определяет тип вопроса: личный или общий."""
        q_lower = question.lower()
        words = re.findall(r"\b\w+\b", q_lower)

        personal_pronouns = {
            "я", "мне", "меня", "мой", "моя", "мои", "моё", "моего", "моей",
            "мной", "мною", "себя", "себе", "собой", "нам", "нас", "наш",
            "наша", "наши", "моих", "моему", "моим",
        }
        if any(w in personal_pronouns for w in words):
            return "personal"

        personal_phrases = [
            "люблю", "нравится", "работаю", "живу", "занимаюсь",
            "хочу", "устал", "устала", "боюсь", "мечтаю", "планирую",
            "у меня", "у нас",
        ]
        if any(phrase in q_lower for phrase in personal_phrases):
            return "personal"

        return "general"

    # ============================================================
    # ИЗВЛЕЧЕНИЕ ФАКТОВ
    # ============================================================
    async def extract_user_facts(self, question: str, answer: str) -> List[str]:
        """Извлекает факты о пользователе из диалога."""
        system_prompt = (
            "Ты — анализатор личных фактов. Извлеки факты из СООБЩЕНИЯ пользователя.\n\n"
            "Примеры:\n"
            "• «Я программист» → [\"Работает программистом\"]\n"
            "• «Люблю кофе» → [\"Любит кофе\"]\n"
            "• «Мне 30 лет» → [\"Возраст: 30 лет\"]\n"
            "• «У меня двое детей» → [\"Есть двое детей\"]\n"
            "• «Живу в Москве» → [\"Живёт в Москве\"]\n"
            "• «Занимаюсь спортом» → [\"Занимается спортом\"]\n"
            "• «Хочу найти работу» → [\"Хочет найти работу\"]\n\n"
            "НЕ включай:\n"
            "• вопросы пользователя («Что меня ждёт?»)\n"
            "• предположения AI\n"
            "• общие фразы («интересно», «подскажи»)\n"
            "• эмоции без контекста\n\n"
            "ВАЖНО: если пользователь пишет утверждение о себе — это факт. "
            "Даже если это короткая фраза без вопроса.\n\n"
            "Формат: JSON-массив строк.\n"
            "Пример: [\"Работает в IT\", \"Любит кофе\"]\n"
            "Если фактов НЕТ — верни [].\n"
            "Максимум 3 факта, каждый до 100 символов."
        )

        user_prompt = (
            f"Сообщение пользователя: {question}\n"
            f"Ответ AI: {answer}\n\n"
            f"Извлеки факты о пользователе (только утверждения о СЕБЕ)."
        )

        raw = await self._query_ai(system_prompt, user_prompt, max_tokens=200)
        if not raw:
            return []

        try:
            match = re.search(r"\[.*?\]", raw, re.DOTALL)
            if match:
                facts = json.loads(match.group())
                if isinstance(facts, list):
                    return [str(f)[:100] for f in facts[:3]]
        except Exception as e:
            logger.debug(f"Парсинг фактов: {e}")

        return []

    # ============================================================
    # КОНТЕКСТ ПРОФИЛЯ
    # ============================================================
    async def _build_context(self, user_id: int, user: Dict[str, Any]) -> str:
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
            line = f"Дата рождения: {user['birth_date']}"
            if user.get("birth_time"):
                line += f" в {user['birth_time']}"
            if user.get("birth_place"):
                line += f", {user['birth_place']}"
            if zodiac:
                line += f" (знак: {zodiac})"
            parts.append(line)
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
                "\nУчитывай ИНФОРМАЦИЮ О ПОЛЬЗОВАТЕЛЕ ниже.\n"
                "Отвечай персонально, обращайся по имени, учитывай цели.\n"
                "4-6 предложений, по делу."
            )
        return base + "\nОтвечай информативно, 4-6 предложений."

    def _build_user_prompt(self, question: str, context: str) -> str:
        if context:
            return f"{context}\n\nВопрос пользователя: {question}"
        return f"Вопрос пользователя: {question}"

    # ============================================================
    # ЗАПРОС К AI
    # ============================================================
    async def _query_ai(self, system_prompt: str, user_prompt: str,
                        max_tokens: int = 800) -> Optional[str]:
        if not self.api_key:
            logger.error("❌ N1N_API_KEY не установлен")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for model_try in self.fallback_models:
            data = {
                "model": model_try,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.8,
                "max_tokens": max_tokens,
            }
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=data,
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        logger.warning(f"❌ {model_try} {response.status_code}")
            except httpx.TimeoutException:
                logger.warning(f"⏰ Таймаут {model_try}")
            except Exception as e:
                logger.warning(f"❌ {model_try}: {e}")
        return None

    def _clean_response(self, text: str) -> str:
        if not text:
            return text
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"#{1,6}\s*", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()[:16]

    def _get_profile_hash(self, user: Dict[str, Any]) -> str:
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

    # ============================================================
    # ГОРОСКОП
    # ============================================================
    async def generate_horoscope(self) -> Optional[str]:
        today = datetime.now().strftime("%d.%m.%Y")
        system_prompt = (
            "Ты — профессиональный астролог. Составь красивый астрологический гороскоп на сегодня.\n"
            "Требования:\n"
            "- НЕ используй markdown (**, __, `)\n"
            "- Используй эмодзи в начале блоков\n"
            "- Разделяй блоки пустой строкой\n"
            "- НЕ упоминай конкретные знаки зодиака\n"
            "- НЕ упоминай числа и даты\n"
            "- Тон: дружелюбный, тёплый\n"
        )
        user_prompt = f"""Составь астрологический гороскоп на {today}.

Структура:
🌅 ОБЩИЙ ПРОГНОЗ
[3-4 предложения]

💫 ПЛАНЕТАРНЫЕ ВЛИЯНИЯ
[2-3 предложения]

💖 ЛЮБОВЬ И ОТНОШЕНИЯ
[2-3 предложения]

💼 КАРЬЕРА И ФИНАНСЫ
[2-3 предложения]

🌿 ЗДОРОВЬЕ
[2-3 предложения]

💡 СОВЕТ ДНЯ
[1-2 предложения]

✨ АСТРОЛОГИЧЕСКИЙ ФАКТ
[1 предложение]

Без markdown, с эмодзи."""
        answer = await self._query_ai(system_prompt, user_prompt)
        return self._clean_response(answer) if answer else None

    # ============================================================
    # СОВМЕСТИМОСТЬ
    # ============================================================
    async def generate_compatibility(self, sign1: str, sign2: str) -> Optional[Dict[str, Any]]:
        system_prompt = (
            "Ты — профессиональный астролог. Проанализируй совместимость знаков.\n"
            "Требования:\n"
            "- НЕ используй markdown\n"
            "- Используй эмодзи\n"
            "- Тон: дружелюбный, поддерживающий\n"
        )
        user_prompt = f"""Совместимость: {sign1} и {sign2}.

Верни СТРОГО:

SCORE: [число 0-100]
LEVEL: [Идеальная / Отличная / Хорошая / Средняя / Сложная совместимость]
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

Ничего кроме формата."""
        answer = await self._query_ai(system_prompt, user_prompt)
        if not answer:
            return None
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
            logger.error(f"Парсинг совместимости: {e}")
            return {
                "score": 75,
                "level": "Совместимость",
                "text": self._clean_response(answer),
            }

    # ============================================================
    # НАТАЛЬНАЯ КАРТА
    # ============================================================
    async def generate_natal_interpretation(self, chart_data: Dict[str, Any]) -> Optional[str]:
        info = chart_data.get("birth_info", {})
        planets = chart_data.get("planets", [])
        planets_text = "\n".join([
            f"- {p.get('name', '?')} в {p.get('sign', '?')} ({p.get('house', '?')} дом)"
            for p in planets
        ])
        system_prompt = (
            "Ты — профессиональный астролог. Составь интерпретацию натальной карты.\n"
            "Требования:\n"
            "- 8-10 предложений\n"
            "- На основе РЕАЛЬНЫХ позиций планет\n"
            "- Без markdown\n"
            "- Тёплый, поддерживающий тон\n"
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

Составь персональную интерпретацию."""
        answer = await self._query_ai(system_prompt, user_prompt, max_tokens=1200)
        return self._clean_response(answer) if answer else None

    # ============================================================
    # FALLBACK
    # ============================================================
    def _get_fallback_answer(self, question: str) -> str:
        q_lower = question.lower()
        if any(w in q_lower for w in ["совместимость", "отношения", "любовь"]):
            return "💕 Совместимость — сложная тема. Попробуйте позже."
        if any(w in q_lower for w in ["карьера", "работа", "деньги"]):
            return "💼 Карьерный вопрос важен. AI временно недоступен, попробуйте позже."
        if any(w in q_lower for w in ["здоровье"]):
            return "🌿 О здоровье важно. AI временно недоступен."
        fallbacks = [
            "🌟 Сейчас звёзды дают мало сигналов — попробуйте позже.",
            "🔮 AI-астролог временно занят. Попробуйте через пару минут.",
            "✨ Вселенная готовит ответ. Попробуйте ещё раз.",
        ]
        return random.choice(fallbacks)

    async def _notify_admins_error(self, question: str, error: str):
        if not ADMINS:
            return
        try:
            from loader import bot
            for admin_id in ADMINS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ AI-ошибка\n\nВопрос: {question[:100]}\nОшибка: {error[:200]}"
                    )
                except Exception:
                    pass
        except Exception:
            pass


ai_service = N1NService()
