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

# === Phase 2.3: Tarot ===
TAROT_MENU_TITLE = (
    "TAROT \u2014 WAHRSAGEN UND RAT\n\n"
    "Stelle deine Frage \u2014 und die Tarotkarten antworten "
    "mit einer pers\u00f6nlichen Deutung vom Tarotleser.\n\n"
    "\U0001F4A1 Wie es funktioniert:\n"
    "1. Du schreibst eine Frage (Liebe, Arbeit, Zukunft)\n"
    "2. Wir ziehen 3 Karten\n"
    "3. Der Tarotleser gibt eine ausf\u00fchrliche Deutung\n\n"
    "\u26a0\ufe0f Dieselbe Frage am selben Tag \u2014 dieselbe Legung.\n"
    "Am n\u00e4chsten Tag \u2014 eine neue."
)
TAROT_BTN_NEW = "\U0001F52E Legung machen"
TAROT_BTN_MORE = "\U0001F52E Noch eine Legung"
TAROT_BTN_BUY = "\U0001F48E Abo kaufen"
TAROT_LOCK = "\n\n\U0001F512 Nur mit Abo verf\u00fcgbar."
TAROT_NOT_LOADED = "\u274c Karten nicht geladen"
TAROT_NEED_SUB = "\U0001F512 Abo erforderlich"
TAROT_ASK_Q = (
    "\U0001F52E STELLE DEINE FRAGE\n\n"
    "Schreibe die Frage, auf die du Antwort m\u00f6chtest.\n\n"
    "Beispiele:\n"
    "\u2022 Was erwartet mich in Beziehungen?\n"
    "\u2022 Soll ich den Job wechseln?\n"
    "\u2022 Was erwartet mich n\u00e4chsten Monat?\n\n"
    "/cancel \u2014 abbrechen"
)
TAROT_CANCELLED = "Abgebrochen."
TAROT_TOO_SHORT = "\u274c Frage zu kurz. Bitte erl\u00e4utern."
TAROT_PROCESSING = "\U0001F52E Karten mischen... 5-15 Sekunden."
TAROT_ERROR = "\u274c Fehler: {err}"
TAROT_AI_TITLE = "\U0001F916 DEUTUNG DES ASTROLOGEN"
TAROT_AI_CACHE = " (aus Cache)"
TAROT_WANT_MORE = "M\u00f6chtest du eine weitere Legung?"
TAROT_POS_PAST = "\U0001F550 Vergangenheit"
TAROT_POS_NOW = "\U0001F550 Gegenwart"
TAROT_POS_FUTURE = "\U0001F550 Zukunft"

# === Tarot positions (DE) ===
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

TAROT_LABEL_BLOCK = "Was blockiert"
TAROT_LABEL_HELP = "Was hilft"
TAROT_LABEL_PROSPECT = "Aussicht"
TAROT_LABEL_PAST = "Vergangenheit"
TAROT_LABEL_NOW = "Gegenwart"
TAROT_LABEL_FUTURE = "Zukunft"
TAROT_LABEL_WORRIES = "Was beunruhigt"
TAROT_LABEL_HELPS = "Was hilft"
TAROT_LABEL_NEAR = "Kurzfristig"
TAROT_LABEL_MID = "Mittelfristig"
TAROT_LABEL_FAR = "Langfristig"
TAROT_LABEL_ADVICE = "Rat"
TAROT_LABEL_TOTAL = "Ergebnis"

