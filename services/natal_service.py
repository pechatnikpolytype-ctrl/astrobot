import logging
import uuid
import os
import hashlib
import httpx
import math
import random
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

from astrology_calculator import AstrologyCalculator, sign_display, element_display, quality_display, planet_display
from locales import t
from database.postgres_db import get_natal_cache, set_natal_cache

from services.geocode import resolve_birth_place
from services.local_astro import calculate_natal_local, to_chart_data
logger = logging.getLogger(__name__)


# ============================================================
# СПРАВОЧНИКИ
# ============================================================
SIGNS_SHORT = {
    "Овен": "Ов", "Телец": "Тл", "Близнецы": "Бл", "Рак": "Рк",
    "Лев": "Лв", "Дева": "Дв", "Весы": "Вс", "Скорпион": "Ск",
    "Стрелец": "Ст", "Козерог": "Кз", "Водолей": "Вд", "Рыбы": "Рб",
    "Неизвестно": "?",
}

SIGNS_FULL = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]

ELEMENTS = {
    "Овен": "Огонь", "Лев": "Огонь", "Стрелец": "Огонь",
    "Телец": "Земля", "Дева": "Земля", "Козерог": "Земля",
    "Близнецы": "Воздух", "Весы": "Воздух", "Водолей": "Воздух",
    "Рак": "Вода", "Скорпион": "Вода", "Рыбы": "Вода",
}

QUALITIES = {
    "Овен": "Кардинальный", "Рак": "Кардинальный",
    "Весы": "Кардинальный", "Козерог": "Кардинальный",
    "Телец": "Фиксированный", "Лев": "Фиксированный",
    "Скорпион": "Фиксированный", "Водолей": "Фиксированный",
    "Близнецы": "Мутабельный", "Дева": "Мутабельный",
    "Стрелец": "Мутабельный", "Рыбы": "Мутабельный",
}

SHORT_INTERPRETATIONS = {
    "Овен": "Вы обладаете лидерскими качествами, энергичны и инициативны.",
    "Телец": "Вы практичны, терпеливы и надёжны.",
    "Близнецы": "Вы любознательны, общительны и быстро адаптируетесь.",
    "Рак": "Вы эмоциональны, заботливы и интуитивны.",
    "Лев": "Вы творческая, щедрая и уверенная в себе личность.",
    "Дева": "Вы аналитичны, внимательны к деталям и трудолюбивы.",
    "Весы": "Вы дипломатичны, обаятельны и стремитесь к гармонии.",
    "Скорпион": "Вы страстны, проницательны и обладаете сильной волей.",
    "Стрелец": "Вы оптимистичны, свободолюбивы и стремитесь к познанию.",
    "Козерог": "Вы дисциплинированы, ответственны и амбициозны.",
    "Водолей": "Вы оригинальны, независимы и гуманистичны.",
    "Рыбы": "Вы сострадательны, творческие и интуитивные.",
}


