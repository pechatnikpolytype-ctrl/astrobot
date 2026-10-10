"""Русский — базовый язык (fallback)."""

START_WELCOME = "🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!"
START_MENU_HINT = "👇 Меню всегда доступно кнопкой внизу."
START_CONTINUE = "🚀 Продолжить"

MENU_TITLE = "🏠 Главное меню:"
MENU_BUTTON = "🏠 Меню"

MENU_ITEMS = {
    "natal": "🔮 Натальная карта",
    "ai": "✨ Личный вопрос",
    "horoscope": "🌙 Гороскоп дня",
    "compat": "💕 Совместимость",
    "profile": "👤 Профиль",
    "diary": "📔 Дневник",
    "tarot": "🃏 Таро",
    "pdf": "📄 PDF отчёт",
    "admin": "👑 Админ-панель",
    "language": "🌐 Язык",
}

LANG_TITLE = "🌐 ВЫБОР ЯЗЫКА\n\nТекущий: {current}\n\nВыберите язык:"
LANG_CHANGED = "✅ Язык изменён на {name}"
LANG_ALREADY = "🌐 Текущий язык: {name}"
LANG_BUTTON_BACK = "🔙 Назад"

ACCESS_DENIED = "❌ Доступ запрещён."
SUBSCRIPTION_INACTIVE = "🔒 Подписка не активна.\n\nВыберите тариф:"
CANCELLED = "✅ Действие отменено."
NOTHING_TO_CANCEL = "Нечего отменять."

# === Клавиатуры (Фаза 2) ===
BTN_NATAL = "🔮 Натальная карта"
BTN_AI = "✨ Личный вопрос"
BTN_HOROSCOPE = "🌙 Гороскоп дня"
BTN_COMPAT = "💕 Совместимость"
BTN_PROFILE = "👤 Профиль"
BTN_DIARY = "📔 Дневник"
BTN_TAROT = "🃏 Таро"
BTN_PDF = "📄 PDF отчёт"
BTN_ADMIN = "👑 Админ-панель"
BTN_LANG = "🌐 Язык"

BTN_CONTINUE = "🚀 Продолжить"
BTN_MENU = "🏠 Меню"
BTN_BACK = "🔙 Назад"
BTN_BACK_MENU = "🔙 Главное меню"

MENU_INPUT_PLACEHOLDER = "Напишите сообщение или нажмите 🏠 Меню"

# === Приветствие /start ===
WELCOME = "🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!"
MENU_HINT = "👇 Меню всегда доступно кнопкой внизу."
MENU_TITLE = "🏠 Главное меню:"

# === Подписка ===
TRIAL_ENDED = "🔒 Пробный период закончился. Выберите тариф:"
SUBSCRIPTION_INACTIVE = "🔒 Подписка не активна.\n\nВыберите тариф:"
ACCESS_DENIED = "❌ Доступ запрещён."

# === Оплата (кнопки) ===
PAY_BUTTON = "🔥 {days} дней — {stars}⭐"

# === Рефералы ===
REFERRAL_NEW_USER = (
    "🎉 По вашей ссылке зарегистрировался новый пользователь!\n\n"
    "Вам начислено {bonus_days} дней Премиум."
)

# === Фаза 2.2: Натальная карта ===
NATAL_MENU_TITLE = (
    "🔮 СОЗДАНИЕ НАТАЛЬНОЙ КАРТЫ\n\n"
    "Натальная карта — это астрологическая карта рождения.\n"
    "Она показывает положение планет в момент вашего рождения.\n\n"
    "Для создания карты нужны:\n"
    "  • Ваше имя\n"
    "  • Дата рождения\n"
    "  • Время рождения\n"
    "  • Место рождения"
)
NATAL_BTN_INPUT = "📝 Ввести данные"
NATAL_ENTER_NAME = "🌟 ВВЕДИТЕ ВАШЕ ИМЯ\n\nНапример: Александр\n\n/cancel — отмена"
NATAL_ENTER_DATE = (
    "📅 ВВЕДИТЕ ДАТУ РОЖДЕНИЯ\n\n"
    "Форматы:\n"
    "  • 15.05.1990\n"
    "  • 15/05/1990\n"
    "  • 1990-05-15\n\n"
    "/cancel — отмена"
)
NATAL_ENTER_TIME = (
    "⏰ ВВЕДИТЕ ВРЕМЯ РОЖДЕНИЯ\n\n"
    "Формат: ЧЧ:ММ\n"
    "Например: 14:30\n\n"
    "Если не знаете — напишите 12:00\n"
    "/cancel — отмена"
)
NATAL_ENTER_PLACE = "📍 ВВЕДИТЕ МЕСТО РОЖДЕНИЯ\n\nНапример: Москва, Россия\n\n/cancel — отмена"
NATAL_NAME_SHORT = "❌ Имя слишком короткое. Введите хотя бы 2 символа."
NATAL_NAME_LONG = "❌ Имя слишком длинное (максимум 50 символов)."
NATAL_CREATING = "🔮 Создаю натальную карту...\n\nЭто может занять 20-30 секунд."
NATAL_AI_ANALYZING = "🔮 Астролог анализирует вашу карту..."
NATAL_SCHEME_CAPTION = "🔮 Схема натальной карты"
NATAL_READY = "✨ Натальная карта готова!"
NATAL_NEED_BIRTH = "❌ Нужны данные о рождении. Сначала создайте натальную карту."
NATAL_CANCELLED = "Отменено"

