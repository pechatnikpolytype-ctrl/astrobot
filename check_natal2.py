from pathlib import Path
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 1. natal_service.py — что в generate_report_text и generate_svg_chart
content = Path("services/natal_service.py").read_text(encoding="utf-8")
print("=" * 60)
print("natal_service.py")
print("=" * 60)

# generate_report_text
idx = content.find("def generate_report_text(self")
end = content.find("def ", idx + 30)
if end < 0:
    end = idx + 3000
print()
print("--- generate_report_text ---")
print(content[idx:end][:2000])

# generate_svg_chart — ключевые строки
print()
print("--- SVG: заголовок, планеты, асцендент ---")
for line in content.split("\n"):
    if "НАТАЛЬНАЯ" in line or "Асцендент" in line or "short_name" in line or "АСЦ" in line or "SIGNS_SHORT" in line:
        print(f"  {line.strip()[:100]}")

# 2. pdf_generator.py — футер
content2 = Path("services/pdf_generator.py").read_text(encoding="utf-8")
print()
print("=" * 60)
print("pdf_generator.py")
print("=" * 60)
for line in content2.split("\n"):
    if "инструмент самопознания" in line or "Сгенерировано" in line or "PDF_FOOTER" in line:
        print(f"  {line.strip()[:120]}")