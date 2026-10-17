# -*- coding: utf-8 -*-
"""Connect dreams_router in webhook_bot.py, bot_prod.py, __init__.py."""
from pathlib import Path
import ast


def patch_file(fname, include_after=None):
    """Добавляет импорт и include для dreams_router."""
    P = Path(fname)
    if not P.exists():
        print(f"[i] {fname}: not found")
        return

    content = P.read_text(encoding="utf-8")
    original = content

    # 1. Импорт
    if "from handlers.dreams import router as dreams_router" not in content:
        # Ищем любую строку "from handlers.X import router as Y_router"
        lines = content.split("\n")
        last_handler_import = -1
        for i, line in enumerate(lines):
            if line.startswith("from handlers.") and "import router" in line:
                last_handler_import = i
        if last_handler_import >= 0:
            lines.insert(
                last_handler_import + 1,
                "from handlers.dreams import router as dreams_router",
            )
            content = "\n".join(lines)
            print(f"[OK] {fname}: import added after line {last_handler_import + 1}")
        else:
            print(f"[ERR] {fname}: no handler imports found")
            return

    # 2. Include
    if "dp.include_router(dreams_router)" not in content:
        lines = content.split("\n")
        last_include = -1
        for i, line in enumerate(lines):
            if "dp.include_router(" in line:
                last_include = i
        if last_include >= 0:
            lines.insert(last_include + 1, "dp.include_router(dreams_router)")
            content = "\n".join(lines)
            print(f"[OK] {fname}: include added after line {last_include + 1}")
        else:
            print(f"[ERR] {fname}: no dp.include_router found")
            return

    if content != original:
        P.write_text(content, encoding="utf-8")

    try:
        ast.parse(content)
        print(f"[OK] {fname}: syntax valid")
    except SyntaxError as e:
        print(f"[ERR] {fname}: {e}")


# Patch webhook_bot.py
patch_file("webhook_bot.py")

# Patch bot_prod.py
patch_file("bot_prod.py")

# Patch handlers/__init__.py
P_init = Path("handlers/__init__.py")
c_init = P_init.read_text(encoding="utf-8")
if "dreams_router" not in c_init:
    # Импорт после последнего from .X import
    lines = c_init.split("\n")
    last_import = -1
    for i, line in enumerate(lines):
        if line.startswith("from .") and "import router" in line:
            last_import = i
    if last_import >= 0:
        lines.insert(last_import + 1, "from .dreams import router as dreams_router")
        c_init = "\n".join(lines)
        print("[OK] __init__.py: import added")

    # __all__ — добавить после tarot_router
    if '"tarot_router"' in c_init:
        c_init = c_init.replace(
            '"tarot_router",',
            '"tarot_router",\n    "dreams_router",',
            1,
        )
        print("[OK] __init__.py: __all__ updated")
    elif "'tarot_router'" in c_init:
        c_init = c_init.replace(
            "'tarot_router',",
            "'tarot_router',\n    'dreams_router',",
            1,
        )
        print("[OK] __init__.py: __all__ updated (single quotes)")

    P_init.write_text(c_init, encoding="utf-8")
    try:
        ast.parse(c_init)
        print("[OK] __init__.py: syntax valid")
    except SyntaxError as e:
        print(f"[ERR] __init__.py: {e}")
else:
    print("[i] __init__.py: already has dreams_router")

print()
print("=" * 60)
print("DONE — verify now:")
print("  python -c \"from handlers.dreams import router; print('OK')\"")
print("=" * 60)