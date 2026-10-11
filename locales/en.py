"""English."""

START_WELCOME = "🌟 Welcome to AstroBot v2 PRO, {first_name}!"
START_MENU_HINT = "👇 Menu is always available at the bottom."
START_CONTINUE = "🚀 Continue"

MENU_TITLE = "🏠 Main menu:"
MENU_BUTTON = "🏠 Menu"

MENU_ITEMS = {
    "natal": "🔮 Natal chart",
    "ai": "✨ Personal question",
    "horoscope": "🌙 Daily horoscope",
    "compat": "💕 Compatibility",
    "profile": "👤 Profile",
    "diary": "📔 Diary",
    "tarot": "🃏 Tarot",
    "pdf": "📄 PDF report",
    "admin": "👑 Admin panel",
    "language": "🌐 Language",
}

LANG_TITLE = "🌐 LANGUAGE SELECTION\n\nCurrent: {current}\n\nChoose language:"
LANG_CHANGED = "✅ Language changed to {name}"
LANG_ALREADY = "🌐 Current language: {name}"
LANG_BUTTON_BACK = "🔙 Back"

ACCESS_DENIED = "❌ Access denied."
SUBSCRIPTION_INACTIVE = "🔒 Subscription inactive.\n\nChoose plan:"
CANCELLED = "✅ Action cancelled."
NOTHING_TO_CANCEL = "Nothing to cancel."

# === Keyboards (Phase 2) ===
BTN_NATAL = "🔮 Natal chart"
BTN_AI = "✨ Personal question"
BTN_HOROSCOPE = "🌙 Daily horoscope"
BTN_COMPAT = "💕 Compatibility"
BTN_PROFILE = "👤 Profile"
BTN_DIARY = "📔 Diary"
BTN_TAROT = "🃏 Tarot"
BTN_PDF = "📄 PDF report"
BTN_ADMIN = "👑 Admin panel"
BTN_LANG = "🌐 Language"

BTN_CONTINUE = "🚀 Continue"
BTN_MENU = "🏠 Menu"
BTN_BACK = "🔙 Back"
BTN_BACK_MENU = "🔙 Main menu"

MENU_INPUT_PLACEHOLDER = "Type a message or tap 🏠 Menu"

# === Welcome /start ===
WELCOME = "🌟 Welcome to AstroBot v2 PRO, {first_name}!"
MENU_HINT = "👇 Menu is always available at the bottom."
MENU_TITLE = "🏠 Main menu:"

# === Subscription ===
TRIAL_ENDED = "🔒 Trial period is over. Choose a plan:"
SUBSCRIPTION_INACTIVE = "🔒 Subscription inactive.\n\nChoose a plan:"
ACCESS_DENIED = "❌ Access denied."

# === Payment ===
PAY_BUTTON = "🔥 {days} days — {stars}⭐"

# === Referrals ===
REFERRAL_NEW_USER = (
    "🎉 Someone joined via your link!\n\n"
    "You got {bonus_days} Premium days."
)

# === Phase 2.2: Natal chart ===
NATAL_MENU_TITLE = (
    "🔮 NATAL CHART CREATION\n\n"
    "Natal chart is your astrological birth map.\n"
    "It shows the planets' positions at your birth.\n\n"
    "To create a chart we need:\n"
    "  • Your name\n"
    "  • Birth date\n"
    "  • Birth time\n"
    "  • Birth place"
)
NATAL_BTN_INPUT = "📝 Enter data"
NATAL_ENTER_NAME = "🌟 ENTER YOUR NAME\n\nFor example: Alexander\n\n/cancel — to cancel"
NATAL_ENTER_DATE = (
    "📅 ENTER YOUR BIRTH DATE\n\n"
    "Formats:\n"
    "  • 15.05.1990\n"
    "  • 15/05/1990\n"
    "  • 1990-05-15\n\n"
    "/cancel — to cancel"
)
NATAL_ENTER_TIME = (
    "⏰ ENTER YOUR BIRTH TIME\n\n"
    "Format: HH:MM\n"
    "For example: 14:30\n\n"
    "If unknown — type 12:00\n"
    "/cancel — to cancel"
)
NATAL_ENTER_PLACE = "📍 ENTER YOUR BIRTH PLACE\n\nFor example: London, UK\n\n/cancel — to cancel"
NATAL_NAME_SHORT = "❌ Name too short. Enter at least 2 characters."
NATAL_NAME_LONG = "❌ Name too long (max 50 characters)."
NATAL_CREATING = "🔮 Creating your natal chart...\n\nThis may take 20-30 seconds."
NATAL_AI_ANALYZING = "🔮 Astrologer is analyzing your chart..."
NATAL_SCHEME_CAPTION = "🔮 Natal chart scheme"
NATAL_READY = "✨ Natal chart is ready!"
NATAL_NEED_BIRTH = "❌ Birth data required. Create a natal chart first."
NATAL_CANCELLED = "Cancelled"

