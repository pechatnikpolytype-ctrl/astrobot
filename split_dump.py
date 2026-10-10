# -*- coding: utf-8 -*-
"""Разбивает dump_natal.txt на 3 части."""
from pathlib import Path

src = Path("dump_natal.txt")
text = src.read_text(encoding="utf-8")

# Ищем разделители файлов
marker = "=" * 70
parts = text.split(marker)

# parts[0] — мусор до первого разделителя
# Каждая пара (нечётный = имя файла, чётный = содержимое)
files = {}
i = 1
while i < len(parts) - 1:
    header = parts[i].strip()  # "\nФАЙЛ: services/xxx.py\n"
    body = parts[i + 1]         # содержимое + хвост
    if header.startswith("ФАЙЛ:"):
        name = header.replace("ФАЙЛ:", "").strip()
        files[name] = body
    i += 2

print(f"Найдено файлов: {len(files)}")
for name, body in files.items():
    out = Path(f"dump_{name.replace('/', '_')}.txt")
    out.write_text(body.strip(), encoding="utf-8")
    print(f"  ✅ {out.name}  ({len(body.encode('utf-8'))} B)")
