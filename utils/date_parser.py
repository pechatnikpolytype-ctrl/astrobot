"""Универсальный парсер дат — принимает популярные форматы."""
import logging
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


# Поддерживаемые форматы (порядок важен — сначала популярные)
SUPPORTED_FORMATS = [
    "%d.%m.%Y",    # 15.05.1990
    "%d/%m/%Y",    # 15/05/1990
    "%d-%m-%Y",    # 15-05-1990
    "%Y-%m-%d",    # 1990-05-15 (ISO)
    "%d.%m.%y",    # 15.05.90
    "%d/%m/%y",    # 15/05/90
    "%d-%m-%y",    # 15-05-90
    "%Y/%m/%d",    # 1990/05/15
]


def parse_date(text: str) -> Tuple[bool, Optional[str], str]:
    """
    Парсит дату из строки.

    Возвращает:
        (успех, дата_в_ISO, сообщение_об_ошибке)

    Дата возвращается в формате ГГГГ-ММ-ДД (для БД).
    """
    if not text or not text.strip():
        return False, None, "Дата не может быть пустой"

    cleaned = text.strip().replace(",", ".").replace(" ", "")

    for fmt in SUPPORTED_FORMATS:
        try:
            date_obj = datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

        # Проверки
        if date_obj.year < 1900:
            return False, None, "Дата слишком ранняя (год < 1900)"

        if date_obj > datetime.now():
            return False, None, "Дата не может быть в будущем"

        age = (datetime.now() - date_obj).days / 365.25
        if age > 120:
            return False, None, "Возраст не может быть больше 120 лет"
        if age < 0:
            return False, None, "Некорректная дата"

        # Возвращаем в ISO
        return True, date_obj.strftime("%Y-%m-%d"), ""

    # Не удалось распознать
    return False, None, (
        "Неверный формат даты.\n\n"
        "Поддерживаемые форматы:\n"
        "  • ДД.ММ.ГГГГ  (15.05.1990)\n"
        "  • ДД/ММ/ГГГГ  (15/05/1990)\n"
        "  • ДД-ММ-ГГГГ  (15-05-1990)\n"
        "  • ГГГГ-ММ-ДД  (1990-05-15)"
    )


def format_date_for_display(iso_date: str) -> str:
    """Преобразует ISO дату (ГГГГ-ММ-ДД) в ДД.ММ.ГГГГ для показа."""
    try:
        date_obj = datetime.strptime(iso_date, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except Exception:
        return iso_date
