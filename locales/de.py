"""Deutsch."""

START_WELCOME = "🌟 Willkommen bei AstroBot v2 PRO, {first_name}!"
START_MENU_HINT = "👇 Das Menü ist immer unten verfügbar."
START_CONTINUE = "🚀 Weiter"

MENU_TITLE = "🏠 Hauptmenü:"
MENU_BUTTON = "🏠 Menü"

MENU_ITEMS = {
    "natal": "🔮 Geburtshoroskop",
    "ai": "✨ Persönliche Frage",
    "horoscope": "🌙 Tageshoroskop",
    "compat": "💕 Kompatibilität",
    "profile": "👤 Profil",
    "diary": "📔 Tagebuch",
    "tarot": "🃏 Tarot",
    "pdf": "📄 PDF-Bericht",
    "admin": "👑 Admin-Panel",
    "language": "🌐 Sprache",
}

LANG_TITLE = "🌐 SPRACHAUSWAHL\n\nAktuell: {current}\n\nSprache wählen:"
LANG_CHANGED = "✅ Sprache geändert zu {name}"
LANG_ALREADY = "🌐 Aktuelle Sprache: {name}"
LANG_BUTTON_BACK = "🔙 Zurück"

ACCESS_DENIED = "❌ Zugriff verweigert."
SUBSCRIPTION_INACTIVE = "🔒 Abo inaktiv.\n\nTarif wählen:"
CANCELLED = "✅ Aktion abgebrochen."
NOTHING_TO_CANCEL = "Nichts abzubrechen."

# === Keyboards (Phase 2) ===
BTN_NATAL = "🔮 Geburtshoroskop"
BTN_AI = "✨ Persönliche Frage"
BTN_HOROSCOPE = "🌙 Tageshoroskop"
BTN_COMPAT = "💕 Kompatibilität"
BTN_PROFILE = "👤 Profil"
BTN_DIARY = "📔 Tagebuch"
BTN_TAROT = "🃏 Tarot"
BTN_PDF = "📄 PDF-Bericht"
BTN_ADMIN = "👑 Admin-Panel"
BTN_LANG = "🌐 Sprache"

BTN_CONTINUE = "🚀 Weiter"
BTN_MENU = "🏠 Menü"
BTN_BACK = "🔙 Zurück"
BTN_BACK_MENU = "🔙 Hauptmenü"

MENU_INPUT_PLACEHOLDER = "Nachricht senden oder 🏠 Menü tippen"

# === Willkommen /start ===
WELCOME = "🌟 Willkommen bei AstroBot v2 PRO, {first_name}!"
MENU_HINT = "👇 Das Menü ist immer unten verfügbar."
MENU_TITLE = "🏠 Hauptmenü:"

# === Abo ===
TRIAL_ENDED = "🔒 Testphase vorbei. Tarif wählen:"
SUBSCRIPTION_INACTIVE = "🔒 Abo inaktiv.\n\nTarif wählen:"
ACCESS_DENIED = "❌ Zugriff verweigert."

# === Zahlung ===
PAY_BUTTON = "🔥 {days} Tage — {stars}⭐"

# === Empfehlungen ===
REFERRAL_NEW_USER = (
    "🎉 Jemand ist über deinen Link beigetreten!\n\n"
    "Du bekommst {bonus_days} Premium-Tage."
)

# === Phase 2.2: Geburtshoroskop ===
NATAL_MENU_TITLE = (
    "🔮 GEBURTSHOROSKOP ERSTELLEN\n\n"
    "Das Geburtshoroskop ist deine astrologische Geburtskarte.\n"
    "Es zeigt die Planetenpositionen zu deiner Geburt.\n\n"
    "Für die Erstellung brauchen wir:\n"
    "  • Deinen Namen\n"
    "  • Geburtsdatum\n"
    "  • Geburtszeit\n"
    "  • Geburtsort"
)
NATAL_BTN_INPUT = "📝 Daten eingeben"
NATAL_ENTER_NAME = "🌟 GIB DEINEN NAMEN EIN\n\nZum Beispiel: Alexander\n\n/cancel — abbrechen"
NATAL_ENTER_DATE = (
    "📅 GIB DEIN GEBURTSDATUM EIN\n\n"
    "Formate:\n"
    "  • 15.05.1990\n"
    "  • 15/05/1990\n"
    "  • 1990-05-15\n\n"
    "/cancel — abbrechen"
)
NATAL_ENTER_TIME = (
    "⏰ GIB DEINE GEBURTSZEIT EIN\n\n"
    "Format: HH:MM\n"
    "Zum Beispiel: 14:30\n\n"
    "Wenn unbekannt — schreibe 12:00\n"
    "/cancel — abbrechen"
)
NATAL_ENTER_PLACE = "📍 GIB DEINEN GEBURTSORT EIN\n\nZum Beispiel: Berlin, Deutschland\n\n/cancel — abbrechen"
NATAL_NAME_SHORT = "❌ Name zu kurz. Mindestens 2 Zeichen."
NATAL_NAME_LONG = "❌ Name zu lang (max. 50 Zeichen)."
NATAL_CREATING = "🔮 Erstelle dein Geburtshoroskop...\n\nDas kann 20-30 Sekunden dauern."
NATAL_AI_ANALYZING = "🔮 Astrologe analysiert deine Karte..."
NATAL_SCHEME_CAPTION = "🔮 Geburtshoroskop-Schema"
NATAL_READY = "✨ Geburtshoroskop ist fertig!"
NATAL_NEED_BIRTH = "❌ Geburtsdaten erforderlich. Erstelle zuerst ein Horoskop."
NATAL_CANCELLED = "Abgebrochen"

