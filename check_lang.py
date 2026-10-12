from pathlib import Path
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

content = Path("handlers/admin_simple.py").read_text(encoding="utf-8")
lines = content.split("\n")

# Находим все функции
funcs = []
for i, line in enumerate(lines):
    if line.strip().startswith("async def ") or line.strip().startswith("def "):
        # Skip _admin_lang
        if "_admin_lang" in line:
            continue
        funcs.append((i, line.strip()))

# Для каждой функции: ищем в её теле t(..., lang)
for i, sig in funcs:
    # Находим конец функции
    end = i + 1
    while end < len(lines):
        line = lines[end]
        if line and not line.startswith(" ") and not line.startswith("#"):
            break
        if line.strip().startswith("async def ") or line.strip().startswith("def "):
            if not line.startswith(" "):
                break
        end += 1
    
    body = "\n".join(lines[i:end])
    
    # Есть ли использование lang
    uses_lang = "lang" in body and ("t(" in body and ", lang" in body)
    defines_lang = "lang = " in body or "lang=await" in body
    
    if uses_lang and not defines_lang:
        print(f"L{i+1}: {sig[:70]}")
        print(f"     USES lang BUT NOT DEFINED")
        print()

print("Готово")