class NatalService:

    CITY_COORDS = {
        "минск": (53.9045, 27.5615, "Europe/Minsk"),
        "москва": (55.7558, 37.6173, "Europe/Moscow"),
        "киев": (50.4501, 30.5234, "Europe/Kiev"),
        "санкт-петербург": (59.9343, 30.3351, "Europe/Moscow"),
        "новосибирск": (55.0084, 82.9357, "Asia/Novosibirsk"),
        "екатеринбург": (56.8389, 60.6057, "Asia/Yekaterinburg"),
        "казань": (55.7887, 49.1221, "Europe/Moscow"),
        "самара": (53.1959, 50.1002, "Europe/Samara"),
        "омск": (54.9885, 73.3242, "Asia/Omsk"),
        "челябинск": (55.1644, 61.4368, "Asia/Yekaterinburg"),
        "ростов-на-дону": (47.2357, 39.7015, "Europe/Moscow"),
        "уфа": (54.7388, 55.9721, "Asia/Yekaterinburg"),
        "волгоград": (48.708, 44.5133, "Europe/Moscow"),
        "пермь": (58.0105, 56.2294, "Asia/Yekaterinburg"),
        "красноярск": (56.0097, 92.7917, "Asia/Krasnoyarsk"),
        "воронеж": (51.6605, 39.2003, "Europe/Moscow"),
        "варшава": (52.2297, 21.0122, "Europe/Warsaw"),
        "вильнюс": (54.6872, 25.2797, "Europe/Vilnius"),
        "рига": (56.9496, 24.1052, "Europe/Riga"),
        "таллин": (59.437, 24.7536, "Europe/Tallinn"),
        "берлин": (52.52, 13.405, "Europe/Berlin"),
        "париж": (48.8566, 2.3522, "Europe/Paris"),
        "лондон": (51.5074, -0.1278, "Europe/London"),
    }

    VEDASTRO_API_KEY = "sk-vedastro-2026"  # Заглушка
    VEDASTRO_BASE_URL = "https://vedastro.org/api/Calculate"

    def __init__(self):
        logger.info("✅ VedAstro сервис инициализирован")

    # ============================================================
    # КООРДИНАТЫ
    # ============================================================
    def get_coordinates(self, place: str) -> Tuple[float, float, str]:
        place_lower = place.lower().strip()
        for city, coords in self.CITY_COORDS.items():
            if city in place_lower or place_lower in city:
                return coords
        words = place_lower.split()
        for word in words:
            for city, coords in self.CITY_COORDS.items():
                if city in word or word in city:
                    return coords
        return 55.7558, 37.6173, "Europe/Moscow"

    # ============================================================
    # ВАЛИДАЦИЯ
    # ============================================================
    def validate_date(self, date_str: str) -> Tuple[bool, Optional[Tuple[int, int, int]], str]:
        """Валидирует дату — поддерживает ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ГГГГ-ММ-ДД и др."""
        from utils.date_parser import parse_date
        ok, iso_date, err = parse_date(date_str)
        if not ok:
            return False, None, err
        try:
            birth_date = datetime.strptime(iso_date, "%Y-%m-%d")
            return True, (birth_date.year, birth_date.month, birth_date.day), ""
        except Exception as e:
            return False, None, str(e)

    def validate_time(self, time_str: str) -> Tuple[bool, Optional[Tuple[int, int]], str]:
        try:
            if not time_str or time_str.lower() == "/skip":
                return True, (12, 0), ""
            hour, minute = map(int, time_str.split(":"))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return True, (hour, minute), ""
            return False, None, "Часы 0-23, минуты 0-59"
        except Exception:
            return False, None, "Формат: ЧЧ:ММ"

    def validate_place(self, place: str) -> Tuple[bool, str, str]:
        if not place or not place.strip():
            return False, "", "Место не может быть пустым"
        cleaned = place.strip()
        if len(cleaned) < 2:
            return False, "", "Слишком короткое название"
        return True, cleaned, ""

    # ============================================================
    # VEDASTRO API
    # ============================================================
    async def _fetch_planet_data(self, planet_name: str, lat: float, lon: float,
                                   year: int, month: int, day: int,
                                   hour: int, minute: int, tz: str) -> Optional[Dict]:
        try:
            url = f"{self.VEDASTRO_BASE_URL}/PlanetName/{planet_name}/Location/UserCity/Time/{hour:02d}:{minute:02d}/{day:02d}/{month:02d}/{year}/{tz}"
            headers = {"X-API-Key": self.VEDASTRO_API_KEY}
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return {
                            "sign": data.get("Sign", {}).get("Name", "Неизвестно"),
                            "house": data.get("House", "?"),
                            "retrograde": data.get("Retrograde", False),
                        }
                    except Exception:
                        return None
                return None
        except Exception as e:
            logger.error(f"Ошибка {planet_name}: {e}")
            return None

    # ============================================================
    # СОЗДАНИЕ НАТАЛЬНОЙ КАРТЫ
    # ============================================================
    async def create_natal_chart(self, name: str, birth_date: str,
                                  birth_time: str, birth_place: str) -> Dict[str, Any]:
        logger.info("Создание натальной карты (Kerykeion) для " + name)
        valid_date, date_parts, date_err = self.validate_date(birth_date)
        if not valid_date:
            raise ValueError(date_err)
        valid_time, time_parts, time_err = self.validate_time(birth_time)
        if not valid_time:
            raise ValueError(time_err)
        valid_place, place_clean, place_err = self.validate_place(birth_place)
        if not valid_place:
            raise ValueError(place_err)
        year, month, day = date_parts
        hour, minute = time_parts if time_parts else (12, 0)
        lat, lng, tz_str = await resolve_birth_place(place_clean)
        if lat is None:
            lat, lng, tz_str = self.get_coordinates(place_clean)
            logger.warning("geocode miss " + place_clean)
        result = calculate_natal_local(
            name=name, year=year, month=month, day=day, hour=hour, minute=minute,
            lat=lat, lng=lng, tz_str=tz_str,
        )
        chart_data = to_chart_data(
            result, name=name, date=birth_date,
            time="%02d:%02d" % (hour, minute), place=place_clean,
        )
        return chart_data

    def _get_demo_sign(self, planet: str, year: int, month: int, day: int) -> str:
        seed = int(hashlib.md5(f"{planet}{year}{month}{day}".encode()).hexdigest()[:8], 16)
        return SIGNS_FULL[seed % 12]

    # ============================================================
    # SVG-СХЕМА (без астрологических символов!)
    # ============================================================
    def generate_svg_chart(self, chart_data: Dict[str, Any], lang: str = "ru") -> Optional[str]:
        """Генерирует SVG-схему натальной карты без символов-заменителей."""
        try:
            k_svg = chart_data.get('_kerykeion_svg')
            if k_svg and os.path.exists(k_svg):
                return k_svg
            svg_filename = f"natal_chart_{uuid.uuid4().hex}.svg"
            info = chart_data["birth_info"]
            asc = chart_data["ascendant"]
            planets = chart_data["planets"]

            # Углы планет
            planet_angles = []
            for idx, p in enumerate(planets):
                try:
                    sign_idx = SIGNS_FULL.index(p["sign"])
                except ValueError:
                    sign_idx = 0
                base_angle = sign_idx * 30
                offset = (idx * 6) % 30
                angle = base_angle + offset - 90
                planet_angles.append((angle, p["name"], p["sign"]))

            svg = []
            svg.append('<svg width="800" height="800" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">')
            svg.append('<rect width="800" height="800" fill="#1a2a3a"/>')

            # Звёзды
            random.seed(hash(info["name"]))
            for _ in range(80):
                x = random.randint(20, 780)
                y = random.randint(20, 780)
                svg.append(f'<circle cx="{x}" cy="{y}" r="1" fill="#FFFFFF" opacity="0.5"/>')
            random.seed()

            # Круги
            svg.append('<circle cx="400" cy="400" r="350" fill="none" stroke="#c9a959" stroke-width="2"/>')
            svg.append('<circle cx="400" cy="400" r="280" fill="none" stroke="#c9a959" stroke-width="1.5"/>')
            svg.append('<circle cx="400" cy="400" r="200" fill="none" stroke="#c9a959" stroke-width="1"/>')
            svg.append('<circle cx="400" cy="400" r="100" fill="none" stroke="#c9a959" stroke-width="0.5"/>')

            # Линии-сектора
            for angle in range(0, 360, 30):
                rad = math.radians(angle - 90)
                x2 = 400 + 350 * math.cos(rad)
                y2 = 400 + 350 * math.sin(rad)
                svg.append(f'<line x1="400" y1="400" x2="{x2}" y2="{y2}" stroke="#c9a959" stroke-width="1" opacity="0.4"/>')

            # Сокращения знаков - на нужном языке
            for i, full_sign in enumerate(SIGNS_FULL):
                display = sign_display(full_sign, lang)
                short = display[:2]
                angle = (i * 30) - 90 + 15
                rad = math.radians(angle)
                r = 320
                x = 400 + r * math.cos(rad)
                y = 400 + r * math.sin(rad) + 6
                svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" fill="#FFD700" font-size="16" font-family="DejaVu Sans, Arial" font-weight="bold">{short}</text>')

            # Номера домов
            for i in range(1, 13):
                angle = (i * 30) - 90 + 15
                rad = math.radians(angle)
                r = 370
                x = 400 + r * math.cos(rad)
                y = 400 + r * math.sin(rad) + 5
                svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" fill="#E0E0E0" font-size="14" font-weight="bold" font-family="DejaVu Sans, Arial">{i}</text>')

            # Планеты (полные названия)
            for angle, name, sign in planet_angles:
                rad = math.radians(angle)
                r = 240
                x = 400 + r * math.cos(rad)
                y = 400 + r * math.sin(rad)
                svg.append(f'<circle cx="{x}" cy="{y}" r="20" fill="#1a2a3a" stroke="#FBBF24" stroke-width="2"/>')
                # Первые 3 буквы названия
                short_name = planet_display(name, lang)[:3]
                svg.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" fill="#FBBF24" font-size="14" font-family="DejaVu Sans, Arial" font-weight="bold">{short_name}</text>')

            # Асцендент
            try:
                asc_angle = SIGNS_FULL.index(asc) * 30 - 90
                rad_asc = math.radians(asc_angle)
                r_asc = 280
                x_asc = 400 + r_asc * math.cos(rad_asc)
                y_asc = 400 + r_asc * math.sin(rad_asc)
                svg.append(f'<circle cx="{x_asc}" cy="{y_asc}" r="16" fill="#FFD700" stroke="#FFFFFF" stroke-width="2"/>')
                svg.append(f'<text x="{x_asc}" y="{y_asc+5}" text-anchor="middle" fill="#1a2a3a" font-size="11" font-weight="bold" font-family="DejaVu Sans, Arial">{t("NATAL_LABEL_ASC", lang)[:3]}</text>')
            except Exception:
                pass

            # Заголовки
            svg.append(f'<text x="400" y="45" text-anchor="middle" fill="#FFD700" font-size="22" font-weight="bold" font-family="DejaVu Sans, Arial">{t("NATAL_TITLE", lang)}</text>')
            svg.append(f'<text x="400" y="75" text-anchor="middle" fill="#FFFFFF" font-size="16" font-family="DejaVu Sans, Arial">{info["name"]}</text>')
            svg.append(f'<text x="400" y="100" text-anchor="middle" fill="#c9a959" font-size="12" font-family="DejaVu Sans, Arial">{info["date"]} {info["time"]} | {info["place"]}</text>')
            svg.append(f'<text x="400" y="760" text-anchor="middle" fill="#FFD700" font-size="13" font-family="DejaVu Sans, Arial">{t("NATAL_LABEL_ASC", lang)}: {sign_display(asc, lang)}</text>')

            svg.append("</svg>")
            content = "".join(svg)

            with open(svg_filename, "w", encoding="utf-8") as f:
                f.write(content)
            return svg_filename

        except Exception as e:
            logger.error(f"Ошибка генерации SVG: {e}")
            return None

    # ============================================================
    # ТЕКСТОВЫЙ ОТЧЁТ (без markdown и символов)
    # ============================================================
    def generate_report_text(self, chart_data: Dict[str, Any], lang: str = "ru") -> str:
        """Text report with translation."""
        lines = []
        info = chart_data["birth_info"]

        lines.append(t("NATAL_TITLE", lang))
        lines.append(f"{info['name']}")
        date_in = "in" if lang == "en" else ("am" if lang == "de" else "\u0432")
        lines.append(f"{info['date']} {date_in} {info['time']}")
        lines.append(f"{info['place']}")
        lines.append("")

        lines.append(t("NATAL_HEADER_MAIN", lang))
        lines.append(f"\u2022 {t('NATAL_LABEL_SUN', lang)}: {sign_display(chart_data['sun_sign'], lang)}")
        lines.append(f"\u2022 {t('NATAL_LABEL_ELEMENT', lang)}: {element_display(chart_data['element'], lang)}")
        lines.append(f"\u2022 {t('NATAL_LABEL_QUALITY', lang)}: {quality_display(chart_data['quality'], lang)}")
        lines.append(f"\u2022 {t('NATAL_LABEL_ASC', lang)}: {sign_display(chart_data['ascendant'], lang)}")
        lines.append("")

        lines.append(t("NATAL_HEADER_PLANETS", lang))
        for pl in chart_data["planets"]:
            retro = f" {t('NATAL_LABEL_RETRO', lang)}" if pl.get("retrograde") else ""
            pl_name = planet_display(pl['name'], lang)
            pl_sign = sign_display(pl['sign'], lang)
            lines.append(f"\u2022 {pl_name}: {pl_sign} ({pl['house']} {t('NATAL_LABEL_HOUSE', lang)}){retro}")
        lines.append("")

        lines.append(t("NATAL_HEADER_HOUSES", lang))
        for h in chart_data["houses"]:
            lines.append(f"\u2022 {h['number']} {t('NATAL_LABEL_HOUSE', lang)}: {sign_display(h['sign'], lang)}")
        lines.append("")

        return "\n".join(lines)
    # ============================================================
    # AI-ИНТЕРПРЕТАЦИЯ
    # ============================================================
    async def generate_ai_report(self, chart_data: Dict[str, Any], lang: str = "ru") -> Optional[str]:
        """AI interpretation with cache. lang affects cache key."""
        try:
            info = chart_data.get("birth_info", {})
            cache_key_raw = f"{info.get('name','')}_{info.get('date','')}_{info.get('time','')}_{info.get('place','')}_{lang}"
            cache_key = hashlib.md5(cache_key_raw.encode()).hexdigest()[:16]

            cached = await get_natal_cache(cache_key)
            if cached and cached.get("text"):
                logger.info(f"[CACHE] AI interpretation: {cache_key}")
                return cached["text"]

            from ai_service_n1n import ai_service
            try:
                text = await ai_service.generate_natal_interpretation(chart_data, lang=lang)
            except TypeError:
                text = await ai_service.generate_natal_interpretation(chart_data)

            if not text:
                return None

            await set_natal_cache(cache_key, text)
            return text

        except Exception as e:
            logger.error(f"AI interpretation error: {e}")
            return None
    # ============================================================
    # ГЛАВНЫЙ МЕТОД: полный отчёт с AI
    # ============================================================
    async def generate_full_report(self, chart_data: Dict[str, Any], lang: str = "ru") -> str:
        """Full report: text + AI."""
        base = self.generate_report_text(chart_data, lang=lang)
        ai_text = await self.generate_ai_report(chart_data, lang=lang)

        if ai_text:
            return base + f"\n\U0001F52E {t('NATAL_HEADER_AI', lang)}\n\n" + ai_text
        else:
            sun_sign = chart_data.get("sun_sign", "Unknown")
            template = SHORT_INTERPRETATIONS.get(sun_sign, "")
            if not template:
                template = sign_display(sun_sign, lang)
            return base + f"\n{t('NATAL_HEADER_AI', lang)}\n\n{template}"

natal_service = NatalService()