# === Phase 2.3B: Kompatibilit\u00e4t ===
COMPAT_MENU_TITLE = (
    "\U0001F495 KOMPATIBILIT\u00c4TSANALYSE\n\n"
    "Gib das Sternzeichen des ersten Partners ein:\n"
    "Zum Beispiel: Widder, Stier, L\u00f6we\n\n"
    "Oder gib ein Geburtsdatum im Format JJJJ-MM-TT ein.\n\n"
    "/cancel \u2014 abbrechen"
)
COMPAT_SUB_LOCK = (
    "\u274c Die Funktion \u00abKompatibilit\u00e4t\u00bb ist nur mit Abo verf\u00fcgbar.\n\n"
    "Abonniere, um sie zu nutzen."
)
COMPAT_SUB_LOCK_SHORT = "\u274c Nur mit Abo verf\u00fcgbar."
COMPAT_PARTNER1_NOT_RECOGNIZED = (
    "\u274c Sternzeichen nicht erkannt.\n\n"
    "Gib den Namen des Zeichens (Widder, Stier...) "
    "oder ein Datum im Format JJJJ-MM-TT ein."
)
COMPAT_PARTNER1_OK = "\u2705 Erster Partner: {sign}\n\nJetzt gib das Zeichen oder Datum des zweiten Partners ein:\n\n/cancel \u2014 abbrechen"
COMPAT_PARTNER2_NOT_RECOGNIZED = "\u274c Zeichen nicht erkannt. Versuche es erneut."
COMPAT_PROCESSING = "\U0001F52E Astrologe analysiert die Kompatibilit\u00e4t..."
COMPAT_CANCELLED = "Abgebrochen"
COMPAT_RESULT_TITLE = "\U0001F495 KOMPATIBILIT\u00c4TSANALYSE"
COMPAT_FALLBACK_LEVEL_IDEAL = "Ideale Kompatibilit\u00e4t"
COMPAT_FALLBACK_LEVEL_EXCELLENT = "Ausgezeichnete Kompatibilit\u00e4t"
COMPAT_FALLBACK_LEVEL_GOOD = "Gute Kompatibilit\u00e4t"
COMPAT_FALLBACK_LEVEL_MEDIUM = "Mittlere Kompatibilit\u00e4t"
COMPAT_FALLBACK_LEVEL_HARD = "Schwierige Kompatibilit\u00e4t"

# === Phase 2.3C: Horoskop ===
HOROSCOPE_PROCESSING = (
    "\U0001F305 Heutiges Horoskop wird erstellt...\n\n"
    "Das dauert 5-15 Sekunden."
)
HOROSCOPE_CACHE_LOG = "\U0001F305 Horoskop aus Cache"
HOROSCOPE_FALLBACK_TITLE = "\U0001F305 ASTROLOGISCHE PROGNOSE F\u00dcR HEUTE"
HOROSCOPE_FALLBACK_TEXT = (
    "\U0001F305 ALLGEMEINE PROGNOSE\n"
    "Heute stehen die Sterne in harmonischer Konstellation und schaffen g\u00fcnstige Energie.\n\n"
    "\U0001F4A1 RAT DES TAGES\n"
    "Vertraue deiner Intuition \u2014 sie ist heute besonders stark.\n\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
    "\U0001F52E Denk daran: Astrologie ist ein Leitfaden, kein Urteil."
)

# === Phase 2.4A: Profil ===
PROFILE_TITLE = "\U0001F464 DEIN PROFIL"
PROFILE_NOT_FOUND = "\u274c Profil nicht gefunden. Dr\u00fccke /start."
PROFILE_BTN_EDIT = "\u270f\ufe0f Bearbeiten"
PROFILE_BTN_NOTES = "\U0001F9E0 Notizen des Astrologen"
PROFILE_BTN_REFERRAL = "\U0001F517 Freund einladen"
PROFILE_LABEL_NAME = "Name"
PROFILE_LABEL_ZODIAC = "Sternzeichen"
PROFILE_LABEL_BIRTH_DATE = "Geburtsdatum"
PROFILE_LABEL_BIRTH_TIME = "Geburtszeit"
PROFILE_LABEL_BIRTH_PLACE = "Geburtsort"
PROFILE_LABEL_GENDER = "Geschlecht"
PROFILE_LABEL_BIO = "Bio"
PROFILE_LABEL_INTERESTS = "Interessen"
PROFILE_LABEL_GOALS = "Ziele"
PROFILE_LABEL_RELATIONSHIP = "Beziehung"
PROFILE_LABEL_STATUS = "Status"
PROFILE_LABEL_SUB_END = "Abo bis"
PROFILE_SECTION_MAIN = "\U0001F31F Haupt"
PROFILE_SECTION_ABOUT = "\U0001F4dd \u00dcber"
PROFILE_EMPTY = "Nicht angegeben"
PROFILE_EMPTY_BIO = "Nicht ausgef\u00fcllt"
PROFILE_STATUS_PREMIUM = "\U0001F48E Premium"
PROFILE_STATUS_FREE = "\U0001F193 Kostenlos"
PROFILE_NO_SUB = "Kein aktives"
PROFILE_AI_UNLIMITED = "\U0001F52E Fragen \u00fcbrig: \u267e\ufe0f unbegrenzt"
PROFILE_AI_LIMITED = "\U0001F52E Fragen \u00fcbrig: {usage}/{limit}"

