from celery import Celery
from celery.signals import worker_shutting_down
import os
import sys


app = Celery(
    "instagram_bot",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

app.conf.update(
    worker_pool='gevent',
    worker_concurrency=4,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=False,
    broker_connection_retry_on_startup=True
)

app.autodiscover_tasks(['modules.tasks'])