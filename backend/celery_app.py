from celery import Celery
from celery.signals import worker_shutting_down
from config.settings import settings
import os
import sys


app = Celery(
    "instagram_bot",
    broker=settings.get_celery_broker_url(),
    backend=settings.get_celery_result_backend()
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