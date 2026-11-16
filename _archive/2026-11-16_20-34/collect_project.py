#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Собирает все файлы проекта в один текстовый файл.
- рекурсивно обходит вложенные папки
- обрезает большие/бинарные файлы
- маскирует секреты (токены, пароли)
- соблюдает общий лимит размера
"""

import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ---------- Настройки по умолчанию ----------
DEFAULT_EXCLUDE_DIRS = {
    "__pycache__", ".git", ".hg", ".svn", "venv", "env", ".venv",
    "node_modules", ".mypy_cache", ".pytest_cache", ".idea", ".vscode",
    "dist", "build", "logs", "media", "downloads", "$Recycle.Bin",
    "System Volume Information", ".tox", "site-packages",
}

DEFAULT_EXCLUDE_EXTS = {
    # бинарники и медиа
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".wav", ".ogg",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # БД и сессии
    ".db", ".sqlite", ".sqlite3", ".session", ".session-journal",
    ".pyc", ".whl", ".egg",
}

# Приоритет текстовых расширений (важные — первыми)
PRIORITY_EXTS = [
    ".py", ".env", ".ini", ".cfg", ".toml", ".yaml", ".yml",
    ".json", ".txt", ".md", ".sql", ".sh", ".bat", ".ps1",
    ".html", ".css", ".js", ".ts", ".xml", ".conf", ".log",
]

# Размер одного файла по умолчанию (КБ), дальше — обрезка
DEFAULT_MAX_FILE_KB = 40
# Общий лимит выходного файла (КБ)
DEFAULT_TOTAL_LIMIT_KB = 400


def is_text_file(path: Path) -> bool:
    """Грубая проверка, текстовый ли файл."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
        if b"\x00" in chunk:
            return False
        # попытка декодировать
        for enc in ("utf-8", "cp1251", "latin-1"):
            try:
                chunk.decode(enc)
                return True
            except UnicodeDecodeError:
                continue
        return False
    except Exception:
        return False


def read_text(path: Path) -> str:
    """Читает текст с автоопределением кодировки."""
    for enc in ("utf-8", "cp1251", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception:
            return ""
    return ""


# ---------- Маскировка секретов ----------
SECRET_PATTERNS = [
    # BOT_TOKEN=123456:ABC...
    (re.compile(r'(?i)(bot[_-]?token\s*[:=]\s*)(["\']?)([A-Za-z0-9_:\-]{20,})(\2)'),
     r'\1\2***MASKED***\4'),
    # api_key / api_secret
    (re.compile(r'(?i)((?:api[_-]?key|api[_-]?secret|secret[_-]?key)\s*[:=]\s*)(["\']?)([A-Za-z0-9_\-]{16,})(\2)'),
     r'\1\2***MASKED***\4'),
    # password / passwd / pwd
    (re.compile(r'(?i)((?:password|passwd|pwd|db[_-]?pass)\s*[:=]\s*)(["\']?)([^\s"\']{4,})(\2)'),
     r'\1\2***MASKED***\4'),
    # приватные ключи (PEM)
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----',
                re.DOTALL),
     '***MASKED PRIVATE KEY***'),
    # токены вида 1234567890:AAH...
    (re.compile(r'\b\d{8,12}:[A-Za-z0-9_\-]{30,}\b'), '***MASKED_TOKEN***'),
    # длинные hex-строки (похоже на ключи)
    (re.compile(r'\b[a-fA-F0-9]{32,}\b'), '***MASKED_HEX***'),
]


def mask_secrets(text: str) -> str:
    for pattern, repl in SECRET_PATTERNS:
        text = pattern.sub(repl, text)
    return text


# ---------- Построение дерева ----------
def build_tree(root: Path, exclude_dirs: set) -> str:
    lines = [f"{root.name}/"]
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith(".")]
        depth = len(Path(dirpath).relative_to(root).parts)
        indent = "│   " * depth
        if depth > 0:
            lines.append(f"{indent}├── {Path(dirpath).name}/")
        for fname in sorted(filenames):
            try:
                size = (Path(dirpath) / fname).stat().st_size
                lines.append(f"{indent}│   ├── {fname}  ({size} B)")
            except Exception:
                lines.append(f"{indent}│   ├── {fname}")
    return "\n".join(lines)


