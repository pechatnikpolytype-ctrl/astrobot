from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from services.pdf_generator import pdf_gen
from keyboards.main import pdf_type_keyboard, back_to_menu_keyboard, main_menu_keyboard
from database.postgres_db import get_user, update_birth_data
from ai_service_n1n import ai_service
import logging
import os
import traceback
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "generate_pdf")
async def pdf_menu(callback: CallbackQuery):
    text = (
        "📄 PDF отчёты\n\n"
        "Выберите тип отчёта:\n"
        "• 🔮 Натальная карта — полный разбор\n"
        "• 🌙 Личный гороскоп — прогноз на сегодня"
    )
    try:
        await callback.message.edit_text(text, reply_markup=pdf_type_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=pdf_type_keyboard())


@router.callback_query(F.data == "pdf_natal")
async def pdf_natal(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await get_user(user_id)
    if not user_data or not user_data.get("birth_date"):
        await callback.message.edit_text(
            "❌ Для создания PDF натальной карты нужны данные о рождении.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    msg = await callback.message.edit_text("📄 Создаю PDF натальной карты...")
    try:
        data = {
            "name": user_data.get("first_name", "Пользователь"),
            "birth_date": user_data.get("birth_date", ""),
            "birth_time": user_data.get("birth_time", "12:00"),
            "birth_place": user_data.get("birth_place", "Не указано"),
        }
        pdf_path = pdf_gen.create_natal_chart_pdf(data)
        try:
            await msg.delete()
        except Exception:
            pass
        pdf_file = FSInputFile(pdf_path)
        await callback.message.answer_document(pdf_file, caption="🔮 Ваша натальная карта")
        await callback.message.answer("Выберите действие:", reply_markup=main_menu_keyboard(user_id))
        os.remove(pdf_path)
    except Exception as e:
        logger.error(f"Ошибка при создании PDF: {e}\n{traceback.format_exc()}")
        try:
            await msg.edit_text(f"❌ Ошибка: {str(e)}")
        except Exception:
            await callback.message.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data == "pdf_horoscope")
async def pdf_horoscope(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await get_user(user_id)
    msg = await callback.message.edit_text("🌙 Создаю PDF гороскопа...")
    try:
        user_name = user_data.get("first_name", "Пользователь") if user_data else "Пользователь"
        today = datetime.now().strftime("%d.%m.%Y")
        response = await ai_service.process_question(
            user_id,
            f"Составь краткий гороскоп для {user_name} на сегодня. НЕ УПОМИНАЙ конкретные числа и даты."
        )
        pdf_data = {
            "user_name": user_name,
            "date": today,
            "horoscope": response["message"],
        }
        pdf_path = pdf_gen.create_horoscope_pdf(pdf_data)
        try:
            await msg.delete()
        except Exception:
            pass
        pdf_file = FSInputFile(pdf_path)
        await callback.message.answer_document(pdf_file, caption="🌙 Ваш гороскоп")
        await callback.message.answer("Выберите действие:", reply_markup=main_menu_keyboard(user_id))
        os.remove(pdf_path)
    except Exception as e:
        logger.error(f"Ошибка при создании PDF гороскопа: {e}\n{traceback.format_exc()}")
        try:
            await msg.edit_text(f"❌ Ошибка: {str(e)}")
        except Exception:
            await callback.message.answer(f"❌ Ошибка: {str(e)}")
