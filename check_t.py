from pathlib import Path

# 1. Что в t() для нужных ключей
from locales import t
for key in ["NATAL_TITLE", "NATAL_HEADER_MAIN", "NATAL_LABEL_SUN", "NATAL_HEADER_PLANETS", "NATAL_HEADER_HOUSES"]:
    print(f"{key}:")
    print(f"  ru: {t(key, 'ru')}")
    print(f"  en: {t(key, 'en')}")
    print(f"  de: {t(key, 'de')}")

# 2. Смотрим строки метода generate_report_text
content = Path("services/natal_service.py").read_text(encoding="utf-8")
lines = content.split("\n")
start = None
for i, line in enumerate(lines):
    if "def generate_report_text(self" in line:
        start = i
        break
if start:
    print()
    print("=== generate_report_text (первые 25 строк) ===")
    for i in range(start, min(start + 25, len(lines))):
        print(f"L{i+1}: {lines[i]}")