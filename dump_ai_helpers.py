from pathlib import Path
content = Path("ai_service_n1n.py").read_text(encoding="utf-8")

methods = [
    "def _get_system_prompt",
    "def _build_user_prompt",
    "def _build_cache_key",
    "async def extract_user_facts",
]

out_lines = []
for sig in methods:
    idx = content.find(sig)
    if idx < 0:
        out_lines.append(f"=== {sig} === NOT FOUND\n")
        continue
    # Find end (next "def " or "async def" at same indent)
    import re
    m = re.search(r'\n    (?:async )?def ', content[idx+10:])
    end = idx + 10 + m.start() if m else len(content)
    out_lines.append(f"=== {sig} ===\n{content[idx:end]}\n")

Path("dump_ai_helpers.txt").write_text("\n".join(out_lines), encoding="utf-8")
print("OK")