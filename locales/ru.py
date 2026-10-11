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

# === Phase 2.3: Tarot ===
TAROT_MENU_TITLE = (
    "TAROT\u2014 \u0413\u0410\u0414\u0410\u041d\u0418\u0415 \u0418 \u0421\u041e\u0412\u0415\u0422\u042b\n\n"
    "\u0417\u0430\u0434\u0430\u0439\u0442\u0435 \u0441\u0432\u043e\u0439 \u0432\u043e\u043f\u0440\u043e\u0441 \u2014 \u0438 \u043a\u0430\u0440\u0442\u044b \u0422\u0430\u0440\u043e \u0434\u0430\u0434\u0443\u0442 \u043e\u0442\u0432\u0435\u0442 "
    "\u0432\u043c\u0435\u0441\u0442\u0435 \u0441 \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u044c\u043d\u044b\u043c \u0442\u043e\u043b\u043a\u043e\u0432\u0430\u043d\u0438\u0435\u043c \u043e\u0442 \u0442\u0430\u0440\u043e\u043b\u043e\u0433\u0430.\n\n"
    "\U0001F4A1 \u041a\u0430\u043a \u044d\u0442\u043e \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442:\n"
    "1. \u0412\u044b \u043f\u0438\u0448\u0435\u0442\u0435 \u0432\u043e\u043f\u0440\u043e\u0441 (\u043f\u0440\u043e \u043b\u044e\u0431\u043e\u0432\u044c, \u0440\u0430\u0431\u043e\u0442\u0443, \u0431\u0443\u0434\u0443\u0449\u0435\u0435)\n"
    "2. \u041c\u044b \u0432\u044b\u0442\u044f\u0433\u0438\u0432\u0430\u0435\u043c 3 \u043a\u0430\u0440\u0442\u044b\n"
    "3. \u0422\u0430\u0440\u043e\u043b\u043e\u0433 \u0434\u0430\u0451\u0442 \u0440\u0430\u0437\u0432\u0451\u0440\u043d\u0443\u0442\u043e\u0435 \u0442\u043e\u043b\u043a\u043e\u0432\u0430\u043d\u0438\u0435\n\n"
    "\u26a0\ufe0f \u041e\u0434\u0438\u043d \u0438 \u0442\u043e\u0442 \u0436\u0435 \u0432\u043e\u043f\u0440\u043e\u0441 \u0432 \u043e\u0434\u0438\u043d \u0434\u0435\u043d\u044c \u2014 \u043e\u0434\u0438\u043d \u0438 \u0442\u043e\u0442 \u0436\u0435 \u0440\u0430\u0441\u043a\u043b\u0430\u0434.\n"
    "\u041d\u0430 \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u0434\u0435\u043d\u044c \u2014 \u043d\u043e\u0432\u044b\u0439."
)
TAROT_BTN_NEW = "\U0001F52E \u0421\u0434\u0435\u043b\u0430\u0442\u044c \u0440\u0430\u0441\u043a\u043b\u0430\u0434"
TAROT_BTN_MORE = "\U0001F52E \u0415\u0449\u0451 \u0440\u0430\u0441\u043a\u043b\u0430\u0434"
TAROT_BTN_BUY = "\U0001F48E \u041a\u0443\u043f\u0438\u0442\u044c \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0443"
TAROT_LOCK = "\n\n\U0001F512 \u0424\u0443\u043d\u043a\u0446\u0438\u044f \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430 \u043f\u043e \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0435."
TAROT_NOT_LOADED = "\u274c \u041a\u0430\u0440\u0442\u044b \u043d\u0435 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u044b"
TAROT_NEED_SUB = "\U0001F512 \u0422\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0430"
TAROT_ASK_Q = (
    "\U0001F52E \u0417\u0410\u0414\u0410\u0419\u0422\u0415 \u0412\u0410\u0428 \u0412\u041e\u041f\u0420\u041e\u0421\n\n"
    "\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u0432\u043e\u043f\u0440\u043e\u0441, \u043d\u0430 \u043a\u043e\u0442\u043e\u0440\u044b\u0439 \u0445\u043e\u0442\u0438\u0442\u0435 \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u043e\u0442\u0432\u0435\u0442.\n\n"
    "\u041f\u0440\u0438\u043c\u0435\u0440\u044b:\n"
    "\u2022 \u0427\u0442\u043e \u043c\u0435\u043d\u044f \u0436\u0434\u0451\u0442 \u0432 \u043e\u0442\u043d\u043e\u0448\u0435\u043d\u0438\u044f\u0445?\n"
    "\u2022 \u0421\u0442\u043e\u0438\u0442 \u043b\u0438 \u043c\u0435\u043d\u044f\u0442\u044c \u0440\u0430\u0431\u043e\u0442\u0443?\n"
    "\u2022 \u0427\u0442\u043e \u0436\u0434\u0451\u0442 \u043c\u0435\u043d\u044f \u0432 \u0431\u043b\u0438\u0436\u0430\u0439\u0448\u0438\u0439 \u043c\u0435\u0441\u044f\u0446?\n\n"
    "/cancel \u2014 \u043e\u0442\u043c\u0435\u043d\u0430"
)
TAROT_CANCELLED = "\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e."
TAROT_TOO_SHORT = "\u274c \u0412\u043e\u043f\u0440\u043e\u0441 \u0441\u043b\u0438\u0448\u043a\u043e\u043c \u043a\u043e\u0440\u043e\u0442\u043a\u0438\u0439. \u041e\u043f\u0438\u0448\u0438\u0442\u0435 \u043f\u043e\u0434\u0440\u043e\u0431\u043d\u0435\u0435."
TAROT_PROCESSING = "\U0001F52E \u0422\u0430\u0441\u0443\u0435\u043c \u043a\u0430\u0440\u0442\u044b... \u042d\u0442\u043e \u0437\u0430\u0439\u043c\u0451\u0442 5-15 \u0441\u0435\u043a\u0443\u043d\u0434."
TAROT_ERROR = "\u274c \u041e\u0448\u0438\u0431\u043a\u0430: {err}"
TAROT_AI_TITLE = "\U0001F916 \u0422\u041e\u041b\u041a\u041e\u0412\u0410\u041d\u0418\u0415 \u0410\u0421\u0422\u0420\u041e\u041b\u041e\u0413\u0410"
TAROT_AI_CACHE = " (\u0438\u0437 \u043a\u044d\u0448\u0430)"
TAROT_WANT_MORE = "\u0425\u043e\u0442\u0438\u0442\u0435 \u0435\u0449\u0451 \u043e\u0434\u0438\u043d \u0440\u0430\u0441\u043a\u043b\u0430\u0434?"
TAROT_POS_PAST = "\U0001F550 \u041f\u0440\u043e\u0448\u043b\u043e\u0435"
TAROT_POS_NOW = "\U0001F550 \u041d\u0430\u0441\u0442\u043e\u044f\u0449\u0435\u0435"
TAROT_POS_FUTURE = "\U0001F550 \u0411\u0443\u0434\u0443\u0449\u0435\u0435"

