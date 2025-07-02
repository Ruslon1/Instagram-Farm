#!/bin/bash

# Скрипт запуска Celery с правильным PYTHONPATH
echo "🚀 Starting Celery worker..."

# Устанавливаем PYTHONPATH
export PYTHONPATH="/app:${PYTHONPATH}"

# Переходим в рабочую директорию
cd /app

# Показываем текущие пути
echo "📍 Current directory: $(pwd)"
echo "📍 PYTHONPATH: $PYTHONPATH"
echo "📍 Available files:"
ls -la

echo "📍 Available modules:"
ls -la modules/ 2>/dev/null || echo "modules directory not found"

echo "📍 Python can import:"
python -c "import sys; print('sys.path:', sys.path)" || echo "Python import test failed"

# Тестируем импорт модулей
echo "🧪 Testing imports..."
python -c "
try:
    import modules
    print('✅ modules imported successfully')
    import modules.tasks
    print('✅ modules.tasks imported successfully')
    import config.settings
    print('✅ config.settings imported successfully')
except Exception as e:
    print(f'❌ Import failed: {e}')
    import sys
    print(f'Python path: {sys.path}')
    import os
    print(f'Current dir contents: {os.listdir(\".\")}')
"

echo "🔧 Starting Celery with explicit app path..."

# Запускаем Celery
exec celery -A celery_app worker --loglevel=info --pool=solo --concurrency=1