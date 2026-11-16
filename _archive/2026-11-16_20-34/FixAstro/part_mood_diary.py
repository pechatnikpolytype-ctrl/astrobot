#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Часть C: Дневник настроения.
Запуск: python part_mood_diary.py
"""

from pathlib import Path
import shutil

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")

if not BASE.exists():
    print(f"❌ Папка не найдена: {BASE}")
    exit(1)


def backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak_mood")
    if not bak.exists():
        shutil.copy2(path, bak)


# ============================================================
# 1. APPEND в database/postgres_db.py
# ============================================================
DB_APPEND = r'''

# ============================================================
# ДНЕВНИК НАСТРОЕНИЯ
# ============================================================
async def init_mood_table():
    """Создаёт таблицу mood_diary."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mood_diary (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                mood INTEGER NOT NULL,
                mood_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, mood_date)
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mood_user ON mood_diary(user_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mood_date ON mood_diary(mood_date)
        """)
    logger.info("✅ Таблица mood_diary создана/проверена")


async def set_mood(user_id: int, mood: int):
    """Сохраняет настроение на сегодня (или обновляет)."""
    from datetime import date
    today = date.today()
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO mood_diary (user_id, mood, mood_date)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, mood_date)
            DO UPDATE SET mood = $2, created_at = CURRENT_TIMESTAMP
        """, user_id, mood, today)


async def get_mood_today(user_id: int):
    """Возвращает настроение за сегодня или None."""
    from datetime import date
    today = date.today()
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT mood FROM mood_diary WHERE user_id = $1 AND mood_date = $2",
            user_id, today
        )
        return row["mood"] if row else None


async def get_mood_history(user_id: int, days: int = 30) -> list:
    """Возвращает список настроений за N дней (от новых к старым)."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT mood, mood_date FROM mood_diary
            WHERE user_id = $1
              AND mood_date >= CURRENT_DATE - INTERVAL '{days} days'
            ORDER BY mood_date DESC
        """, user_id)
        return [dict(r) for r in rows]


async def get_mood_stats(user_id: int, days: int = 7) -> dict:
    """Статистика: средний балл, количество записей."""
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(f"""
            SELECT
                COUNT(*) as total,
                AVG(mood) as avg_mood,
                MIN(mood) as min_mood,
                MAX(mood) as max_mood
            FROM mood_diary
            WHERE user_id = $1
              AND mood_date >= CURRENT_DATE - INTERVAL '{days} days'
        """, user_id)
        return {
            "total": row["total"] or 0,
            "avg": float(row["avg_mood"]) if row["avg_mood"] else 0,
            "min": row["min_mood"] or 0,
            "max": row["max_mood"] or 0,
        }


async def count_bad_mood_streak(user_id: int) -> int:
    """Считает подряд идущие дни с плохим настроением (<=2)."""
    history = await get_mood_history(user_id, days=10)
    streak = 0
    for entry in history:
        if entry["mood"] <= 2:
            streak += 1
        else:
            break
    return streak
'''

db_path = BASE / "database" / "postgres_db.py"
backup(db_path)
content = db_path.read_text(encoding="utf-8")

if "async def init_mood_table" not in content:
    with open(db_path, "a", encoding="utf-8") as f:
        f.write(DB_APPEND)
    print("  ✅ database/postgres_db.py — функции mood_diary")

# Патч init_postgres_db — добавить вызов init_mood_table
content = db_path.read_text(encoding="utf-8")
ANCHOR = '    # --- Инициализация рефералов ---'
if "await init_mood_table()" not in content and ANCHOR in content:
    content = content.replace(
        ANCHOR,
        "    # --- Инициализация дневника настроения ---\n    await init_mood_table()\n\n" + ANCHOR,
        1
    )
    db_path.write_text(content, encoding="utf-8")
    print("  ✅ init_mood_table вызывается в init_postgres_db")


# ============================================================
# 2. Новый handlers/mood_diary.py
# ============================================================
MOOD_DIARY_PY = r'''import logging
import os
import uuid
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from database.postgres_db import (
    set_mood, get_mood_today, get_mood_history, get_mood_stats,
    count_bad_mood_streak,
)
from keyboards.main import back_to_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# НАСТРОЕНИЯ
# ============================================================
MOODS = {
    5: {"emoji": "😊", "name": "Отлично"},
    4: {"emoji": "🙂", "name": "Хорошо"},
    3: {"emoji": "😐", "name": "Нормально"},
    2: {"emoji": "😔", "name": "Плохо"},
    1: {"emoji": "😢", "name": "Ужасно"},
}


