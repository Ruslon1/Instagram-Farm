#!/bin/bash

echo "🛑 Stopping Instagram Bot..."

# Остановка Celery workers по PID файлу
if [ -f celery.pid ]; then
    CELERY_PID=$(cat celery.pid)
    echo "⚡ Stopping Celery worker (PID: $CELERY_PID)..."
    kill $CELERY_PID 2>/dev/null
    rm -f celery.pid
fi

# Остановка всех Celery процессов
pkill -f "celery worker"

# Остановка Redis
echo "📡 Stopping Redis..."
brew services stop redis

# Остановка основного процесса (если запущен)
pkill -f "python.*main.py"

# Очистка лог файлов
rm -f celery.log nohup.out

echo "✅ All services stopped"