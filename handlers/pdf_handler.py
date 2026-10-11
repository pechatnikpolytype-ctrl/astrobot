from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from services.pdf_generator import pdf_gen
from services.natal_service import natal_service
from keyboards.main import pdf_type_keyboard, back_to_menu_keyboard, main_menu_keyboard
from database.postgres_db import get_user, is_admin, get_user_lang_cached
from config import MULTILANG_ENABLED
from ai_service_n1n import ai_service
from locales import t
import logging
import os
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)
router = Router()


async def _lang(user_id: int) -> str:
    if not MULTILANG_ENABLED:
        return "ru"
    try:
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


@router.callback_query(F.data == "generate_pdf")
async def pdf_menu(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    text = t("PDF_MENU_TITLE", lang)
    try:
        await callback.message.edit_text(text, reply_markup=pdf_type_keyboard(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=pdf_type_keyboard(lang))


@router.callback_query(F.data == "pdf_natal")
async def pdf_natal(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    user_data = await get_user(user_id)

    if not user_data or not user_data.get("birth_date"):
        await callback.message.edit_text(
            t("PDF_NEED_PROFILE", lang),
            reply_markup=back_to_menu_keyboard(lang)
        )
        return

    msg = await callback.message.edit_text(t("PDF_CREATING_NATAL", lang))

    try:
        name = user_data.get("first_name") or "User"
        birth_date = user_data.get("birth_date", "1990-01-01")
        birth_time = user_data.get("birth_time") or "12:00"
        birth_place = user_data.get("birth_place") or "-"

        chart_data = await natal_service.create_natal_chart(
            name, birth_date, birth_time, birth_place
        )

        await msg.edit_text(t("PDF_AI_ANALYZING", lang))
        try:
            ai_text = await natal_service.generate_ai_report(chart_data, lang=lang)
            chart_data["ai_interpretation"] = (ai_text or "")[:1500]
        except Exception as e:
            logger.error(f"шибка AI: {e}")
            chart_data["ai_interpretation"] = ""

        await msg.edit_text(t("PDF_CREATING", lang))
        pdf_path = pdf_gen.create_natal_chart_pdf(chart_data, lang=lang)

        try:
            await msg.delete()
        except Exception:
            pass

        pdf_file = FSInputFile(pdf_path)
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
        logger.error(f"шибка PDF: {e}\n{traceback.format_exc()}")
        try:
            await msg.edit_text(f"❌ {e}", reply_markup=back_to_menu_keyboard(lang))
        except Exception:
            await callback.message.answer(f"❌ {e}", reply_markup=back_to_menu_keyboard(lang))


@router.callback_query(F.data == "pdf_horoscope")
async def pdf_horoscope(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    user_data = await get_user(user_id)
    user_name = "User"
    if user_data:
        user_name = user_data.get("first_name") or "User"

    msg = await callback.message.edit_text(t("PDF_CREATING_HORO", lang))

    try:
        today = datetime.now().strftime("%d.%m.%Y")

        # ромпт на нужном языке
        if lang == "en":
            prompt = (
                f"Write a short personal horoscope for {user_name} for today. "
                f"Do NOT mention exact dates. 5-7 sentences. Answer in English."
            )
        elif lang == "de":
            prompt = (
                f"Schreibe ein kurzes persönliches Horoskop für {user_name} für heute. "
                f"Erwähne keine genauen Daten. 5-7 Sätze. Antworte auf Deutsch."
            )
        else:
            prompt = (
                f"Составь краткий персональный гороскоп для {user_name} на сегодня. "
                f" упоминай конкретные числа и даты. 5-7 предложений."
            )

        response = await ai_service.process_question(user_id, prompt, lang=lang)
        horoscope_text = response.get("message", "-")

        pdf_data = {
            "user_name": user_name,
            "date": today,
            "horoscope": horoscope_text,
        }

        pdf_path = pdf_gen.create_horoscope_pdf(pdf_data, lang=lang)

        try:
            await msg.delete()
        except Exception:
            pass

        pdf_file = FSInputFile(pdf_path)
        await callback.message.answer_document(
            pdf_file,
            caption=t("PDF_HORO_CAPTION", lang, name=user_name)
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
        logger.error(f"шибка PDF гороскопа: {e}\n{traceback.format_exc()}")
        try:
            await msg.edit_text(f"❌ {e}", reply_markup=back_to_menu_keyboard(lang))
        except Exception:
            await callback.message.answer(f"❌ {e}", reply_markup=back_to_menu_keyboard(lang))