# === Фаза 2.2: PDF ===
PDF_MENU_TITLE = (
    "📄 PDF ОТЧЁТЫ\n\n"
    "Выберите тип отчёта:\n\n"
    "🔮 Натальная карта — полный астрологический разбор\n"
    "🌙 Личный гороскоп — прогноз на сегодня"
)
PDF_BTN_NATAL = "🔮 Натальная карта"
PDF_BTN_HOROSCOPE = "🌙 Гороскоп"
PDF_NEED_PROFILE = (
    "❌ Для создания PDF нужны данные о рождении.\n\n"
    "Заполните профиль: Профиль → Редактировать.\n"
    "Или создайте натальную карту вручную."
)
PDF_CREATING_NATAL = "📄 Создаю PDF натальной карты...\n\nЭто может занять 20-30 секунд."
PDF_AI_ANALYZING = "🔮 Астролог анализирует карту..."
PDF_CREATING = "📄 Создаю PDF..."
PDF_CREATING_HORO = "🌙 Создаю PDF гороскопа..."
PDF_NATAL_CAPTION = "🔮 Натальная карта: {name}"
PDF_HORO_CAPTION = "🌙 Гороскоп для {name}"
PDF_CHOOSE_ACTION = "📌 Выберите действие:"
PDF_DOWNLOAD_BTN = "📄 Скачать PDF-отчёт"

# === Фаза 2.2.1: Знаки зодиака ===
ZODIAC_ARIES = "Овен"
ZODIAC_TAURUS = "Телец"
ZODIAC_GEMINI = "Близнецы"
ZODIAC_CANCER = "Рак"
ZODIAC_LEO = "Лев"
ZODIAC_VIRGO = "Дева"
ZODIAC_LIBRA = "Весы"
ZODIAC_SCORPIO = "Скорпион"
ZODIAC_SAGITTARIUS = "Стрелец"
ZODIAC_CAPRICORN = "Козерог"
ZODIAC_AQUARIUS = "Водолей"
ZODIAC_PISCES = "Рыбы"
ZODIAC_UNKNOWN = "Неизвестно"

# === Элементы ===
ELEM_FIRE = "Огонь"
ELEM_EARTH = "Земля"
ELEM_AIR = "Воздух"
ELEM_WATER = "Вода"

# === Качества ===
QUAL_CARDINAL = "Кардинальный"
QUAL_FIXED = "Фиксированный"
QUAL_MUTABLE = "Мутабельный"

# === Планеты ===
PLANET_SUN = "Солнце"
PLANET_MOON = "Луна"
PLANET_MERCURY = "Меркурий"
PLANET_VENUS = "Венера"
PLANET_MARS = "Марс"
PLANET_JUPITER = "Юпитер"
PLANET_SATURN = "Сатурн"
PLANET_URANUS = "Уран"
PLANET_NEPTUNE = "Нептун"
PLANET_PLUTO = "Плутон"

# === Заголовки натальной карты ===
NATAL_TITLE = "НАТАЛЬНАЯ КАРТА"
NATAL_HEADER_MAIN = "ОСНОВНЫЕ ХАРАКТЕРИСТИКИ"
NATAL_HEADER_PLANETS = "ПОЛОЖЕНИЕ ПЛАНЕТ"
NATAL_HEADER_HOUSES = "АСТРОЛОГИЧЕСКИЕ ДОМА"
NATAL_HEADER_AI = "АСТРОЛОГИЧЕСКИЙ АНАЛИЗ"
NATAL_LABEL_SUN = "Солнце в знаке"
NATAL_LABEL_ELEMENT = "Стихия"
NATAL_LABEL_QUALITY = "Качество"
NATAL_LABEL_ASC = "Асцендент"
NATAL_LABEL_HOUSE = "дом"
NATAL_LABEL_RETRO = "(ретроградный)"

# === PDF ===
PDF_NATAL_TITLE = "НАТАЛЬНАЯ КАРТА"
PDF_HOROSCOPE_TITLE = "ГОРОСКОП"
PDF_LABEL_DATE = "Дата"
PDF_FOOTER = "Астрология — это инструмент самопознания. Звёзды указывают путь, но выбор всегда за вами!"
PDF_FOOTER_CREATED = "Сгенерировано AstroBot"