PROFILE_EDIT_TITLE = "\u270f\ufe0f PROFIL BEARBEITEN"
PROFILE_EDIT_BTN_DATE = "\U0001F382 Geburtsdatum"
PROFILE_EDIT_BTN_TIME = "\u23f0 Geburtszeit"
PROFILE_EDIT_BTN_PLACE = "\U0001F4CD Geburtsort"
PROFILE_EDIT_BTN_GENDER = "\U0001F464 Geschlecht"
PROFILE_EDIT_BTN_BIO = "\U0001F4dd Bio"
PROFILE_EDIT_BTN_INTERESTS = "\U0001F3af Interessen"
PROFILE_EDIT_BTN_GOALS = "\U0001F3C6 Ziele"
PROFILE_EDIT_BTN_RELATIONSHIP = "\U0001F495 Beziehung"

PROFILE_ENTER_DATE = "\U0001F382 Geburtsdatum eingeben:\n\nFormate: 15.05.1990, 15/05/1990, 1990-05-15\n\n/cancel \u2014 abbrechen"
PROFILE_ENTER_TIME = "\u23f0 Zeit eingeben (HH:MM):\n\n/cancel \u2014 abbrechen"
PROFILE_ENTER_PLACE = "\U0001F4CD Geburtsort eingeben:\n\n/cancel \u2014 abbrechen"
PROFILE_ENTER_BIO = "\U0001F4dd Erz\u00e4hle \u00fcber dich (2-3 S\u00e4tze):\n\n/cancel \u2014 abbrechen"
PROFILE_ENTER_INTERESTS = "\U0001F3af Deine Interessen (kommagetrennt):\n\n/cancel \u2014 abbrechen"
PROFILE_ENTER_GOALS = "\U0001F3C6 Deine Ziele:\n\n/cancel \u2014 abbrechen"
PROFILE_SAVED = "\u2705 Gespeichert!"
PROFILE_SAVED_DATE = "\u2705 Datum aktualisiert: {date}"
PROFILE_SAVED_TIME = "\u2705 Zeit aktualisiert!"
PROFILE_SAVED_PLACE = "\u2705 Ort aktualisiert!"
PROFILE_SAVED_BIO = "\u2705 Bio aktualisiert!"
PROFILE_SAVED_INTERESTS = "\u2705 Interessen aktualisiert!"
PROFILE_SAVED_GOALS = "\u2705 Ziele aktualisiert!"
PROFILE_CANCELLED = "Abgebrochen"
PROFILE_ERR_FORMAT = "\u274c Ung\u00fcltiges Format"
PROFILE_ERR_TOO_SHORT = "\u274c Zu kurz"
PROFILE_ERR_MAX_500 = "\u274c Maximal 500 Zeichen"

PROFILE_GENDER_TITLE = "\U0001F464 GESCHLECHT W\u00c4HLEN"
PROFILE_GENDER_MALE = "\U0001F468 M\u00e4nnlich"
PROFILE_GENDER_FEMALE = "\U0001F469 Weiblich"
PROFILE_GENDER_NONE = "\U0001F6ab Nicht angeben"

PROFILE_REL_TITLE = "\U0001F495 BEZIEHUNGSSTATUS"
PROFILE_REL_SINGLE = "\U0001F49A Ledig"
PROFILE_REL_DATING = "\U0001F49B In einer Beziehung"
PROFILE_REL_MARRIED = "\U0001F48D Verheiratet"
PROFILE_REL_DIVORCED = "\U0001F494 Geschieden"
PROFILE_REL_NONE = "\U0001F6ab Nicht angeben"

PROFILE_REF_DISABLED = "\U0001F517 EMPFEHLUNGSPROGRAMM\n\nVor\u00fcbergehend nicht verf\u00fcgbar."
PROFILE_REF_TITLE = "\U0001F517 EMPFEHLUNGSPROGRAMM"
PROFILE_REF_INVITE = "\U0001F381 Lade einen Freund ein \u2014 beide bekommen {days} Tage Premium!"
PROFILE_REF_YOUR_LINK = "\U0001F4CE Dein Link:"
PROFILE_REF_STATS = "\U0001F4CA Statistik:"
PROFILE_REF_INVITED = "Eingeladen"
PROFILE_REF_BONUSES = "Boni erhalten"
PROFILE_REF_LEFT = "Boni \u00fcbrig"
PROFILE_REF_HOW = "\U0001F4A1 So funktioniert es:\n1. Sende den Link an einen Freund\n2. Freund registriert sich\n3. Beide bekommen {days} Tage Premium\n\n\u26a0\ufe0f Bonus nur f\u00fcr neue Nutzer."
PROFILE_REF_SHARE = "\U0001F4E4 Link teilen"
PROFILE_REF_SHARE_TEXT = "Probier diesen Astrologen aus!"
PROFILE_REF_BACK = "\U0001F519 Zur\u00fcck"

