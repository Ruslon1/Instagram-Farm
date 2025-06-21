#!/bin/bash

echo "🚀 Starting Instagram Bot..."

# Проверка Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Добавление Homebrew в PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Проверка и установка Redis
if ! command -v redis-server &> /dev/null; then
    echo "🔴 Installing Redis..."
    brew install redis
fi

# Проверка Redis
if ! pgrep redis-server > /dev/null; then
    echo "📡 Starting Redis..."
    brew services start redis
    sleep 3
fi

# Проверка подключения к Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis connection failed. Starting manually..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis started manually"
    else
        echo "❌ Failed to start Redis"
        exit 1
    fi
fi

# Создание необходимых директорий
mkdir -p videos sessions

# Инициализация базы данных
echo "🗄️ Initializing database..."
python3 -c "from modules.database import init_database; init_database()"

# Проверка Python зависимостей
echo "📦 Checking Python dependencies..."
python3 -c "import celery, redis" 2>/dev/null || {
    echo "❌ Missing dependencies. Installing..."
    pip install celery redis gevent
}

# Запуск Celery worker в фоне
echo "⚡ Starting Celery worker..."
nohup celery -A celery_app worker --loglevel=info --pool=solo > celery.log 2>&1 &
CELERY_PID=$!

sleep 5

# Проверка Celery
if ps -p $CELERY_PID > /dev/null; then
    echo "✅ Celery worker is running (PID: $CELERY_PID)"
    echo $CELERY_PID > celery.pid
else
    echo "❌ Celery worker failed to start. Check celery.log:"
    tail -n 10 celery.log
    exit 1
fi

# Запуск основного скрипта
echo "🎬 Starting main application..."
python3 main.py