# ---------- Основная логика ----------
def collect(
    root: Path,
    out_file: Path,
    max_file_kb: int,
    total_limit_kb: int,
    mask: bool,
    include_binaries: bool,
):
    total_limit_bytes = total_limit_kb * 1024
    max_file_bytes = max_file_kb * 1024

    # 1) Собираем список файлов
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS and not d.startswith(".")]
        for fname in filenames:
            p = Path(dirpath) / fname
            ext = p.suffix.lower()
            if ext in DEFAULT_EXCLUDE_EXTS and not include_binaries:
                continue
            if fname.endswith(".session") or fname.endswith(".session-journal"):
                continue
            if p.name in (out_file.name,):
                continue
            all_files.append(p)

    # 2) Сортируем по приоритету (важные расширения — первыми), потом по размеру
    def sort_key(p: Path):
        try:
            ext_rank = PRIORITY_EXTS.index(p.suffix.lower()) if p.suffix.lower() in PRIORITY_EXTS else 999
        except ValueError:
            ext_rank = 999
        try:
            size = p.stat().st_size
        except Exception:
            size = 0
        return (ext_rank, size)

    all_files.sort(key=sort_key)

    # 3) Пишем
    written_bytes = 0
    written_files = 0
    skipped_files = []

    with open(out_file, "w", encoding="utf-8") as out:
        header = (
            "=" * 80 + "\n"
            f"ПРОЕКТ: {root}\n"
            f"СОБРАНО: {datetime.now().isoformat()}\n"
            f"ЛИМИТ ФАЙЛА: {total_limit_kb} КБ\n"
            f"МАКС. РАЗМЕР ОДНОГО ФАЙЛА: {max_file_kb} КБ\n"
            + ("СЕКРЕТЫ: МАСКИРУЮТСЯ\n" if mask else "СЕКРЕТЫ: НЕ МАСКИРУЮТСЯ ⚠️\n")
            + "=" * 80 + "\n\n"
        )
        out.write(header)
        written_bytes += len(header.encode("utf-8"))

        # Дерево проекта
        tree = build_tree(root, DEFAULT_EXCLUDE_DIRS)
        out.write("СТРУКТУРА ПРОЕКТА:\n")
        out.write(tree + "\n\n")
        written_bytes += len(tree.encode("utf-8")) + 30

        out.write("=" * 80 + "\n")
        out.write("СОДЕРЖИМОЕ ФАЙЛОВ\n")
        out.write("=" * 80 + "\n\n")

        for path in all_files:
            try:
                rel = path.relative_to(root)
                size = path.stat().st_size
            except Exception as e:
                skipped_files.append((str(path), f"ошибка доступа: {e}"))
                continue

            # Проверка общего лимита
            if written_bytes >= total_limit_bytes:
                skipped_files.append((str(rel), "превышен общий лимит"))
                continue

            out.write("\n" + "-" * 80 + "\n")
            out.write(f"ФАЙЛ: {rel}\n")
            out.write(f"РАЗМЕР: {size} B\n")
            out.write("-" * 80 + "\n")

            # Бинарный?
            if not is_text_file(path):
                out.write("[БИНАРНЫЙ ФАЙЛ — содержимое не включено]\n")
                written_files += 1
                continue

            content = read_text(path)
            if not content:
                out.write("[НЕ УДАЛОСЬ ПРОЧИТАТЬ — пусто или ошибка]\n")
                written_files += 1
                continue

            if mask:
                content = mask_secrets(content)

            # Обрезка больших файлов
            truncated = False
            if len(content.encode("utf-8")) > max_file_bytes:
                # режем по символам (примерно)
                content = content[:max_file_bytes]
                truncated = True

            out.write(content)
            if truncated:
                out.write(f"\n\n[...ОБРЕЗАНО до {max_file_kb} КБ...]\n")
            if not content.endswith("\n"):
                out.write("\n")

            written_bytes = out.tell()
            written_files += 1

        # Итоги
        out.write("\n" + "=" * 80 + "\n")
        out.write("ИТОГИ\n")
        out.write("=" * 80 + "\n")
        out.write(f"Файлов включено: {written_files}\n")
        out.write(f"Пропущено/обрезано: {len(skipped_files)}\n")
        out.write(f"Итоговый размер: {written_bytes / 1024:.1f} КБ\n")
        if skipped_files:
            out.write("\nПРОПУЩЕННЫЕ / НЕ ВОШЕДШИЕ ФАЙЛЫ:\n")
            for name, reason in skipped_files[:100]:
                out.write(f"  - {name} ({reason})\n")

    print(f"✅ Готово: {out_file}")
    print(f"   Файлов включено: {written_files}")
    print(f"   Пропущено: {len(skipped_files)}")
    print(f"   Размер: {written_bytes / 1024:.1f} КБ")


# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(
        description="Собрать весь проект в один текстовый файл (с учётом лимитов)."
    )
    parser.add_argument("project_path", help="Путь к папке проекта")
    parser.add_argument("-o", "--output", default="project_dump.txt",
                        help="Имя выходного файла (по умолчанию project_dump.txt)")
    parser.add_argument("--max-file-kb", type=int, default=DEFAULT_MAX_FILE_KB,
                        help=f"Макс. размер одного файла в КБ (по умолчанию {DEFAULT_MAX_FILE_KB})")
    parser.add_argument("--total-limit-kb", type=int, default=DEFAULT_TOTAL_LIMIT_KB,
                        help=f"Общий лимит выходного файла в КБ (по умолчанию {DEFAULT_TOTAL_LIMIT_KB})")
    parser.add_argument("--no-mask", action="store_true",
                        help="НЕ маскировать секреты (по умолчанию маскируются)")
    parser.add_argument("--include-binaries", action="store_true",
                        help="Включать бинарные файлы (только пометка, без содержимого)")
    args = parser.parse_args()

    root = Path(args.project_path).resolve()
    if not root.is_dir():
        print(f"❌ Папка не найдена: {root}")
        sys.exit(1)

    collect(
        root=root,
        out_file=Path(args.output),
        max_file_kb=args.max_file_kb,
        total_limit_kb=args.total_limit_kb,
        mask=not args.no_mask,
        include_binaries=args.include_binaries,
    )


if __name__ == "__main__":
    main()