# === Tarot positions ===
TAROT_POS_LOVE_1 = "\U0001F494 {block}"
TAROT_POS_LOVE_2 = "\U0001F496 {help}"
TAROT_POS_LOVE_3 = "\u2728 {prospect}"

TAROT_POS_WORK_1 = "\U0001F4C9 {past}"
TAROT_POS_WORK_2 = "\U0001F4CA {now}"
TAROT_POS_WORK_3 = "\U0001F680 {future}"

TAROT_POS_HEALTH_1 = "\U0001F33F {worries}"
TAROT_POS_HEALTH_2 = "\U0001F48A {helps}"
TAROT_POS_HEALTH_3 = "\u2728 {prospect}"

TAROT_POS_FUTURE_1 = "\U0001F550 {near}"
TAROT_POS_FUTURE_2 = "\U0001F4C5 {mid}"
TAROT_POS_FUTURE_3 = "\U0001F52E {far}"

TAROT_POS_ADVICE_1 = "\u26A1 {now}"
TAROT_POS_ADVICE_2 = "\U0001F4A1 {advice}"
TAROT_POS_ADVICE_3 = "\U0001F31F {total}"

TAROT_POS_GENERIC_1 = "\U0001F550 {past}"
TAROT_POS_GENERIC_2 = "\U0001F550 {now}"
TAROT_POS_GENERIC_3 = "\U0001F550 {future}"

