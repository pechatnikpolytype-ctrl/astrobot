import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Telegram
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ============================================================
# Админы
# ============================================================
ADMINS_RAW = os.getenv("ADMIN_IDS", "")
ADMINS = [int(x.strip()) for x in ADMINS_RAW.split(",") if x.strip().isdigit()]

# ============================================================
# PostgreSQL (Supabase / Pooler)
# ============================================================
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "postgres")

# ============================================================
# AI (n1n.ai)
# ============================================================
N1N_API_KEY = os.getenv("N1N_API_KEY", "")
N1N_BASE_URL = os.getenv("N1N_BASE_URL", "https://api.n1n.ai/v1")
N1N_MODEL = os.getenv("N1N_MODEL", "gpt-4o-mini")

# Для обратной совместимости
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "google/gemini-2.0-flash-exp:free"

# ============================================================
# РЕЖИМ РАЗРАБОТКИ
# ============================================================
# FREE_MODE = True  -> все пользователи считаются оплаченными
# FREE_MODE = False -> работает штатная проверка подписки
FREE_MODE = os.getenv("FREE_MODE", "true").lower() in ("1", "true", "yes", "on")

# ============================================================
# Прочее
# ============================================================
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "10000"))
