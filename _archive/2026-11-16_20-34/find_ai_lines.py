# -*- coding: utf-8 -*-
"""Найти все строки с 'AI' в пользовательских файлах (UTF-8)."""
from pathlib import Path

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")

FILES = [
    "handlers/ai_handler.py",
    "handlers/mood_diary.py",
    "handlers/pdf_handler.py",
    "handlers/tarot.py",
    "handlers/profile.py",
    "services/reminder.py",
    "services/natal_service.py",
]

for rel in FILES:
    p = BASE / rel
    if not p.exists():
        print(f"НЕТ ФАЙЛА: {rel}")
        continue

    print()
    print("=" * 70)
    print(f"ФАЙЛ: {rel}")
    print("=" * 70)

    lines = p.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, 1):
        if "AI" in line or "ИИ" in line:
            print(f"L{i}: {repr(line)}")

print()
print("=" * 70)
print("ГОТОВО")
