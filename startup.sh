#!/bin/bash
# Скрипт запуска AstroBot на Render
echo "🚀 Запуск AstroBot..."

# Проверка обязательных переменных
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN не установлен!"
    exit 1
fi
if [ -z "$DB_HOST" ]; then
    echo "❌ DB_HOST не установлен!"
    exit 1
fi

echo "✅ Переменные окружения на месте"
echo "🤖 Запуск бота..."

# Запуск через gunicorn (продакшен-сервер)
exec gunicorn bot_prod:app \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
