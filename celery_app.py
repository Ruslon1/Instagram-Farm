#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Получаем абсолютный путь к корневой директории проекта
PROJECT_ROOT = Path(__file__).parent.absolute()
print(f"🔧 Project root: {PROJECT_ROOT}")

# Добавляем корневую директорию в PYTHONPATH
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    print(f"✅ Added {PROJECT_ROOT} to Python path")

# Устанавливаем переменную окружения
os.environ['PYTHONPATH'] = f"{PROJECT_ROOT}:{os.environ.get('PYTHONPATH', '')}"

# Выводим отладочную информацию
print(f"📍 Current working directory: {os.getcwd()}")
print(f"📍 Python executable: {sys.executable}")
print(f"📍 Python path: {sys.path[:3]}...")  # Показываем первые 3 элемента

# Тестируем импорты
try:
    print("🧪 Testing imports...")

    # Проверяем, что файлы существуют
    modules_dir = PROJECT_ROOT / "modules"
    config_dir = PROJECT_ROOT / "config"

    print(f"📁 modules directory exists: {modules_dir.exists()}")
    print(f"📁 config directory exists: {config_dir.exists()}")

    if modules_dir.exists():
        print(f"📁 modules contents: {list(modules_dir.iterdir())}")

    # Пробуем импортировать
    from config.settings import settings

    print("✅ Successfully imported config.settings")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📋 Available directories:")
    for item in PROJECT_ROOT.iterdir():
        if item.is_dir():
            print(f"  📁 {item.name}")
    sys.exit(1)

# Теперь импортируем Celery
from celery import Celery
from celery.signals import worker_shutting_down

# Создаем приложение Celery
app = Celery(
    "instagram_bot",
    broker=settings.get_celery_broker_url(),
    backend=settings.get_celery_result_backend()
)

# Конфигурация Celery
app.conf.update(
    worker_pool='solo',
    worker_concurrency=1,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=False,
    broker_connection_retry_on_startup=True,
    # Принудительно указываем модули для импорта
    include=[
        'modules.tasks',
    ],
    imports=[
        'modules.tasks',
    ]
)

# Пробуем зарегистрировать задачи вручную
try:
    print("🔍 Trying to import modules.tasks...")
    import modules.tasks

    print("✅ modules.tasks imported successfully")

    # Автоматическое обнаружение задач
    app.autodiscover_tasks(['modules'])
    print("✅ Tasks autodiscovered")

except ImportError as e:
    print(f"❌ Failed to import modules.tasks: {e}")
    print("🔧 Available modules:")
    try:
        import modules

        print(f"   modules.__file__: {modules.__file__}")
        import pkgutil

        for importer, modname, ispkg in pkgutil.iter_modules(modules.__path__):
            print(f"   📦 {modname}")
    except Exception as ex:
        print(f"   ❌ Can't explore modules: {ex}")

print("🎯 Celery app configured successfully")

if __name__ == '__main__':
    print("🚀 Starting Celery worker...")
    app.start()