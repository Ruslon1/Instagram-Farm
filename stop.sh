#!/bin/bash

echo "🛑 Stopping Instagram Bot..."

# Остановка Celery workers по PID файлу
if [ -f celery.pid ]; then
    CELERY_PID=$(cat celery.pid)
    if ps -p $CELERY_PID > /dev/null 2>&1; then
        echo "⚡ Stopping Celery worker (PID: $CELERY_PID)..."
        kill -TERM $CELERY_PID 2>/dev/null
        sleep 3
        # Если процесс все еще работает, принудительно убиваем
        if ps -p $CELERY_PID > /dev/null 2>&1; then
            echo "🔥 Force killing Celery worker (PID: $CELERY_PID)..."
            kill -KILL $CELERY_PID 2>/dev/null
        fi
        rm -f celery.pid
    else
        echo "⚠️  Celery PID file exists, but process not found. Cleaning up..."
        rm -f celery.pid
    fi
fi

# Остановка всех Celery процессов более агрессивно
echo "⚡ Stopping all Celery workers..."
# Найти все процессы celery и убить их
CELERY_PIDS=$(ps aux | grep "celery.*worker" | grep -v grep | awk '{print $2}')
if [ ! -z "$CELERY_PIDS" ]; then
    echo "🔍 Found Celery processes: $CELERY_PIDS"
    for PID in $CELERY_PIDS; do
        echo "⚡ Killing Celery process $PID..."
        kill -TERM $PID 2>/dev/null
        sleep 2
        # Проверяем, остался ли процесс
        if ps -p $PID > /dev/null 2>&1; then
            echo "🔥 Force killing process $PID..."
            kill -KILL $PID 2>/dev/null
        fi
    done
else
    echo "✅ No Celery processes found"
fi

# Дополнительная проверка celery процессов
sleep 2
REMAINING_CELERY=$(ps aux | grep "celery.*worker" | grep -v grep)
if [ ! -z "$REMAINING_CELERY" ]; then
    echo "⚠️  Some Celery processes still running:"
    echo "$REMAINING_CELERY"
    echo "🔥 Force killing remaining processes..."
    pkill -9 -f "celery.*worker"
fi

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

# Остановка uvicorn процессов
echo "🌐 Stopping uvicorn processes..."
pkill -f "uvicorn"

# Очистка лог файлов
echo "🧹 Cleaning up log files..."
rm -f celery.log nohup.out

# Финальная проверка
echo "🔍 Final check for remaining processes..."
REMAINING_PROCESSES=$(ps aux | grep -E "(celery|uvicorn|main.py)" | grep -v grep)
if [ ! -z "$REMAINING_PROCESSES" ]; then
    echo "⚠️  Some processes still running:"
    echo "$REMAINING_PROCESSES"
    echo "🔥 Force killing all remaining processes..."
    pkill -9 -f "celery"
    pkill -9 -f "uvicorn"
    pkill -9 -f "main.py"
fi

echo "✅ All services stopped"