def mood_emoji(mood: int) -> str:
    return MOODS.get(mood, {}).get("emoji", "❓")


def mood_name(mood: int) -> str:
    return MOODS.get(mood, {}).get("name", "?")


def avg_to_mood(avg: float) -> tuple:
    """Возвращает (emoji, name) для среднего балла."""
    if avg >= 4.5: return "😊", "Отлично"
    if avg >= 3.5: return "🙂", "Хорошо"
    if avg >= 2.5: return "😐", "Нормально"
    if avg >= 1.5: return "😔", "Плохо"
    return "😢", "Ужасно"


def build_mood_keyboard():
    """Клавиатура выбора настроения."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😊 Отлично", callback_data="mood_set_5"),
         InlineKeyboardButton(text="🙂 Хорошо", callback_data="mood_set_4")],
        [InlineKeyboardButton(text="😐 Нормально", callback_data="mood_set_3"),
         InlineKeyboardButton(text="😔 Плохо", callback_data="mood_set_2")],
        [InlineKeyboardButton(text="😢 Ужасно", callback_data="mood_set_1")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="mood_stats"),
         InlineKeyboardButton(text="📈 График", callback_data="mood_chart")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])


# ============================================================
# ГЛАВНЫЙ ЭКРАН ДНЕВНИКА
# ============================================================
@router.callback_query(F.data == "mood_diary")
async def mood_diary_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    today_mood = await get_mood_today(user_id)

    if today_mood:
        today_text = f"Сегодня вы отметили: {mood_emoji(today_mood)} {mood_name(today_mood)}"
    else:
        today_text = "Сегодня вы ещё не отметили настроение."

    text = (
        "📔 ДНЕВНИК НАСТРОЕНИЯ\n\n"
        "Как ваше настроение сегодня?\n\n"
        f"{today_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Выберите настроение или посмотрите статистику:"
    )

    try:
        await callback.message.edit_text(text, reply_markup=build_mood_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=build_mood_keyboard())


# ============================================================
# СОХРАНЕНИЕ НАСТРОЕНИЯ
# ============================================================
@router.callback_query(F.data.startswith("mood_set_"))
async def mood_set(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        mood = int(callback.data.replace("mood_set_", ""))
    except ValueError:
        return

    if mood not in MOODS:
        return

    await set_mood(user_id, mood)

    # Проверяем streak плохого настроения
    streak = await count_bad_mood_streak(user_id)

    # Показываем ответ
    mood_text = f"{mood_emoji(mood)} {mood_name(mood)}"

    if streak >= 3:
        # Даём AI-совет
        text = (
            f"✅ Настроение сохранено: {mood_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💙 Мы заметили, что последние {streak} дня "
            f"вы чувствуете себя не очень.\n\n"
            f"Хотите поговорить с AI-астрологом? Он даст "
            f"персональный совет."
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Поговорить с AI", callback_data="ai_question")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="mood_stats")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ])
    else:
        text = f"✅ Настроение сохранено: {mood_text}"
        keyboard = build_mood_keyboard()

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


# ============================================================
# СТАТИСТИКА
# ============================================================
@router.callback_query(F.data == "mood_stats")
async def mood_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    history = await get_mood_history(user_id, days=7)
    stats = await get_mood_stats(user_id, days=7)

    if not history:
        text = (
            "📊 СТАТИСТИКА\n\n"
            "Пока нет записей. Отметьте настроение!"
        )
    else:
        text = "📊 СТАТИСТИКА ЗА 7 ДНЕЙ\n\n"
        for entry in history:
            date_str = entry["mood_date"].strftime("%d.%m")
            text += f"{date_str} — {mood_emoji(entry['mood'])} {mood_name(entry['mood'])}\n"

        if stats["total"] > 0:
            avg_emoji, avg_name = avg_to_mood(stats["avg"])
            text += (
                f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Средний балл: {avg_emoji} {avg_name} ({stats['avg']:.1f}/5)\n"
                f"Записей: {stats['total']}"
            )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📔 Дневник", callback_data="mood_diary")],
        [InlineKeyboardButton(text="📈 График", callback_data="mood_chart")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ГРАФИК
# ============================================================
@router.callback_query(F.data == "mood_chart")
async def mood_chart(callback: CallbackQuery):
    user_id = callback.from_user.id
    history = await get_mood_history(user_id, days=30)

    if len(history) < 2:
        await callback.answer(
            "Нужно минимум 2 записи для графика.", show_alert=True
        )
        return

    msg = await callback.message.edit_text("📈 Строю график...")

    try:
        chart_path = _build_mood_chart(history)
        if not chart_path:
            await msg.edit_text("❌ Не удалось построить график.")
            return

        try:
            await msg.delete()
        except Exception:
            pass

        photo = FSInputFile(chart_path)
        await callback.message.answer_photo(
            photo, caption="📈 Ваше настроение за 30 дней"
        )
        await callback.message.answer(
            "Что дальше?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📔 Дневник", callback_data="mood_diary")],
                [InlineKeyboardButton(text="📊 Статистика", callback_data="mood_stats")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
            ])
        )

        try:
            os.remove(chart_path)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Ошибка графика: {e}")
        try:
            await msg.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


def _build_mood_chart(history: list) -> str:
    """Строит график настроения. Возвращает путь к PNG."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from datetime import datetime
    except ImportError:
        logger.error("matplotlib не установлен")
        return None

    # Сортируем по дате (от старых к новым)
    data = sorted(history, key=lambda x: x["mood_date"])
    dates = [d["mood_date"].strftime("%d.%m") for d in data]
    moods = [d["mood"] for d in data]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#1a2a3a")
    ax.set_facecolor("#1a2a3a")

    # Линия + маркеры
    ax.plot(dates, moods, "o-", color="#FFD700", linewidth=2, markersize=8)

    # Сетка
    ax.grid(True, alpha=0.3, color="#c9a959")
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["😢", "😔", "😐", "🙂", "😊"], fontsize=14)

    # Заголовки
    ax.set_title("Настроение за 30 дней", color="#FFD700", fontsize=16, pad=15)
    ax.tick_params(colors="#F0F0F0", labelsize=9)

    # Поворот дат
    plt.xticks(rotation=45, ha="right")

    # Границы
    for spine in ax.spines.values():
        spine.set_color("#c9a959")

    plt.tight_layout()

    filename = f"mood_chart_{uuid.uuid4().hex}.png"
    plt.savefig(filename, facecolor="#1a2a3a", dpi=100)
    plt.close()
    return filename
