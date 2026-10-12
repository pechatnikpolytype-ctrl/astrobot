"""Tarot card names RU/EN/DE (78 cards)."""

TAROT_NAMES = {
    # ===== MAJOR ARCANA =====
    "00_fool": {"ru": "Шут", "en": "The Fool", "de": "Der Narr"},
    "01_magician": {"ru": "Маг", "en": "The Magician", "de": "Der Magier"},
    "02_high_priestess": {"ru": "Жрица", "en": "The High Priestess", "de": "Die Hohepriesterin"},
    "03_empress": {"ru": "Императрица", "en": "The Empress", "de": "Die Herrscherin"},
    "04_emperor": {"ru": "Император", "en": "The Emperor", "de": "Der Herrscher"},
    "05_hierophant": {"ru": "Иерофант", "en": "The Hierophant", "de": "Der Hierophant"},
    "06_lovers": {"ru": "Влюблённые", "en": "The Lovers", "de": "Die Liebenden"},
    "07_chariot": {"ru": "Колесница", "en": "The Chariot", "de": "Der Wagen"},
    "08_strength": {"ru": "Сила", "en": "Strength", "de": "Die Kraft"},
    "09_hermit": {"ru": "Отшельник", "en": "The Hermit", "de": "Der Eremit"},
    "10_wheel": {"ru": "Колесо Фортуны", "en": "Wheel of Fortune", "de": "Das Rad des Schicksals"},
    "11_justice": {"ru": "Справедливость", "en": "Justice", "de": "Die Gerechtigkeit"},
    "12_hanged": {"ru": "Повешенный", "en": "The Hanged Man", "de": "Der Gehängte"},
    "13_death": {"ru": "Смерть", "en": "Death", "de": "Der Tod"},
    "14_temperance": {"ru": "Умеренность", "en": "Temperance", "de": "Die Mäßigkeit"},
    "15_devil": {"ru": "Дьявол", "en": "The Devil", "de": "Der Teufel"},
    "16_tower": {"ru": "Башня", "en": "The Tower", "de": "Der Turm"},
    "17_star": {"ru": "Звезда", "en": "The Star", "de": "Der Stern"},
    "18_moon": {"ru": "Луна", "en": "The Moon", "de": "Der Mond"},
    "19_sun": {"ru": "Солнце", "en": "The Sun", "de": "Die Sonne"},
    "20_judgement": {"ru": "Суд", "en": "Judgement", "de": "Das Gericht"},
    "21_world": {"ru": "Мир", "en": "The World", "de": "Die Welt"},

    # ===== WANDS (Жезлы) =====
    "wands_ace": {"ru": "Ас Жезлов", "en": "Ace of Wands", "de": "Ass der Stäbe"},
    "wands_02": {"ru": "Двойка Жезлов", "en": "Two of Wands", "de": "Zwei der Stäbe"},
    "wands_03": {"ru": "Тройка Жезлов", "en": "Three of Wands", "de": "Drei der Stäbe"},
    "wands_04": {"ru": "Четвёрка Жезлов", "en": "Four of Wands", "de": "Vier der Stäbe"},
    "wands_05": {"ru": "Пятёрка Жезлов", "en": "Five of Wands", "de": "Fünf der Stäbe"},
    "wands_06": {"ru": "Шестёрка Жезлов", "en": "Six of Wands", "de": "Sechs der Stäbe"},
    "wands_07": {"ru": "Семёрка Жезлов", "en": "Seven of Wands", "de": "Sieben der Stäbe"},
    "wands_08": {"ru": "Восьмёрка Жезлов", "en": "Eight of Wands", "de": "Acht der Stäbe"},
    "wands_09": {"ru": "Девятка Жезлов", "en": "Nine of Wands", "de": "Neun der Stäbe"},
    "wands_10": {"ru": "Десятка Жезлов", "en": "Ten of Wands", "de": "Zehn der Stäbe"},
    "wands_page": {"ru": "Паж Жезлов", "en": "Page of Wands", "de": "Bube der Stäbe"},
    "wands_knight": {"ru": "Рыцарь Жезлов", "en": "Knight of Wands", "de": "Ritter der Stäbe"},
    "wands_queen": {"ru": "Королева Жезлов", "en": "Queen of Wands", "de": "Königin der Stäbe"},
    "wands_king": {"ru": "Король Жезлов", "en": "King of Wands", "de": "König der Stäbe"},

    # ===== CUPS (Кубки) =====
    "cups_ace": {"ru": "Ас Кубков", "en": "Ace of Cups", "de": "Ass der Kelche"},
    "cups_02": {"ru": "Двойка Кубков", "en": "Two of Cups", "de": "Zwei der Kelche"},
    "cups_03": {"ru": "Тройка Кубков", "en": "Three of Cups", "de": "Drei der Kelche"},
    "cups_04": {"ru": "Четвёрка Кубков", "en": "Four of Cups", "de": "Vier der Kelche"},
    "cups_05": {"ru": "Пятёрка Кубков", "en": "Five of Cups", "de": "Fünf der Kelche"},
    "cups_06": {"ru": "Шестёрка Кубков", "en": "Six of Cups", "de": "Sechs der Kelche"},
    "cups_07": {"ru": "Семёрка Кубков", "en": "Seven of Cups", "de": "Sieben der Kelche"},
    "cups_08": {"ru": "Восьмёрка Кубков", "en": "Eight of Cups", "de": "Acht der Kelche"},
    "cups_09": {"ru": "Девятка Кубков", "en": "Nine of Cups", "de": "Neun der Kelche"},
    "cups_10": {"ru": "Десятка Кубков", "en": "Ten of Cups", "de": "Zehn der Kelche"},
    "cups_page": {"ru": "Паж Кубков", "en": "Page of Cups", "de": "Bube der Kelche"},
    "cups_knight": {"ru": "Рыцарь Кубков", "en": "Knight of Cups", "de": "Ritter der Kelche"},
    "cups_queen": {"ru": "Королева Кубков", "en": "Queen of Cups", "de": "Königin der Kelche"},
    "cups_king": {"ru": "Король Кубков", "en": "King of Cups", "de": "König der Kelche"},

    # ===== SWORDS (Мечи) =====
    "swords_ace": {"ru": "Ас Мечей", "en": "Ace of Swords", "de": "Ass der Schwerter"},
    "swords_02": {"ru": "Двойка Мечей", "en": "Two of Swords", "de": "Zwei der Schwerter"},
    "swords_03": {"ru": "Тройка Мечей", "en": "Three of Swords", "de": "Drei der Schwerter"},
    "swords_04": {"ru": "Четвёрка Мечей", "en": "Four of Swords", "de": "Vier der Schwerter"},
    "swords_05": {"ru": "Пятёрка Мечей", "en": "Five of Swords", "de": "Fünf der Schwerter"},
    "swords_06": {"ru": "Шестёрка Мечей", "en": "Six of Swords", "de": "Sechs der Schwerter"},
    "swords_07": {"ru": "Семёрка Мечей", "en": "Seven of Swords", "de": "Sieben der Schwerter"},
    "swords_08": {"ru": "Восьмёрка Мечей", "en": "Eight of Swords", "de": "Acht der Schwerter"},
    "swords_09": {"ru": "Девятка Мечей", "en": "Nine of Swords", "de": "Neun der Schwerter"},
    "swords_10": {"ru": "Десятка Мечей", "en": "Ten of Swords", "de": "Zehn der Schwerter"},
    "swords_page": {"ru": "Паж Мечей", "en": "Page of Swords", "de": "Bube der Schwerter"},
    "swords_knight": {"ru": "Рыцарь Мечей", "en": "Knight of Swords", "de": "Ritter der Schwerter"},
    "swords_queen": {"ru": "Королева Мечей", "en": "Queen of Swords", "de": "Königin der Schwerter"},
    "swords_king": {"ru": "Король Мечей", "en": "King of Swords", "de": "König der Schwerter"},

    # ===== PENTACLES (Пентакли) =====
    "pentacles_ace": {"ru": "Ас Пентаклей", "en": "Ace of Pentacles", "de": "Ass der Münzen"},
    "pentacles_02": {"ru": "Двойка Пентаклей", "en": "Two of Pentacles", "de": "Zwei der Münzen"},
    "pentacles_03": {"ru": "Тройка Пентаклей", "en": "Three of Pentacles", "de": "Drei der Münzen"},
    "pentacles_04": {"ru": "Четвёрка Пентаклей", "en": "Four of Pentacles", "de": "Vier der Münzen"},
    "pentacles_05": {"ru": "Пятёрка Пентаклей", "en": "Five of Pentacles", "de": "Fünf der Münzen"},
    "pentacles_06": {"ru": "Шестёрка Пентаклей", "en": "Six of Pentacles", "de": "Sechs der Münzen"},
    "pentacles_07": {"ru": "Семёрка Пентаклей", "en": "Seven of Pentacles", "de": "Sieben der Münzen"},
    "pentacles_08": {"ru": "Восьмёрка Пентаклей", "en": "Eight of Pentacles", "de": "Acht der Münzen"},
    "pentacles_09": {"ru": "Девятка Пентаклей", "en": "Nine of Pentacles", "de": "Neun der Münzen"},
    "pentacles_10": {"ru": "Десятка Пентаклей", "en": "Ten of Pentacles", "de": "Zehn der Münzen"},
    "pentacles_page": {"ru": "Паж Пентаклей", "en": "Page of Pentacles", "de": "Bube der Münzen"},
    "pentacles_knight": {"ru": "Рыцарь Пентаклей", "en": "Knight of Pentacles", "de": "Ritter der Münzen"},
    "pentacles_queen": {"ru": "Королева Пентаклей", "en": "Queen of Pentacles", "de": "Königin der Münzen"},
    "pentacles_king": {"ru": "Король Пентаклей", "en": "King of Pentacles", "de": "König der Münzen"},
}


def card_name(card_key: str, lang: str = "ru") -> str:
    """Returns localized card name."""
    entry = TAROT_NAMES.get(card_key)
    if not entry:
        return card_key
    return entry.get(lang, entry.get("ru", card_key))