# Labels
TAROT_LABEL_BLOCK = "\u0427\u0442\u043e \u043c\u0435\u0448\u0430\u0435\u0442"
TAROT_LABEL_HELP = "\u0427\u0442\u043e \u043f\u043e\u043c\u043e\u0436\u0435\u0442"
TAROT_LABEL_PROSPECT = "\u041f\u0435\u0440\u0441\u043f\u0435\u043a\u0442\u0438\u0432\u0430"
TAROT_LABEL_PAST = "\u041f\u0440\u043e\u0448\u043b\u043e\u0435"
TAROT_LABEL_NOW = "\u041d\u0430\u0441\u0442\u043e\u044f\u0449\u0435\u0435"
TAROT_LABEL_FUTURE = "\u0411\u0443\u0434\u0443\u0449\u0435\u0435"
TAROT_LABEL_WORRIES = "\u0427\u0442\u043e \u0431\u0435\u0441\u043f\u043e\u043a\u043e\u0438\u0442"
TAROT_LABEL_HELPS = "\u0427\u0442\u043e \u043f\u043e\u043c\u043e\u0436\u0435\u0442"
TAROT_LABEL_NEAR = "\u0411\u043b\u0438\u0436\u0430\u0439\u0448\u0435\u0435"
TAROT_LABEL_MID = "\u0421\u0440\u0435\u0434\u043d\u0435\u0441\u0440\u043e\u0447\u043d\u043e\u0435"
TAROT_LABEL_FAR = "\u0414\u0430\u043b\u044c\u043d\u0435\u0435"
TAROT_LABEL_ADVICE = "\u0421\u043e\u0432\u0435\u0442"
TAROT_LABEL_TOTAL = "\u0418\u0442\u043e\u0433"

# === Phase 2.3B: Compatibility ===
COMPAT_MENU_TITLE = (
    "\U0001F495 \u0410\u041d\u0410\u041b\u0418\u0417 \u0421\u041e\u0412\u041c\u0415\u0421\u0422\u0418\u041c\u041e\u0421\u0422\u0418\n\n"
    "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0437\u043d\u0430\u043a \u0437\u043e\u0434\u0438\u0430\u043a\u0430 \u043f\u0435\u0440\u0432\u043e\u0433\u043e \u043f\u0430\u0440\u0442\u043d\u0451\u0440\u0430:\n"
    "\u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: \u041e\u0432\u0435\u043d, \u0422\u0435\u043b\u0435\u0446, \u041b\u0435\u0432\n\n"
    "\u0418\u043b\u0438 \u0443\u043a\u0430\u0436\u0438\u0442\u0435 \u0434\u0430\u0442\u0443 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u0432 \u0444\u043e\u0440\u043c\u0430\u0442\u0435 \u0413\u0413\u0413\u0413-\u041c\u041c-\u0414\u0414.\n\n"
    "/cancel \u2014 \u043e\u0442\u043c\u0435\u043d\u0430"
)
COMPAT_SUB_LOCK = (
    "\u274c \u0424\u0443\u043d\u043a\u0446\u0438\u044f \u00ab\u0421\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u043e\u0441\u0442\u044c\u00bb \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430 \u0442\u043e\u043b\u044c\u043a\u043e \u043f\u043e \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0435.\n\n"
    "\u041e\u0444\u043e\u0440\u043c\u0438\u0442\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0443, \u0447\u0442\u043e\u0431\u044b \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c\u0441\u044f."
)
COMPAT_SUB_LOCK_SHORT = "\u274c \u0414\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u0442\u043e\u043b\u044c\u043a\u043e \u043f\u043e \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0435."
COMPAT_PARTNER1_NOT_RECOGNIZED = (
    "\u274c \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0438\u0442\u044c \u0437\u043d\u0430\u043a \u0437\u043e\u0434\u0438\u0430\u043a\u0430.\n\n"
    "\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0437\u043d\u0430\u043a\u0430 (\u041e\u0432\u0435\u043d, \u0422\u0435\u043b\u0435\u0446...) "
    "\u0438\u043b\u0438 \u0434\u0430\u0442\u0443 \u0432 \u0444\u043e\u0440\u043c\u0430\u0442\u0435 \u0413\u0413\u0413\u0413-\u041c\u041c-\u0414\u0414."
)
COMPAT_PARTNER1_OK = "\u2705 \u041f\u0435\u0440\u0432\u044b\u0439 \u043f\u0430\u0440\u0442\u043d\u0451\u0440: {sign}\n\n\u0422\u0435\u043f\u0435\u0440\u044c \u0432\u0432\u0435\u0434\u0438\u0442\u0435 \u0437\u043d\u0430\u043a \u0438\u043b\u0438 \u0434\u0430\u0442\u0443 \u0432\u0442\u043e\u0440\u043e\u0433\u043e \u043f\u0430\u0440\u0442\u043d\u0451\u0440\u0430:\n\n/cancel \u2014 \u043e\u0442\u043c\u0435\u043d\u0430"
COMPAT_PARTNER2_NOT_RECOGNIZED = "\u274c \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0438\u0442\u044c \u0437\u043d\u0430\u043a. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0435\u0449\u0451 \u0440\u0430\u0437."
COMPAT_PROCESSING = "\U0001F52E \u0410\u0441\u0442\u0440\u043e\u043b\u043e\u0433 \u0430\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u0443\u0435\u0442 \u0441\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u043e\u0441\u0442\u044c..."
COMPAT_CANCELLED = "\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e"
COMPAT_RESULT_TITLE = "\U0001F495 \u0410\u041d\u0410\u041b\u0418\u0417 \u0421\u041e\u0412\u041c\u0415\u0421\u0422\u0418\u041c\u041e\u0421\u0422\u0418"
COMPAT_FALLBACK_LEVEL_IDEAL = "\u0418\u0434\u0435\u0430\u043b\u044c\u043d\u0430\u044f \u0441\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u043e\u0441\u0442\u044c"
COMPAT_FALLBACK_LEVEL_EXCELLENT = "\u041e\u0442\u043b\u0438\u0447\u043d\u0430\u044f \u0441\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u043e\u0441\u0442\u044c"
COMPAT_FALLBACK_LEVEL_GOOD = "\u0425\u043e\u0440\u043e\u0448\u0430\u044f \u0441\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u043e\u0441\u0442\u044c"
COMPAT_FALLBACK_LEVEL_MEDIUM = "\u0421\u0440\u0435\u0434\u043d\u044f\u044f \u0441\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u043e\u0441\u0442\u044c"
COMPAT_FALLBACK_LEVEL_HARD = "\u0421\u043b\u043e\u0436\u043d\u0430\u044f \u0441\u043e\u0432\u043c\u0435\u0441\u0442\u0438\u043c\u043e\u0441\u0442\u044c"

