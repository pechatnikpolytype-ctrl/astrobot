from pathlib import Path
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

for f in ["services/natal_service.py", "services/pdf_generator.py", "astrology_calculator.py"]:
    p = Path(f)
    print("=" * 70)
    print(f"ФАЙЛ: {f}")
    print("=" * 70)
    print(p.read_text(encoding="utf-8"))
    print()
