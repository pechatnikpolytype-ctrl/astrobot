from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from states import NatalChartStates
from services.natal_service import natal_service
from services.pdf_generator import pdf_gen
from keyboards.main import natal_options_keyboard, main_menu_keyboard, back_to_menu_keyboard
from database.postgres_db import get_user, update_birth_data
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

last_chart_cache = {}


# ============================================================
# МЕНЮ
# ============================================================
@router.callback_query(F.data == "natal_chart")
async def natal_chart_menu(callback: CallbackQuery):
    text = (
        "🔮 СОЗДАНИЕ НАТАЛЬНОЙ КАРТЫ\n\n"
        "Натальная карта — это астрологическая карта рождения.\n"
        "Она показывает положение планет в момент вашего рождения.\n\n"
        "Для создания карты нужны:\n"
        "  • Ваше имя\n"
        "  • Дата рождения\n"
        "  • Время рождения\n"
        "  • Место рождения"
    )
    try:
        await callback.message.edit_text(text, reply_markup=natal_options_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=natal_options_keyboard())


@router.callback_query(F.data == "natal_input")
async def natal_input_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NatalChartStates.waiting_name)
    try:
        await callback.message.edit_text(
            "🌟 ВВЕДИТЕ ВАШЕ ИМЯ\n\nНапример: Александр\n\n/cancel — отмена"
        )
    except Exception:
        await callback.message.answer(
            "🌟 ВВЕДИТЕ ВАШЕ ИМЯ\n\nНапример: Александр\n\n/cancel — отмена"
        )


