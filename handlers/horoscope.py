import logging
import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.main import back_to_menu_keyboard
from ai_service_n1n import ai_service
from database.postgres_db import get_daily_horoscope, set_daily_horoscope

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# FALLBACK (если AI упал) — старая база
# ============================================================
FALLBACK_HOROSCOPE = """🌅 АСТРОЛОГИЧЕСКИЙ ПРОГНОЗ НА СЕГОДНЯ

📅 {date}

━━━━━━━━━━━━━━━━━━━━━━━━

🌅 ОБЩИЙ ПРОГНОЗ
Сегодня звёзды выстраиваются в гармоничную конфигурацию, создавая благоприятную энергетику. Это время, когда Вселенная поддерживает ваши начинания и помогает реализовать задуманное.

💫 ПЛАНЕТАРНЫЕ ВЛИЯНИЯ
Меркурий в трине с Юпитером способствует успеху в коммуникациях и обучении. Венера гармонизирует отношения, а Луна усиливает интуицию.

💖 ЛЮБОВЬ И ОТНОШЕНИЯ
Благоприятный день для романтических знакомств и укрепления отношений. Не стесняйтесь говорить о своих чувствах близким.

💼 КАРЬЕРА И ФИНАНСЫ
Удачное время для деловых переговоров, презентаций и важных встреч. Возможны неожиданные денежные поступления.

🌿 ЗДОРОВЬЕ
Луна в огненном знаке придаёт бодрость и энергию. Отличное время для физических нагрузок и активного отдыха.

💡 СОВЕТ ДНЯ
Доверьтесь своей интуиции — она особенно сильна сегодня и подскажет верные решения.

✨ АСТРОЛОГИЧЕСКИЙ ФАКТ
Луна меняет знак каждые 2-3 дня, поэтому лунный гороскоп может сильно отличаться от солнечного.

━━━━━━━━━━━━━━━━━━━━━━━━

🔮 Помните: астрология — это руководство, а не приговор. Звёзды указывают путь, но выбор всегда за вами!"""


# ============================================================
# ГЛАВНЫЙ ОБРАБОТЧИК
# ============================================================
@router.callback_query(F.data == "daily_horoscope")
async def daily_horoscope_handler(callback: CallbackQuery):
    """Гороскоп дня — AI + кэш."""
    today_str = datetime.now().strftime("%d.%m.%Y")

    # Проверяем кэш
    cached = await get_daily_horoscope()
    if cached:
        logger.info("✅ Гороскоп из кэша")
        try:
            await callback.message.edit_text(
                cached, reply_markup=back_to_menu_keyboard()
            )
        except Exception:
            await callback.message.answer(
                cached, reply_markup=back_to_menu_keyboard()
            )
        return

    # Генерируем новый
    processing_msg = None
    try:
        processing_msg = await callback.message.edit_text(
            "🌅 Генерирую гороскоп на сегодня...\n\n"
            "Это займёт 5-15 секунд."
        )
    except Exception:
        processing_msg = await callback.message.answer(
            "🌅 Генерирую гороскоп на сегодня..."
        )

    # Запрос к AI
    try:
        text = await ai_service.generate_horoscope()
    except Exception as e:
        logger.error(f"Ошибка AI-гороскопа: {e}")
        text = None

    if text:
        # Сохраняем в кэш
        await set_daily_horoscope(text)
        logger.info(f"✅ Новый AI-гороскоп сохранён: {len(text)} символов")
    else:
        # Fallback
        logger.warning("⚠️ AI не ответил, используем fallback")
        text = FALLBACK_HOROSCOPE.format(date=today_str)

    # Отправляем
    try:
        await processing_msg.edit_text(text, reply_markup=back_to_menu_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_menu_keyboard())