PROFILE_NOTES_TITLE = "\U0001F9E0 NOTIZEN DES ASTROLOGEN"
PROFILE_NOTES_EMPTY = "\U0001F9E0 NOTIZEN DES ASTROLOGEN\n\nNoch leer."
PROFILE_NOTES_ABOUT = "\U0001F9E0 NOTIZEN \u00dcBER DICH"
PROFILE_NOTES_BTN_DELETE = "\U0001F5D1\ufe0f L\u00f6schen"
PROFILE_NOTES_BTN_CLEAR = "\U0001F9F9 Leeren"
PROFILE_NOTES_BTN_BACK = "\U0001F519 Zur\u00fcck"
PROFILE_NOTES_NO = "Keine Notizen"
PROFILE_NOTES_CHOOSE = "Zum L\u00f6schen ausw\u00e4hlen:"
PROFILE_NOTES_DELETED = "\u2705 Gel\u00f6scht"
PROFILE_NOTES_CLEAR_CONFIRM = "\U0001F9F9 ALLE Notizen l\u00f6schen?"
PROFILE_NOTES_YES = "\u2705 Ja"
PROFILE_NOTES_NO_BTN = "\u274c Nein"
PROFILE_NOTES_CLEARED = "\u2705 Notizen gel\u00f6scht"

# === Phase 2.4B: Stimmungstagebuch ===
MOOD_TITLE = "\U0001F4D4 STIMMUNGSTAGEBUCH"
MOOD_ASK = "Wie ist deine Stimmung heute?"
MOOD_TODAY_SET = "Heute markiert: {emoji} {name}"
MOOD_TODAY_NOT_SET = "Du hast deine Stimmung heute noch nicht markiert."
MOOD_SELECT_PROMPT = "W\u00e4hle deine Stimmung oder sieh dir die Statistik an:"

MOOD_5_NAME = "Ausgezeichnet"
MOOD_4_NAME = "Gut"
MOOD_3_NAME = "Okay"
MOOD_2_NAME = "Schlecht"
MOOD_1_NAME = "Schrecklich"
MOOD_5_BTN = "\U0001F60A Ausgezeichnet"
MOOD_4_BTN = "\U0001F642 Gut"
MOOD_3_BTN = "\U0001F610 Okay"
MOOD_2_BTN = "\U0001F614 Schlecht"
MOOD_1_BTN = "\U0001F622 Schrecklich"

MOOD_Q_5 = "\U0001F31F Super! Erz\u00e4hl, was Gutes passiert ist?"
MOOD_Q_4 = "\U0001F60A Sch\u00f6n! Was hat dich heute gefreut?"
MOOD_Q_3 = "\U0001F914 Was ist los? Erz\u00e4hlst du?"
MOOD_Q_2 = "\U0001F499 Was ist passiert? Ich h\u00f6re zu."
MOOD_Q_1 = "\U0001FAC2 Es tut mir leid, dass es dir schwer f\u00e4llt. M\u00f6chtest du teilen?"
MOOD_Q_DEFAULT = "Erz\u00e4hlst du?"

MOOD_BTN_STATS = "\U0001F4CA Statistik"
MOOD_BTN_CHART = "\U0001F4C8 Diagramm"
MOOD_BTN_SKIP = "\u23ed\ufe0f \u00dcberspringen"
MOOD_BTN_DIARY = "\U0001F4D4 Tagebuch"
MOOD_BTN_TALK = "\U0001F4AC Mit Astrologe sprechen"

MOOD_SAVED = "\u2705 Stimmung gespeichert: {emoji} {name}"
MOOD_WRITE_OR_SKIP = "Du kannst ein paar Worte schreiben oder \u00fcberspringen."
MOOD_STREAK_NOTE = "\n\n\U0001F499 \u00dcbrigens ist das schon Tag {n} in Folge. Was ist los?"

