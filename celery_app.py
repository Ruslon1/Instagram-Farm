import os
import sys
from celery import Celery
from celery.signals import worker_shutting_down

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings

app = Celery(
    "instagram_bot",
    broker=settings.get_celery_broker_url(),
    backend=settings.get_celery_result_backend()
)

app.conf.update(
    worker_pool='solo',  # Изменено с 'gevent' на 'solo' для Docker
    worker_concurrency=1,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=False,
    broker_connection_retry_on_startup=True,
    # Добавляем настройки для импорта
    include=['modules.tasks'],
    imports=['modules.tasks']
)

# Автоматическое обнаружение задач
app.autodiscover_tasks(['modules'])

if __name__ == '__main__':
    app.start()