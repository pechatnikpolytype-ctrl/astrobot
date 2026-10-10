# -*- coding: utf-8 -*-
"""Дамп ключевых файлов в UTF-8 для просмотра."""
from pathlib import Path
import sys
import io

# Принудительно UTF-8 для stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FILES = [
    "keyboards/main.py",
    "handlers/start.py",
    "handlers/natal.py",
    "handlers/tarot.py",
    "handlers/compatibility.py",
    "handlers/profile.py",
    "handlers/ai_handler.py",
    "handlers/pdf_handler.py",
    "handlers/mood_diary.py",
    "handlers/horoscope.py",
]

out = Path("dump_phase2.txt")
with out.open("w", encoding="utf-8") as f:
    for rel in FILES:
        p = Path(rel)
        f.write("=" * 70 + "\n")
        f.write(f"ФАЙЛ: {rel}\n")
        f.write("=" * 70 + "\n")
        if p.exists():
            f.write(p.read_text(encoding="utf-8"))
        else:
            f.write(f"[НЕ НАЙДЕН: {rel}]\n")
        f.write("\n\n")

print(f"✅ Дамп записан: {out.resolve()}")
print(f"   Размер: {out.stat().st_size} B")
print(f"   Файлов: {len(FILES)}")