MOOD_SKIP_OK_TALK = "Okay. Wenn du reden m\u00f6chtest \u2014 ich bin da \U0001F499"
MOOD_SKIP_OK = "Sch\u00f6n! Bis morgen \U0001F31F"
MOOD_CANCELLED = "Okay. Bis bald!"
MOOD_TOO_SHORT = "Erz\u00e4hl etwas mehr oder tippe \u00ab\u23ed\ufe0f \u00dcberspringen\u00bb."

MOOD_PROCESSING = "\U0001F52E Astrologe verarbeitet deine Geschichte..."
MOOD_ERROR = "\u274c Ein Fehler ist aufgetreten. Versuche es erneut."
MOOD_GOOD_DAY = "Hab einen guten Tag! \U0001F31F"
MOOD_AI_PREFIX = "\U0001F916"

MOOD_STATS_TITLE = "\U0001F4CA STATISTIK"
MOOD_STATS_EMPTY = "\U0001F4CA STATISTIK\n\nNoch keine Eintr\u00e4ge. Markiere deine Stimmung!"
MOOD_STATS_TITLE_7 = "\U0001F4CA STATISTIK F\u00dcR 7 TAGE"
MOOD_STATS_AVG = "Durchschnitt"
MOOD_STATS_COUNT = "Eintr\u00e4ge"
MOOD_STATS_CHART_NEED = "Mindestens 2 Eintr\u00e4ge f\u00fcr ein Diagramm."
MOOD_CHART_BUILDING = "\U0001F4C8 Diagramm wird erstellt..."
MOOD_CHART_FAIL = "\u274c Diagramm konnte nicht erstellt werden."
MOOD_CHART_CAPTION = "\U0001F4C8 Stimmung \u00fcber 30 Tage"
MOOD_CHART_WHAT_NEXT = "Was als N\u00e4chstes?"

MOOD_FACTS_HEADER = "\u2728 Astrologe m\u00f6chte sich an dich erinnern:\n\nTippe auf einen Fakt zum Aus-/Abw\u00e4hlen.\nDann tippe \u00ab\U0001F4BE Speichern\u00bb."
MOOD_FACTS_SAVE = "\U0001F4BE Speichern"
MOOD_FACTS_SKIP = "\u274c Nein, danke"
MOOD_FACTS_SAVED = "\u2705 {n} Fakt(en) gespeichert.\n\nAnsehen: \U0001F464 Profil \u2192 \U0001F9E0 Notizen des Astrologen."
MOOD_FACTS_CANCELLED = "\u274c Fakten nicht gespeichert."

MOOD_LIMIT_TITLE = "\u26a0\ufe0f FRAGEN-LIMIT ERREICHT"
MOOD_LIMIT_DESC = "Du hast heute {usage}/{limit} Fragen gestellt.\nLimit wird um 00:00 UTC zur\u00fcckgesetzt.\n\n\U0001F48E Kaufe Premium \u2014 100 Anfragen/Tag.\n\nDeine Stimmung ist gespeichert \U0001F31F"
MOOD_LIMIT_BUY = "\U0001F48E Premium kaufen"

# === Phase 2.4C: AI-Fragen ===
AI_MENU_TITLE = "\U0001F52E ASTROLOGE"
AI_MENU_DESC = "Stelle jede Frage zu Horoskopen, Sternzeichen, Kompatibilit\u00e4t oder Planeten!"
AI_MENU_EXAMPLES = (
    "\U0001F4DD Beispiele:\n"
    "  \u2022 Was erwartet Widder diese Woche?\n"
    "  \u2022 Wie ist die Kompatibilit\u00e4t von L\u00f6we und Skorpion?\n"
    "  \u2022 Wie wirkt sich der r\u00fcckl\u00e4ufige Merkur auf mich aus?"
)
AI_MENU_PROFILE_NOTE = "\U0001F4A1 Der Astrologe kennt dein Profil und antwortet pers\u00f6nlich!"
AI_MENU_DIALOG_NOTE = (
    "\U0001F4AC Nach der Antwort kannst du weitere Fragen stellen "
    "ohne Tasten zu dr\u00fccken \u2014 schreib einfach.\n"
    "Wenn du fertig bist \u2014 tippe \u00ab\U0001F51A Dialog beenden\u00bb."
)
AI_MENU_LIMIT_UNLIMITED = "\U0001F52E Fragen \u00fcbrig: \u267e\ufe0f unbegrenzt"
AI_MENU_LIMIT = "\U0001F52E Fragen \u00fcbrig: {left}/{limit}"

