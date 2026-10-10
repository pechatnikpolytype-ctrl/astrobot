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