# === Phase 2.2: PDF ===
PDF_MENU_TITLE = (
    "📄 PDF-BERICHTE\n\n"
    "Berichtstyp wählen:\n\n"
    "🔮 Geburtshoroskop — vollständige Analyse\n"
    "🌙 Persönliches Horoskop — heutige Prognose"
)
PDF_BTN_NATAL = "🔮 Geburtshoroskop"
PDF_BTN_HOROSCOPE = "🌙 Horoskop"
PDF_NEED_PROFILE = (
    "❌ Geburtsdaten für PDF erforderlich.\n\n"
    "Fülle dein Profil: Profil → Bearbeiten.\n"
    "Oder erstelle zuerst ein Geburtshoroskop."
)
PDF_CREATING_NATAL = "📄 Erstelle PDF Geburtshoroskop...\n\nDas kann 20-30 Sekunden dauern."
PDF_AI_ANALYZING = "🔮 Astrologe analysiert die Karte..."
PDF_CREATING = "📄 Erstelle PDF..."
PDF_CREATING_HORO = "🌙 Erstelle Horoskop-PDF..."
PDF_NATAL_CAPTION = "🔮 Geburtshoroskop: {name}"
PDF_HORO_CAPTION = "🌙 Horoskop für {name}"
PDF_CHOOSE_ACTION = "📌 Aktion wählen:"
PDF_DOWNLOAD_BTN = "📄 PDF herunterladen"

# === Phase 2.2.1: Sternzeichen ===
ZODIAC_ARIES = "Widder"
ZODIAC_TAURUS = "Stier"
ZODIAC_GEMINI = "Zwillinge"
ZODIAC_CANCER = "Krebs"
ZODIAC_LEO = "Löwe"
ZODIAC_VIRGO = "Jungfrau"
ZODIAC_LIBRA = "Waage"
ZODIAC_SCORPIO = "Skorpion"
ZODIAC_SAGITTARIUS = "Schütze"
ZODIAC_CAPRICORN = "Steinbock"
ZODIAC_AQUARIUS = "Wassermann"
ZODIAC_PISCES = "Fische"
ZODIAC_UNKNOWN = "Unbekannt"

# === Elemente ===
ELEM_FIRE = "Feuer"
ELEM_EARTH = "Erde"
ELEM_AIR = "Luft"
ELEM_WATER = "Wasser"

# === Qualitäten ===
QUAL_CARDINAL = "Kardinal"
QUAL_FIXED = "Fixiert"
QUAL_MUTABLE = "Veränderlich"

# === Planeten ===
PLANET_SUN = "Sonne"
PLANET_MOON = "Mond"
PLANET_MERCURY = "Merkur"
PLANET_VENUS = "Venus"
PLANET_MARS = "Mars"
PLANET_JUPITER = "Jupiter"
PLANET_SATURN = "Saturn"
PLANET_URANUS = "Uranus"
PLANET_NEPTUNE = "Neptun"
PLANET_PLUTO = "Pluto"

# === Geburtshoroskop ===
NATAL_TITLE = "GEBURTSHOROSKOP"
NATAL_HEADER_MAIN = "HAUPTMERKMALE"
NATAL_HEADER_PLANETS = "PLANETENPOSITIONEN"
NATAL_HEADER_HOUSES = "ASTROLOGISCHE HÄUSER"
NATAL_HEADER_AI = "ASTROLOGISCHE ANALYSE"
NATAL_LABEL_SUN = "Sonne im Zeichen"
NATAL_LABEL_ELEMENT = "Element"
NATAL_LABEL_QUALITY = "Qualität"
NATAL_LABEL_ASC = "Aszendent"
NATAL_LABEL_HOUSE = "Haus"
NATAL_LABEL_RETRO = "(rückläufig)"

# === PDF ===
PDF_NATAL_TITLE = "GEBURTSHOROSKOP"
PDF_HOROSCOPE_TITLE = "HOROSKOP"
PDF_LABEL_DATE = "Datum"
PDF_FOOTER = "Astrologie ist ein Werkzeug zur Selbsterkenntnis. Die Sterne zeigen den Weg, aber die Wahl liegt immer bei dir!"
PDF_FOOTER_CREATED = "Erstellt von AstroBot"
