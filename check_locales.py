from locales import t
# Печатаем что возвращает t() для ключей отчёта на трёх языках
for key in ["NATAL_TITLE", "NATAL_HEADER_MAIN", "NATAL_HEADER_PLANETS", "NATAL_HEADER_HOUSES", "NATAL_LABEL_SUN", "NATAL_LABEL_ELEMENT"]:
    print(f"{key}:")
    print(f"  ru: {t(key, 'ru')}")
    print(f"  en: {t(key, 'en')}")
    print(f"  de: {t(key, 'de')}")