# === Phase 2.3C: Horoscope ===
HOROSCOPE_PROCESSING = (
    "\U0001F305 \u0413\u0435\u043d\u0435\u0440\u0438\u0440\u0443\u044e \u0433\u043e\u0440\u043e\u0441\u043a\u043e\u043f \u043d\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f...\n\n"
    "\u042d\u0442\u043e \u0437\u0430\u0439\u043c\u0451\u0442 5-15 \u0441\u0435\u043a\u0443\u043d\u0434."
)
HOROSCOPE_CACHE_LOG = "\U0001F305 \u0413\u043e\u0440\u043e\u0441\u043a\u043e\u043f \u0438\u0437 \u043a\u044d\u0448\u0430"
HOROSCOPE_FALLBACK_TITLE = "\U0001F305 \u0410\u0421\u0422\u0420\u041e\u041b\u041e\u0413\u0418\u0427\u0415\u0421\u041a\u0418\u0419 \u041f\u0420\u041e\u0413\u041d\u041e\u0417 \u041d\u0410 \u0421\u0415\u0413\u041e\u0414\u041d\u042f"
HOROSCOPE_FALLBACK_TEXT = (
    "\U0001F305 \u041e\u0411\u0429\u0418\u0419 \u041f\u0420\u041e\u0413\u041d\u041e\u0417\n"
    "\u0421\u0435\u0433\u043e\u0434\u043d\u044f \u0437\u0432\u0451\u0437\u0434\u044b \u0432\u044b\u0441\u0442\u0440\u0430\u0438\u0432\u0430\u044e\u0442\u0441\u044f \u0432 \u0433\u0430\u0440\u043c\u043e\u043d\u0438\u0447\u043d\u0443\u044e \u043a\u043e\u043d\u0444\u0438\u0433\u0443\u0440\u0430\u0446\u0438\u044e, \u0441\u043e\u0437\u0434\u0430\u0432\u0430\u044f \u0431\u043b\u0430\u0433\u043e\u043f\u0440\u0438\u044f\u0442\u043d\u0443\u044e \u044d\u043d\u0435\u0440\u0433\u0435\u0442\u0438\u043a\u0443.\n\n"
    "\U0001F4A1 \u0421\u041e\u0412\u0415\u0422 \u0414\u041d\u042f\n"
    "\u0414\u043e\u0432\u0435\u0440\u044c\u0442\u0435\u0441\u044c \u0441\u0432\u043e\u0435\u0439 \u0438\u043d\u0442\u0443\u0438\u0446\u0438\u0438 \u2014 \u043e\u043d\u0430 \u043e\u0441\u043e\u0431\u0435\u043d\u043d\u043e \u0441\u0438\u043b\u044c\u043d\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f.\n\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
    "\U0001F52E \u041f\u043e\u043c\u043d\u0438\u0442\u0435: \u0430\u0441\u0442\u0440\u043e\u043b\u043e\u0433\u0438\u044f \u2014 \u044d\u0442\u043e \u0440\u0443\u043a\u043e\u0432\u043e\u0434\u0441\u0442\u0432\u043e, \u0430 \u043d\u0435 \u043f\u0440\u0438\u0433\u043e\u0432\u043e\u0440."
)