# ============================================================
# ПОШАГОВЫЙ ВВОД
# ============================================================
@router.message(NatalChartStates.waiting_name)
async def natal_name(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено", reply_markup=back_to_menu_keyboard())
        return
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Введите хотя бы 2 символа.")
        return
    if len(name) > 50:
        await message.answer("❌ Имя слишком длинное (максимум 50 символов).")
        return
    await state.update_data(name=name)
    await state.set_state(NatalChartStates.waiting_birth_date)
    await message.answer(
        "📅 ВВЕДИТЕ ДАТУ РОЖДЕНИЯ\n\n"
        "Форматы:\n"
        "  • 15.05.1990\n"
        "  • 15/05/1990\n"
        "  • 1990-05-15\n\n"
        "/cancel — отмена"
    )


@router.message(NatalChartStates.waiting_birth_date)
async def natal_date(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено", reply_markup=back_to_menu_keyboard())
        return
    date_str = message.text.strip()
    valid, _, error = natal_service.validate_date(date_str)
    if not valid:
        await message.answer(f"❌ {error}\n\nПопробуйте снова или /cancel")
        return
    await state.update_data(birth_date=date_str)
    await state.set_state(NatalChartStates.waiting_birth_time)
    await message.answer(
        "⏰ ВВЕДИТЕ ВРЕМЯ РОЖДЕНИЯ\n\n"
        "Формат: ЧЧ:ММ\n"
        "Например: 14:30\n\n"
        "Если не знаете — напишите 12:00\n"
        "/cancel — отмена"
    )


@router.message(NatalChartStates.waiting_birth_time)
async def natal_time(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено", reply_markup=back_to_menu_keyboard())
        return
    time_str = message.text.strip()
    valid, _, error = natal_service.validate_time(time_str)
    if not valid:
        await message.answer(f"❌ {error}\n\nПопробуйте снова или /cancel")
        return
    await state.update_data(birth_time=time_str)
    await state.set_state(NatalChartStates.waiting_birth_place)
    await message.answer(
        "📍 ВВЕДИТЕ МЕСТО РОЖДЕНИЯ\n\n"
        "Например: Москва, Россия\n\n"
        "/cancel — отмена"
    )


# ============================================================
# СОЗДАНИЕ КАРТЫ
# ============================================================
@router.message(NatalChartStates.waiting_birth_place)
async def natal_finish(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Отменено", reply_markup=back_to_menu_keyboard())
        return

    place = message.text.strip()
    valid, cleaned, error = natal_service.validate_place(place)
    if not valid:
        await message.answer(f"❌ {error}\n\nПопробуйте снова или /cancel")
        return

    data = await state.get_data()
    data["birth_place"] = cleaned
    await state.clear()

    processing_msg = await message.answer(
        "🔮 Создаю натальную карту...\n\n"
        "Это может занять 20-30 секунд."
    )

    try:
        # 1. Создаём карту (VedAstro)
        chart_data = await natal_service.create_natal_chart(
            data["name"], data["birth_date"], data["birth_time"], data["birth_place"]
        )
        user_id = message.from_user.id
        last_chart_cache[user_id] = chart_data

        await update_birth_data(
            user_id, data["birth_date"], data["birth_time"], data["birth_place"]
        )

        try:
            await processing_msg.delete()
        except Exception:
            pass

        # 2. AI-интерпретация (с кэшем)
        ai_processing = await message.answer("🤖 AI анализирует вашу карту...")
        try:
            ai_text = await natal_service.generate_ai_report(chart_data)
            if ai_text:
                # Ограничение на PDF
                chart_data["ai_interpretation"] = ai_text[:1500]
                logger.info(f"✅ AI-интерпретация: {len(ai_text)} символов")
            else:
                chart_data["ai_interpretation"] = ""
                logger.warning("AI не дал интерпретацию")
        except Exception as e:
            logger.error(f"Ошибка AI: {e}")
            chart_data["ai_interpretation"] = ""

        try:
            await ai_processing.delete()
        except Exception:
            pass

        # 3. Отправляем SVG-схему
        image_path = natal_service.generate_svg_chart(chart_data)
        if image_path and os.path.exists(image_path):
            try:
                doc = FSInputFile(image_path)
                await message.answer_document(
                    doc, caption="🔮 Схема натальной карты"
                )
            except Exception as img_err:
                logger.warning(f"Не удалось отправить SVG: {img_err}")
            finally:
                try:
                    os.remove(image_path)
                except Exception:
                    pass

        # 4. Полный отчёт (шаблон + AI)
        full_report = await natal_service.generate_full_report(chart_data)

        # Отправка по частям (лимит Telegram 4096)
        if len(full_report) > 4000:
            for i in range(0, len(full_report), 4000):
                await message.answer(full_report[i:i + 4000])
        else:
            await message.answer(full_report)

        # 5. Кнопки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Скачать PDF-отчёт", callback_data="pdf_natal_from_chart")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ])
        await message.answer("✨ Натальная карта готова!", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка создания карты: {e}")
        try:
            await processing_msg.edit_text(f"❌ Ошибка: {str(e)}")
        except Exception:
            await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=back_to_menu_keyboard())


# ============================================================
# PDF ИЗ КЭША
# ============================================================
@router.callback_query(F.data == "pdf_natal_from_chart")
async def pdf_natal_from_chart(callback: CallbackQuery):
    user_id = callback.from_user.id
    chart_data = last_chart_cache.get(user_id)

    if not chart_data:
        user_data = await get_user(user_id)
        if not user_data or not user_data.get("birth_date"):
            await callback.message.edit_text(
                "❌ Нужны данные о рождении. Сначала создайте натальную карту.",
                reply_markup=back_to_menu_keyboard()
            )
            return
        try:
            chart_data = await natal_service.create_natal_chart(
                user_data.get("first_name", "Пользователь"),
                user_data["birth_date"],
                user_data.get("birth_time", "12:00"),
                user_data.get("birth_place", "Не указано"),
            )
            last_chart_cache[user_id] = chart_data
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=back_to_menu_keyboard()
            )
            return

    processing_msg = await callback.message.edit_text("📄 Создаю PDF...")

    try:
        # AI-интерпретация (если ещё нет)
        if "ai_interpretation" not in chart_data or not chart_data["ai_interpretation"]:
            try:
                ai_text = await natal_service.generate_ai_report(chart_data)
                chart_data["ai_interpretation"] = (ai_text or "")[:1500]
            except Exception as e:
                logger.error(f"Ошибка AI при PDF: {e}")
                chart_data["ai_interpretation"] = ""

        # Создаём PDF
        pdf_path = pdf_gen.create_natal_chart_pdf(chart_data)

        try:
            await processing_msg.delete()
        except Exception:
            pass

        pdf_file = FSInputFile(pdf_path)
        name = chart_data.get("birth_info", {}).get("name", "Пользователь")
        await callback.message.answer_document(
            pdf_file,
            caption=f"🔮 Натальная карта: {name}"
        )
        await callback.message.answer(
            "📌 Выберите действие:",
            reply_markup=main_menu_keyboard(user_id)
        )

        try:
            os.remove(pdf_path)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Ошибка PDF: {e}")
        try:
            await processing_msg.edit_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=back_to_menu_keyboard()
            )
        except Exception:
            await callback.message.answer(
                f"❌ Ошибка: {str(e)}",
                reply_markup=back_to_menu_keyboard()
            )
