from pathlib import Path
content = Path("services/natal_service.py").read_text(encoding="utf-8")

# Считаем сколько раз встречается каждая сигнатура
for sig in ["def generate_report_text", "async def generate_ai_report", "async def generate_full_report"]:
    count = content.count(sig)
    print(f"{sig}: {count} раз")

# Покажем все строки с "ОСНОВНЫЕ ХАРАКТЕРИСТИКИ" (может остался старый код)
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
for i, line in enumerate(content.split("\n"), 1):
    if "generate_report_text" in line or "generate_full_report" in line:
        print(f"L{i}: {line.strip()[:80]}")