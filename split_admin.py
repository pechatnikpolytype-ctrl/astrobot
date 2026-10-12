from pathlib import Path

src = Path("dump_admin_simple.txt")
raw = src.read_bytes()
print(f"Size: {len(raw)} B")
print(f"First 4 bytes: {raw[:4].hex()}")

# Try encodings
content = None
for enc in ["utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "cp1251", "utf-8"]:
    try:
        content = raw.decode(enc)
        print(f"Decoded with: {enc}")
        break
    except UnicodeDecodeError:
        continue

if content is None:
    print("ERR: cannot decode")
    exit(1)

lines = content.split("\n")
total = len(lines)
print(f"Total lines: {total}")

part_size = (total + 2) // 3
parts = [lines[i:i+part_size] for i in range(0, total, part_size)]

for i, part in enumerate(parts, 1):
    out = Path(f"dump_admin_part{i}.txt")
    # Save as UTF-8 without BOM
    out.write_text("\n".join(part), encoding="utf-8")
    print(f"  {out.name}: {len(part)} lines")