# === Phase 2.2: PDF ===
PDF_MENU_TITLE = (
    "📄 PDF REPORTS\n\n"
    "Choose report type:\n\n"
    "🔮 Natal chart — full astrological analysis\n"
    "🌙 Personal horoscope — today's forecast"
)
PDF_BTN_NATAL = "🔮 Natal chart"
PDF_BTN_HOROSCOPE = "🌙 Horoscope"
PDF_NEED_PROFILE = (
    "❌ Birth data required for PDF.\n\n"
    "Fill your profile: Profile → Edit.\n"
    "Or create a natal chart first."
)
PDF_CREATING_NATAL = "📄 Creating natal chart PDF...\n\nThis may take 20-30 seconds."
PDF_AI_ANALYZING = "🔮 Astrologer is analyzing the chart..."
PDF_CREATING = "📄 Creating PDF..."
PDF_CREATING_HORO = "🌙 Creating horoscope PDF..."
PDF_NATAL_CAPTION = "🔮 Natal chart: {name}"
PDF_HORO_CAPTION = "🌙 Horoscope for {name}"
PDF_CHOOSE_ACTION = "📌 Choose action:"
PDF_DOWNLOAD_BTN = "📄 Download PDF"

# === Phase 2.2.1: Zodiac signs ===
ZODIAC_ARIES = "Aries"
ZODIAC_TAURUS = "Taurus"
ZODIAC_GEMINI = "Gemini"
ZODIAC_CANCER = "Cancer"
ZODIAC_LEO = "Leo"
ZODIAC_VIRGO = "Virgo"
ZODIAC_LIBRA = "Libra"
ZODIAC_SCORPIO = "Scorpio"
ZODIAC_SAGITTARIUS = "Sagittarius"
ZODIAC_CAPRICORN = "Capricorn"
ZODIAC_AQUARIUS = "Aquarius"
ZODIAC_PISCES = "Pisces"
ZODIAC_UNKNOWN = "Unknown"

# === Elements ===
ELEM_FIRE = "Fire"
ELEM_EARTH = "Earth"
ELEM_AIR = "Air"
ELEM_WATER = "Water"

# === Qualities ===
QUAL_CARDINAL = "Cardinal"
QUAL_FIXED = "Fixed"
QUAL_MUTABLE = "Mutable"

# === Planets ===
PLANET_SUN = "Sun"
PLANET_MOON = "Moon"
PLANET_MERCURY = "Mercury"
PLANET_VENUS = "Venus"
PLANET_MARS = "Mars"
PLANET_JUPITER = "Jupiter"
PLANET_SATURN = "Saturn"
PLANET_URANUS = "Uranus"
PLANET_NEPTUNE = "Neptune"
PLANET_PLUTO = "Pluto"

# === Natal chart headers ===
NATAL_TITLE = "NATAL CHART"
NATAL_HEADER_MAIN = "MAIN CHARACTERISTICS"
NATAL_HEADER_PLANETS = "PLANET POSITIONS"
NATAL_HEADER_HOUSES = "ASTROLOGICAL HOUSES"
NATAL_HEADER_AI = "ASTROLOGICAL ANALYSIS"
NATAL_LABEL_SUN = "Sun in sign"
NATAL_LABEL_ELEMENT = "Element"
NATAL_LABEL_QUALITY = "Quality"
NATAL_LABEL_ASC = "Ascendant"
NATAL_LABEL_HOUSE = "house"
NATAL_LABEL_RETRO = "(retrograde)"

# === PDF ===
PDF_NATAL_TITLE = "NATAL CHART"
PDF_HOROSCOPE_TITLE = "HOROSCOPE"
PDF_LABEL_DATE = "Date"
PDF_FOOTER = "Astrology is a tool for self-knowledge. The stars show the way, but the choice is always yours!"
PDF_FOOTER_CREATED = "Generated by AstroBot"

