# services/local_astro.py
# Локальный расчёт натальной карты через Kerykeion (Swiss Ephemeris).
# Заменяет VedAstro API (который отдаёт 404).

from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

def calculate_natal_local(
    name: str,
    year: int, month: int, day: int, hour: int, minute: int,
    lat: float, lng: float, tz_str: str,
    output_dir: str = "charts_output"
) -> dict:
    """
    Считает натальную карту локально и сохраняет SVG.
    Возвращает словарь с путём к SVG и данными планет.
    """
    # Создаём субъект (online=False — без интернета)
    subject = AstrologicalSubjectFactory.from_birth_data(
        name, year, month, day, hour, minute,
        lng=lng, lat=lat, tz_str=tz_str,
        online=False,
    )

    # Данные для PDF/AI (планеты, дома)
    chart_data = ChartDataFactory.create_natal_chart_data(subject)

    # Генерируем SVG
    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    drawer = ChartDrawer(chart_data=chart_data)
    svg_path = out / f"natal_{name.replace(' ', '_')}.svg"
    drawer.save_svg(output_path=out, filename=svg_path.stem, style="classic", remove_css_variables=True)

    # Собираем текстовые данные для AI-интерпретации
    planets = {}
    for p in [subject.sun, subject.moon, subject.mercury, subject.venus,
              subject.mars, subject.jupiter, subject.saturn, subject.uranus,
              subject.neptune, subject.pluto, subject.chiron]:
        if p:
            planets[p.name] = {
                "sign": p.sign,
                "position": p.position,
                "house": p.house,
                "retrograde": p.retrograde,
            }

    return {
        "svg_path": str(svg_path),
        "planets": planets,
        "ascendant": subject.first_house.sign if subject.first_house else None,
        "raw_subject": subject,  # если нужен полный объект
    }
# ---- адаптер Kerykeion -> формат natal_service ----
SIGN_MAP_RU = {
    "Ari": "Овен", "Tau": "Телец", "Gem": "Близнецы", "Can": "Рак",
    "Leo": "Лев", "Vir": "Дева", "Lib": "Весы", "Sco": "Скорпион",
    "Sag": "Стрелец", "Cap": "Козерог", "Aqu": "Водолей", "Pis": "Рыбы",
}
PLANET_MAP_RU = {
    "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий",
    "Venus": "Венера", "Mars": "Марс", "Jupiter": "Юпитер",
    "Saturn": "Сатурн", "Uranus": "Уран", "Neptune": "Нептун",
    "Pluto": "Плутон", "Chiron": "Хирон",
}
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
SIGNS_ORDER_RU = ["Овен","Телец","Близнецы","Рак","Лев","Дева",
                  "Весы","Скорпион","Стрелец","Козерог","Водолей","Рыбы"]


def _ru_sign(s):
    return SIGN_MAP_RU.get(s, s)


def to_chart_data(result: dict, name: str, date: str, time: str, place: str) -> dict:
    """Преобразует результат calculate_natal_local в старый формат natal_service."""
    subj = result["raw_subject"]
    planets_list = []
    for eng, info in result["planets"].items():
        ru_name = PLANET_MAP_RU.get(eng, eng)
        _h = info.get("house", "")
        _hmap = {"First_House":"1","Second_House":"2","Third_House":"3","Fourth_House":"4",
                 "Fifth_House":"5","Sixth_House":"6","Seventh_House":"7","Eighth_House":"8",
                 "Ninth_House":"9","Tenth_House":"10","Eleventh_House":"11","Twelfth_House":"12"}
        planets_list.append({
            "name": ru_name,
            "sign": _ru_sign(info.get("sign", "")),
            "house": _hmap.get(_h, str(_h) if _h else "?"),
            "retrograde": bool(info.get("retrograde", False)),
        })
    sun_ru = _ru_sign(subj.sun.sign) if subj.sun else "Неизвестно"
    asc_ru = _ru_sign(subj.first_house.sign) if subj.first_house else sun_ru
    sun_idx = SIGNS_ORDER_RU.index(sun_ru) if sun_ru in SIGNS_ORDER_RU else 0
    houses = []
    _house_names = ["first_house","second_house","third_house","fourth_house",
                    "fifth_house","sixth_house","seventh_house","eighth_house",
                    "ninth_house","tenth_house","eleventh_house","twelfth_house"]
    for i, hn in enumerate(_house_names):
        h = getattr(subj, hn, None)
        houses.append({"number": i + 1, "sign": _ru_sign(h.sign) if h else "?"})
    return {
        "sun_sign": sun_ru,
        "element": ELEMENTS.get(sun_ru, "Неизвестно"),
        "quality": QUALITIES.get(sun_ru, "Неизвестно"),
        "ascendant": asc_ru,
        "planets": planets_list,
        "houses": houses,
        "birth_info": {"name": name, "date": date, "time": time, "place": place},
        "_kerykeion_svg": result["svg_path"],
    }