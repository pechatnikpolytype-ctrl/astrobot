import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
BACKUP_DIR = BASE_DIR / 'backups'


def create_backup():
    """Создаёт бэкап PostgreSQL через pg_dump."""
    try:
        if not DB_HOST:
            logger.warning("DB_HOST не задан, бэкап PostgreSQL невозможен.")
            return False

        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = BACKUP_DIR / f'pg_backup_{timestamp}.sql'

        env = os.environ.copy()
        env['PGPASSWORD'] = DB_PASSWORD or ''

        cmd = [
            'pg_dump',
            '-h', DB_HOST,
            '-p', str(DB_PORT or 5432),
            '-U', DB_USER,
            '-d', DB_NAME,
            '-f', str(backup_file),
        ]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            logger.error(f"❌ pg_dump ошибка: {result.stderr}")
            return False

        logger.info(f"✅ Бэкап создан: {backup_file.name}")

        # Оставляем последние 10 бэкапов
        backups = sorted(BACKUP_DIR.glob('pg_backup_*.sql'))
        if len(backups) > 10:
            for old in backups[:-10]:
                old.unlink()
                logger.info(f"🗑️ Удален старый бэкап: {old.name}")
        return True
    except FileNotFoundError:
        logger.error("❌ pg_dump не найден. Установите PostgreSQL client.")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка создания бэкапа: {e}")
        return False
