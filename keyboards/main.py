from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from database.postgres_db import get_pricing
from locales import t


async def welcome_keyboard(lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    kb.button(text=t("BTN_CONTINUE", lang), callback_data="check_status")
    return kb.as_markup()


async def payment_keyboard(lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    pricing = await get_pricing()
    for plan, info in pricing.items():
        kb.button(
            text=t("PAY_BUTTON", lang, days=info["days"], stars=info["stars"]),
            callback_data=f"pay_{plan}",
        )
    kb.adjust(1)
    return kb.as_markup()


def main_menu_keyboard(user_id, lang: str = "ru"):
    """Главное меню. Порядок: AI-фичи → PDF → Профиль → Язык → Админ."""
    kb = InlineKeyboardBuilder()
    # --- AI / астро-фичи ---
    kb.button(text=t("BTN_NATAL", lang), callback_data="natal_chart")
    kb.button(text=t("BTN_AI", lang), callback_data="ai_question")
    kb.button(text=t("BTN_HOROSCOPE", lang), callback_data="daily_horoscope")
    kb.button(text=t("BTN_COMPAT", lang), callback_data="compatibility")
    kb.button(text=t("BTN_TAROT", lang), callback_data="tarot_menu")
    kb.button(text=t("BTN_DREAMS", lang), callback_data="dreams_menu")
    kb.button(text=t("BTN_DIARY", lang), callback_data="mood_diary")
    # --- PDF ---
    kb.button(text=t("BTN_PDF", lang), callback_data="generate_pdf")
    # --- Профиль / Язык ---
    kb.button(text=t("BTN_PROFILE", lang), callback_data="profile")
    kb.button(text=t("BTN_LANG", lang), callback_data="lang_menu")
    kb.button(text="⭐ Подписка", callback_data="subscription_info")

    # --- Админ ---
    from config import ADMINS
    if user_id in ADMINS:
        kb.button(text=t("BTN_ADMIN", lang), callback_data="admin_panel")
    kb.button(text='👤 Поддержка', url='https://t.me/Grandmother_admin')
    kb.adjust(2)
    return kb.as_markup()


def natal_options_keyboard(lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 " + ("Ввести данные" if lang == "ru" else
                            "Enter data" if lang == "en" else
                            "Daten eingeben"), callback_data="natal_input")
    kb.button(text=t("BTN_BACK", lang), callback_data="main_menu")
    return kb.as_markup()


def ai_question_keyboard(lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    labels = {
        "ru": ("💭 Задать вопрос", "📝 Примеры"),
        "en": ("💭 Ask a question", "📝 Examples"),
        "de": ("💭 Frage stellen", "📝 Beispiele"),
    }
    ask, examples = labels.get(lang, labels["ru"])
    kb.button(text=ask, callback_data="ask_ai")
    kb.button(text=examples, callback_data="ai_examples")
    kb.button(text="👤 Поддержка", url="https://t.me/Grandmother_admin")
    kb.button(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def ai_dialog_keyboard(lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    labels = {
        "ru": ("🔚 Закончить диалог", "📝 Примеры вопросов"),
        "en": ("🔚 End dialogue", "📝 Question examples"),
        "de": ("🔚 Dialog beenden", "📝 Fragebeispiele"),
    }
    end, examples = labels.get(lang, labels["ru"])
    kb.button(text=end, callback_data="ai_end_dialog")
    kb.button(text=examples, callback_data="ai_examples")
    kb.adjust(1)
    return kb.as_markup()


def compatibility_keyboard(lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    analyze = {"ru": "💑 Анализ", "en": "💑 Analyze", "de": "💑 Analyse"}.get(lang, "💑 Анализ")
    kb.button(text=analyze, callback_data="compat_analyze")
    kb.button(text=t("BTN_BACK", lang), callback_data="main_menu")
    return kb.as_markup()


def profile_keyboard(lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    edit = {"ru": "📝 Редактировать", "en": "📝 Edit", "de": "📝 Bearbeiten"}.get(lang, "📝 Редактировать")
    kb.button(text=edit, callback_data="profile_edit")
    kb.button(text="👤 Поддержка", url="https://t.me/Grandmother_admin")
    kb.button(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")
    return kb.as_markup()


def pdf_type_keyboard(lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    labels = {
        "ru": ("🔮 Натальная карта", "🌙 Гороскоп"),
        "en": ("🔮 Natal chart", "🌙 Horoscope"),
        "de": ("🔮 Geburtshoroskop", "🌙 Horoskop"),
    }
    natal, horo = labels.get(lang, labels["ru"])
    kb.button(text=natal, callback_data="pdf_natal")
    kb.button(text=horo, callback_data="pdf_horoscope")
    kb.button(text=t("BTN_BACK", lang), callback_data="main_menu")
    return kb.as_markup()


def back_to_menu_keyboard_no_support(lang: str = "ru"):
    """Клавиатура без кнопки поддержки (для гороскопа)."""
    kb = InlineKeyboardBuilder()
    kb.button(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")
    return kb.as_markup()


def back_to_menu_keyboard(lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Поддержка", url="https://t.me/Grandmother_admin")
    kb.button(text=t("BTN_BACK_MENU", lang), callback_data="main_menu")
    return kb.as_markup()


def main_reply_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Постоянная reply-клавиатура с кнопкой Меню."""
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("BTN_MENU", lang))]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=t("MENU_INPUT_PLACEHOLDER", lang),
    )
    return kb