'''


mood_path = BASE / "handlers" / "mood_diary.py"
mood_path.write_text(MOOD_DIARY_PY, encoding="utf-8")
print("  ✅ handlers/mood_diary.py — создан")


# ============================================================
# 3. Кнопка 📔 Дневник в главное меню
# ============================================================
kb_path = BASE / "keyboards" / "main.py"
backup(kb_path)
content = kb_path.read_text(encoding="utf-8")

if '📔 Дневник' not in content:
    OLD_MENU = '''    kb.button(text="👤 Профиль", callback_data="profile")
    kb.button(text="📄 PDF отчёт", callback_data="generate_pdf")'''
    NEW_MENU = '''    kb.button(text="👤 Профиль", callback_data="profile")
    kb.button(text="📔 Дневник", callback_data="mood_diary")
    kb.button(text="📄 PDF отчёт", callback_data="generate_pdf")'''
    if OLD_MENU in content:
        content = content.replace(OLD_MENU, NEW_MENU, 1)
        kb_path.write_text(content, encoding="utf-8")
        print("  ✅ keyboards/main.py — добавлена кнопка 📔 Дневник")
    else:
        print("  ⚠️  keyboards/main.py — anchor не найден")
else:
    print("  ℹ️  keyboards/main.py — кнопка уже есть")


# ============================================================
# 4. Подключить роутер в handlers/__init__.py
# ============================================================
init_path = BASE / "handlers" / "__init__.py"
backup(init_path)
content = init_path.read_text(encoding="utf-8")

if "mood_diary" not in content:
    lines = content.rstrip().split("\n")
    for i, line in enumerate(lines):
        if line.startswith("__all__"):
            lines.insert(i, "from .mood_diary import router as mood_router")
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "]":
                    lines.insert(j, "    'mood_router',")
                    break
            break
    content = "\n".join(lines) + "\n"
    init_path.write_text(content, encoding="utf-8")
    print("  ✅ handlers/__init__.py — mood_router подключён")
else:
    print("  ℹ️  handlers/__init__.py — mood_router уже есть")


# ============================================================
# 5. Патч webhook_bot.py и bot_prod.py
# ============================================================
for fname in ["webhook_bot.py", "bot_prod.py"]:
    fpath = BASE / fname
    if not fpath.exists():
        continue

    backup(fpath)
    content = fpath.read_text(encoding="utf-8")

    if "mood_router" in content:
        print(f"  ℹ️  {fname} — mood_router уже есть")
        continue

    # Добавляем импорт
    if "from handlers.menu_commands import router as menu_router" in content:
        content = content.replace(
            "from handlers.menu_commands import router as menu_router",
            "from handlers.menu_commands import router as menu_router\nfrom handlers.mood_diary import router as mood_router"
        )
    elif "from handlers.start import router as start_router" in content:
        content = content.replace(
            "from handlers.start import router as start_router",
            "from handlers.start import router as start_router\nfrom handlers.mood_diary import router as mood_router"
        )

    # Подключаем роутер
    if "dp.include_router(start_router)" in content:
        content = content.replace(
            "dp.include_router(start_router)",
            "dp.include_router(start_router)\ndp.include_router(mood_router)"
        )

    fpath.write_text(content, encoding="utf-8")
    print(f"  ✅ {fname} — mood_router подключён")


# ============================================================
# 6. Проверка requirements.txt на matplotlib
# ============================================================
req_path = BASE / "requirements.txt"
content = req_path.read_text(encoding="utf-8")

if "matplotlib" not in content:
    with open(req_path, "a", encoding="utf-8") as f:
        f.write("\nmatplotlib==3.9.2\n")
    print("  ✅ requirements.txt — добавлен matplotlib")
else:
    print("  ℹ️  requirements.txt — matplotlib уже есть")


print()
print("=" * 60)
print("ГОТОВО!")
print("=" * 60)
print()
print("Что работает:")
print("  • Кнопка 📔 Дневник в главном меню")
print("  • 5 настроений (😊🙂😐😔😢)")
print("  • Статистика за 7 дней")
print("  • График за 30 дней")
print("  • AI-совет при 3+ днях плохого")
print()
print("⚠️ ВАЖНО:")
print("  • matplotlib должен работать на Render (Python 3.11)")
print("  • Проверь, что в requirements.txt есть matplotlib")
print()
print("Дальше:")
print("  cd C:\\Users\\User\\Desktop\\AstroBot_clean")
print("  python webhook_bot.py")
print()
print("Проверь:")
print("  1. /start → 📔 Дневник")
print("  2. Отметь настроение")
print("  3. Нажми «📊 Статистика»")
print("  4. Нажми «📈 График»")