# === Phase 2.3: Tarot ===
TAROT_MENU_TITLE = (
    "TAROT \u2014 FORTUNE AND ADVICE\n\n"
    "Ask your question \u2014 and Tarot cards will answer "
    "with a personal interpretation from a tarot reader.\n\n"
    "\U0001F4A1 How it works:\n"
    "1. You write a question (love, work, future)\n"
    "2. We draw 3 cards\n"
    "3. Tarot reader gives a detailed interpretation\n\n"
    "\u26a0\ufe0f The same question on the same day \u2014 the same reading.\n"
    "Next day \u2014 a new one."
)
TAROT_BTN_NEW = "\U0001F52E Make a reading"
TAROT_BTN_MORE = "\U0001F52E Another reading"
TAROT_BTN_BUY = "\U0001F48E Buy subscription"
TAROT_LOCK = "\n\n\U0001F512 Available by subscription."
TAROT_NOT_LOADED = "\u274c Cards not loaded"
TAROT_NEED_SUB = "\U0001F512 Subscription required"
TAROT_ASK_Q = (
    "\U0001F52E ASK YOUR QUESTION\n\n"
    "Write the question you want answered.\n\n"
    "Examples:\n"
    "\u2022 What awaits me in relationships?\n"
    "\u2022 Should I change jobs?\n"
    "\u2022 What awaits me next month?\n\n"
    "/cancel \u2014 to cancel"
)
TAROT_CANCELLED = "Cancelled."
TAROT_TOO_SHORT = "\u274c Question is too short. Please elaborate."
TAROT_PROCESSING = "\U0001F52E Shuffling cards... 5-15 seconds."
TAROT_ERROR = "\u274c Error: {err}"
TAROT_AI_TITLE = "\U0001F916 ASTROLOGER'S INTERPRETATION"
TAROT_AI_CACHE = " (from cache)"
TAROT_WANT_MORE = "Want another reading?"
TAROT_POS_PAST = "\U0001F550 Past"
TAROT_POS_NOW = "\U0001F550 Present"
TAROT_POS_FUTURE = "\U0001F550 Future"

# === Tarot positions (EN) ===
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

TAROT_LABEL_BLOCK = "What blocks"
TAROT_LABEL_HELP = "What helps"
TAROT_LABEL_PROSPECT = "Prospect"
TAROT_LABEL_PAST = "Past"
TAROT_LABEL_NOW = "Present"
TAROT_LABEL_FUTURE = "Future"
TAROT_LABEL_WORRIES = "What worries"
TAROT_LABEL_HELPS = "What helps"
TAROT_LABEL_NEAR = "Near term"
TAROT_LABEL_MID = "Mid term"
TAROT_LABEL_FAR = "Long term"
TAROT_LABEL_ADVICE = "Advice"
TAROT_LABEL_TOTAL = "Result"

# === Phase 2.3B: Compatibility ===
COMPAT_MENU_TITLE = (
    "\U0001F495 COMPATIBILITY ANALYSIS\n\n"
    "Enter the zodiac sign of the first partner:\n"
    "For example: Aries, Taurus, Leo\n\n"
    "Or enter a birth date in YYYY-MM-DD format.\n\n"
    "/cancel \u2014 to cancel"
)
COMPAT_SUB_LOCK = (
    "\u274c The \u00abCompatibility\u00bb feature is available by subscription only.\n\n"
    "Subscribe to use it."
)
COMPAT_SUB_LOCK_SHORT = "\u274c Available by subscription only."
COMPAT_PARTNER1_NOT_RECOGNIZED = (
    "\u274c Couldn't recognize the zodiac sign.\n\n"
    "Enter a sign name (Aries, Taurus...) "
    "or a date in YYYY-MM-DD format."
)
COMPAT_PARTNER1_OK = "\u2705 First partner: {sign}\n\nNow enter the sign or date of the second partner:\n\n/cancel \u2014 to cancel"
COMPAT_PARTNER2_NOT_RECOGNIZED = "\u274c Couldn't recognize the sign. Try again."
COMPAT_PROCESSING = "\U0001F52E Astrologer is analyzing compatibility..."
COMPAT_CANCELLED = "Cancelled"
COMPAT_RESULT_TITLE = "\U0001F495 COMPATIBILITY ANALYSIS"
COMPAT_FALLBACK_LEVEL_IDEAL = "Ideal compatibility"
COMPAT_FALLBACK_LEVEL_EXCELLENT = "Excellent compatibility"
COMPAT_FALLBACK_LEVEL_GOOD = "Good compatibility"
COMPAT_FALLBACK_LEVEL_MEDIUM = "Medium compatibility"
COMPAT_FALLBACK_LEVEL_HARD = "Difficult compatibility"

# === Phase 2.3C: Horoscope ===
HOROSCOPE_PROCESSING = (
    "\U0001F305 Generating today's horoscope...\n\n"
    "This will take 5-15 seconds."
)
HOROSCOPE_CACHE_LOG = "\U0001F305 Horoscope from cache"
HOROSCOPE_FALLBACK_TITLE = "\U0001F305 ASTROLOGICAL FORECAST FOR TODAY"
HOROSCOPE_FALLBACK_TEXT = (
    "\U0001F305 GENERAL FORECAST\n"
    "Today the stars align in a harmonious configuration, creating favorable energy.\n\n"
    "\U0001F4A1 ADVICE OF THE DAY\n"
    "Trust your intuition \u2014 it is especially strong today.\n\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
    "\U0001F52E Remember: astrology is a guide, not a verdict."
)
