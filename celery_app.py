from celery import Celery

import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

app = Celery(
    "instagram_bot",
    broker="redis://localhost:6379/0",  # Протокол Redis и базовый номер базы данных
    backend="redis://localhost:6379/0"  # Протокол Redis и базовый номер базы данных
)

app.conf.update(
    worker_pool='solo',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

app.autodiscover_tasks(['modules.tasks'])
