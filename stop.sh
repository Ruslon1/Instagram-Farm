#!/bin/bash

echo "🛑 Stopping Instagram Bot..."

# Остановка Celery workers по PID файлу
if [ -f celery.pid ]; then
    CELERY_PID=$(cat celery.pid)
    if ps -p $CELERY_PID > /dev/null 2>&1; then
        echo "⚡ Stopping Celery worker (PID: $CELERY_PID)..."
        kill $CELERY_PID 2>/dev/null
        rm -f celery.pid
    else
        echo "⚠️  Celery PID file exists, but process not found. Cleaning up..."
        rm -f celery.pid
    fi
fi

# Остановка всех Celery процессов
echo "⚡ Stopping all Celery workers..."
pkill -f "celery worker"

# Остановка Redis
echo "📡 Stopping Redis..."
if brew services list | grep -q "redis.*started"; then
    brew services stop redis
else
    echo "⚠️  Redis is not running via Homebrew. Attempting manual stop..."
    pkill redis-server 2>/dev/null || echo "Redis server not found."
fi

# Остановка основного процесса (если запущен)
echo "🛠️  Stopping main process..."
pkill -f "python.*main.py"

# Очистка лог файлов
echo "🧹 Cleaning up log files..."
rm -f celery.log nohup.out

echo "✅ All services stopped"