AI_LIMIT_TITLE = "\u26a0\ufe0f FRAGEN-LIMIT ERREICHT"
AI_LIMIT_DESC = "Du hast heute {usage}/{limit} Fragen gestellt.\nLimit wird um 00:00 UTC zur\u00fcckgesetzt.\n\n\U0001F48E Kaufe Premium \u2014 100 Anfragen/Tag."
AI_LIMIT_BUY = "\U0001F48E Premium kaufen"

AI_ASK = (
    "\U0001F52E STELLE DEINE FRAGE\n\n"
    "Schreibe eine astrologische Frage.\n\n"
    "\U0001F4AC Du kannst mehrere Fragen hintereinander stellen \u2014 schreib einfach.\n"
    "Wenn du fertig bist \u2014 tippe \u00ab\U0001F51A Dialog beenden\u00bb.\n\n"
    "/cancel \u2014 abbrechen"
)
AI_ASK_SHORT = "\U0001F52E STELLE DEINE FRAGE\n\n/cancel \u2014 abbrechen"

AI_CANCELLED = "Dialog beendet."
AI_PROCESSING = "\U0001F52E Astrologe analysiert deine Frage..."
AI_THINKING = "\U0001F52E Astrologe denkt nach...\n\nDas kann 10-30 Sekunden dauern.\nBitte warten."
AI_ERROR = "\u274c Ein Fehler ist aufgetreten. Versuche es sp\u00e4ter."
AI_ANSWER_TITLE = "\U0001F916 ANTWORT DES ASTROLOGEN:"
AI_ANSWER_HINT = "\U0001F4AC Du kannst die n\u00e4chste Frage stellen oder \u00ab\U0001F51A Dialog beenden\u00bb tippen."
AI_ANSWER_MODEL = "\U0001F916 Modell: {model}"
AI_LEFT_5 = "\u26a0\ufe0f Du hast heute {left} Anfragen \u00fcbrig."
AI_LEFT_0 = "\u26a0\ufe0f Fragen-Limit f\u00fcr heute erreicht."
AI_ENDED = "\u2705 Dialog beendet.\n\nKomm zur\u00fcck, wenn du Fragen hast! \U0001F31F"
AI_ENDED_SHORT = "\u2705 Dialog beendet."

AI_FACTS_TITLE = "\u2728 ASTROLOGE M\u00d6CHTE SICH AN DICH ERINNERN"
AI_FACTS_HINT = "Tippe auf einen Fakt zum Aus-/Abw\u00e4hlen.\nDann tippe \u00ab\U0001F4BE Speichern\u00bb."
AI_FACTS_SAVE = "\U0001F4BE Speichern"
AI_FACTS_SKIP = "\u274c Nein, danke"
AI_FACTS_SAVED = "\u2705 {n} Fakt(en) gespeichert.\n\nAnsehen: \U0001F464 Profil \u2192 \U0001F9E0 Notizen des Astrologen."
AI_FACTS_NOTHING = "\u274c Nichts gespeichert."
AI_FACTS_CANCELLED = "\u274c Fakten nicht gespeichert."
AI_FACTS_ALREADY = "\u2705 Astrologe hat bemerkt, dass du schon davon erz\u00e4hlt hast."
AI_FILL_PROFILE_NOTE = "\U0001F4A1 M\u00f6chtest du, dass der Astrologe dich besser kennt?\n\nF\u00fclle das Profil aus \u2014 die Antworten werden genauer."
AI_FILL_PROFILE_BTN = "\U0001F464 Profil ausf\u00fcllen"

AI_EXAMPLES_TEXT = (
    "\U0001F4DD FRAGEBEISPIELE\n\n"
    "\U0001F52E \u00dcber Horoskop:\n"
    "  \u2022 Was erwartet mich diese Woche?\n"
    "  \u2022 Welcher Tag ist der beste f\u00fcr wichtige Dinge?\n\n"
    "\U0001F495 \u00dcber Liebe:\n"
    "  \u2022 Passt ein Skorpion-Partner zu mir?\n"
    "  \u2022 Wie verbessere ich Beziehungen?\n\n"
    "\U0001F4BC \u00dcber Karriere:\n"
    "  \u2022 Soll ich den Job wechseln?\n"
    "  \u2022 Welcher Beruf passt zu mir?\n\n"
    "\U0001F31F \u00dcber mich:\n"
    "  \u2022 Was sagt mein Geburtshoroskop?\n"
    "  \u2022 Was sind meine St\u00e4rken?\n\n"
    "\u2728 Stelle deine Fragen!"
)
