import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.postgres_db import (
    get_daily_fact_settings, get_today_fact, set_today_fact,
    save_fact_history, get_all_users,
)

logger = logging.getLogger(__name__)


# ============================================================
# FALLBACK ФАКТЫ (20 шт)
# ============================================================
FALLBACK_FACTS = [
    "🔮 Луна меняет знак зодиака каждые 2-3 дня. Лунный гороскоп может сильно отличаться от солнечного.",
    "✨ Меркурий становится ретроградным 3-4 раза в год. В эти периоды не рекомендуют начинать важные дела.",
    "🌟 Знаки зодиака делятся на 4 стихии: Огонь, Земля, Воздух, Вода. Каждая стихия — свой характер.",
    "🌙 В астрологии есть не только 12 знаков, но и 12 домов. Каждый дом отвечает за определённую сферу жизни.",
    "💫 Солнце переходит из знака в знак примерно 20-го числа каждого месяца. Границы знаков немного отличаются от привычных дат.",
    "🌞 Ведическая астрология (Джйотиш) считается одной из древнейших — ей около 5000 лет.",
    "🪐 Сатурн — самая медленная планета, видимая невооружённым глазом. Он находится в одном знаке около 2,5 лет.",
    "🌟 Асцендент часто важнее солнечного знака для описания личности — это знак, восходивший на горизонте в момент рождения.",
    "✨ Точка весеннего равноденствия медленно перемещается. Сейчас она в Рыбах, скоро перейдёт в Водолей — Эра Водолея.",
    "🌙 Луна в астрологии отвечает за эмоции, интуицию и подсознание. Её положение описывает внутренний мир.",
    "💫 Каждая планета управляет определённым знаком. Марс — Овном, Венера — Тельцом и Весами.",
    "🔮 Астрология — не только гороскопы. Это система, изучающая связь небесных тел и событий на Земле.",
    "🌟 В натальной карте учитываются не только планеты, но и астероиды (Хирон, Церера) и лунные узлы.",
    "✨ Ретроградность — оптическая иллюзия. Планета не движется назад, но с Земли кажется так.",
    "🌞 Солнечный знак описывает суть, лунный — эмоции. У многих они разные — это нормально.",
    "🌙 Полнолуние усиливает эмоции и интуицию. Полезно завершать дела и отпускать старое.",
    "💫 Новолуние — время для новых начинаний. Лучший день для старта проектов.",
    "🌟 Плутон — самая дальняя планета в карте. Отвечает за трансформацию и перемены.",
    "🪐 Юпитер называют планетой удачи. Его положение показывает, где сопутствует успех.",
    "✨ Астрология появилась в древнем Вавилоне ~2500 лет назад.",
]


def _build_fact_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Узнать больше", callback_data="ai_question")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])


async def generate_fact() -> str:
    try:
        from ai_service_n1n import ai_service
        system_prompt = (
            "Ты — астролог-просветитель. Придумай ОДИН интересный факт про астрологию.\n"
            "Требования:\n"
            "- 3-4 предложения\n"
            "- БЕЗ markdown (**, __, `)\n"
            "- БЕЗ фразы 'Знаете ли вы'\n"
            "- Эмодзи в начале\n"
            "- Интересный и малоизвестный\n"
        )
        user_prompt = "Придумай интересный факт про астрологию. Без markdown, с эмодзи, 3-4 предложения."
        text = await ai_service._query_ai(system_prompt, user_prompt, max_tokens=400)
        if text:
            text = ai_service._clean_response(text)
            logger.info(f"✅ AI-факт: {len(text)} символов")
            return text
    except Exception as e:
        logger.error(f"Ошибка AI-факта: {e}")

    logger.warning("⚠️ Fallback факт")
    return random.choice(FALLBACK_FACTS)


async def send_daily_facts(bot: Bot):
    settings = await get_daily_fact_settings()
    if not settings.get("enabled", True):
        logger.info("⏸️ Утренние факты отключены")
        return

    # Факт из кэша или новый
    today_fact = await get_today_fact()
    if today_fact and today_fact.get("text"):
        fact_text = today_fact["text"]
        logger.info("✅ Факт из кэша")
    else:
        fact_text = await generate_fact()
        if not fact_text:
            return
        await set_today_fact(fact_text)
        await save_fact_history(fact_text)

    users = await get_all_users()
    if not users:
        logger.info("👥 Нет пользователей")
        return

    logger.info(f"📤 Рассылка фактов: {len(users)} чел.")

    text = (
        f"✨ ИНТЕРЕСНЫЙ ФАКТ ДНЯ\n\n"
        f"{fact_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌙 Хотите узнать больше о своём знаке?"
    )

    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(
                user["user_id"],
                text,
                reply_markup=_build_fact_keyboard()
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            logger.debug(f"Факт не отправлен {user['user_id']}: {e}")

    logger.info(f"✅ Факты: отправлено={sent}, ошибок={failed}")


async def send_test_fact(bot: Bot, user_id: int):
    fact_text = await generate_fact()
    if not fact_text:
        return False
    text = f"🧪 ТЕСТОВЫЙ ФАКТ:\n\n{fact_text}"
    try:
        await bot.send_message(user_id, text, reply_markup=_build_fact_keyboard())
        return True
    except Exception as e:
        logger.error(f"Тестовый факт: {e}")
        return False
