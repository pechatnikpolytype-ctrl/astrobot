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
from database.postgres_db import get_user, update_birth_data, get_user_lang_cached
from config import MULTILANG_ENABLED
from locales import t
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

last_chart_cache = {}


async def _lang(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


@router.callback_query(F.data == "natal_chart")
async def natal_chart_menu(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    text = t("NATAL_MENU_TITLE", lang)
    try:
        await callback.message.edit_text(text, reply_markup=natal_options_keyboard(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=natal_options_keyboard(lang))


@router.callback_query(F.data == "natal_input")
async def natal_input_start(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    await state.set_state(NatalChartStates.waiting_name)
    text = t("NATAL_ENTER_NAME", lang)
    try:
        await callback.message.edit_text(text)
    except Exception:
        await callback.message.answer(text)


@router.message(NatalChartStates.waiting_name)
async def natal_name(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("NATAL_CANCELLED", lang), reply_markup=back_to_menu_keyboard(lang))
        return
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(t("NATAL_NAME_SHORT", lang))
        return
    if len(name) > 50:
        await message.answer(t("NATAL_NAME_LONG", lang))
        return
    await state.update_data(name=name)
    await state.set_state(NatalChartStates.waiting_birth_date)
    await message.answer(t("NATAL_ENTER_DATE", lang))


@router.message(NatalChartStates.waiting_birth_date)
async def natal_date(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("NATAL_CANCELLED", lang), reply_markup=back_to_menu_keyboard(lang))
        return
    date_str = message.text.strip()
    valid, _, error = natal_service.validate_date(date_str)
    if not valid:
        await message.answer(f"❌ {error}\n\n/cancel")
        return
    await state.update_data(birth_date=date_str)
    await state.set_state(NatalChartStates.waiting_birth_time)
    await message.answer(t("NATAL_ENTER_TIME", lang))


@router.message(NatalChartStates.waiting_birth_time)
async def natal_time(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("NATAL_CANCELLED", lang), reply_markup=back_to_menu_keyboard(lang))
        return
    time_str = message.text.strip()
    valid, _, error = natal_service.validate_time(time_str)
    if not valid:
        await message.answer(f"❌ {error}\n\n/cancel")
        return
    await state.update_data(birth_time=time_str)
    await state.set_state(NatalChartStates.waiting_birth_place)
    await message.answer(t("NATAL_ENTER_PLACE", lang))


@router.message(NatalChartStates.waiting_birth_place)
async def natal_finish(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("NATAL_CANCELLED", lang), reply_markup=back_to_menu_keyboard(lang))
        return

    place = message.text.strip()
    valid, cleaned, error = natal_service.validate_place(place)
    if not valid:
        await message.answer(f"❌ {error}\n\n/cancel")
        return

    data = await state.get_data()
    data["birth_place"] = cleaned
    await state.clear()

    processing_msg = await message.answer(t("NATAL_CREATING", lang))

    try:
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

        ai_processing = await message.answer(t("NATAL_AI_ANALYZING", lang))
        try:
            ai_text = await natal_service.generate_ai_report(chart_data, lang=lang)
            chart_data["ai_interpretation"] = (ai_text or "")[:1500]
            try:
                from database.postgres_db import increment_ai_usage
                await increment_ai_usage(user_id)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"шибка AI: {e}")
            chart_data["ai_interpretation"] = ""

        try:
            await ai_processing.delete()
        except Exception:
            pass

        # SVG-схема с языком
        image_path = natal_service.generate_svg_chart(chart_data, lang=lang)
        if image_path and os.path.exists(image_path):
            try:
                # Конвертируем SVG в PNG с белым фоном для корректного отображения в Telegram
                import cairosvg
                png_path = image_path.replace(".svg", ".png")
                cairosvg.svg2png(url=image_path, write_to=png_path, output_width=1200, background_color="white")
                photo = FSInputFile(png_path)
                await message.answer_photo(photo, caption=t("NATAL_SCHEME_CAPTION", lang))
                try:
                    os.remove(png_path)
                except Exception:
                    pass
            except Exception as img_err:
                logger.warning(f"SVG: {img_err}")
            finally:
                try:
                    os.remove(image_path)
                except Exception:
                    pass

        # олный отчёт с языком
        full_report = await natal_service.generate_full_report(chart_data, lang=lang)
        if len(full_report) > 4000:
            for i in range(0, len(full_report), 4000):
                await message.answer(full_report[i:i + 4000])
        else:
            await message.answer(full_report)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=t("PDF_DOWNLOAD_BTN", lang),
                callback_data="pdf_natal_from_chart"
            )],
            [InlineKeyboardButton(
                text=t("BTN_BACK_MENU", lang),
                callback_data="main_menu"
            )],
        ])
        await message.answer(t("NATAL_READY", lang), reply_markup=keyboard)

    except Exception as e:
        logger.error(f"шибка создания карты: {e}")
        try:
            await processing_msg.edit_text(f"❌ {e}")
        except Exception:
            await message.answer(f"❌ {e}", reply_markup=back_to_menu_keyboard(lang))


@router.callback_query(F.data == "pdf_natal_from_chart")
async def pdf_natal_from_chart(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    chart_data = last_chart_cache.get(user_id)

    if not chart_data:
        user_data = await get_user(user_id)
        if not user_data or not user_data.get("birth_date"):
            await callback.message.edit_text(
                t("NATAL_NEED_BIRTH", lang),
                reply_markup=back_to_menu_keyboard(lang)
            )
            return
        try:
            chart_data = await natal_service.create_natal_chart(
                user_data.get("first_name", "User"),
                user_data["birth_date"],
                user_data.get("birth_time", "12:00"),
                user_data.get("birth_place", "-"),
            )
            last_chart_cache[user_id] = chart_data
        except Exception as e:
            await callback.message.edit_text(
                f"❌ {e}",
                reply_markup=back_to_menu_keyboard(lang)
            )
            return

    processing_msg = await callback.message.edit_text(t("PDF_CREATING", lang))

    try:
        if "ai_interpretation" not in chart_data or not chart_data["ai_interpretation"]:
            try:
                ai_text = await natal_service.generate_ai_report(chart_data, lang=lang)
                chart_data["ai_interpretation"] = (ai_text or "")[:1500]
                try:
                    from database.postgres_db import increment_ai_usage
                    await increment_ai_usage(user_id)
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"шибка AI при PDF: {e}")
                chart_data["ai_interpretation"] = ""

        pdf_path = pdf_gen.create_natal_chart_pdf(chart_data, lang=lang)

        try:
            await processing_msg.delete()
        except Exception:
            pass

        pdf_file = FSInputFile(pdf_path)
        name = chart_data.get("birth_info", {}).get("name", "User")
        await callback.message.answer_document(
            pdf_file,
            caption=t("PDF_NATAL_CAPTION", lang, name=name)
        )
        await callback.message.answer(
            t("PDF_CHOOSE_ACTION", lang),
            reply_markup=main_menu_keyboard(user_id, lang)
        )

        try:
            os.remove(pdf_path)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"шибка PDF: {e}")
        try:
            await processing_msg.edit_text(
                f"❌ {e}",
                reply_markup=back_to_menu_keyboard(lang)
            )
        except Exception:
            await callback.message.answer(
                f"❌ {e}",
                reply_markup=back_to_menu_keyboard(lang)
            )
