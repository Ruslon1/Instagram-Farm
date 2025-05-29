from celery import Celery
import os

app = Celery(
    "instagram_bot",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

app.conf.update(
    worker_pool='gevent',  # Changed from 'solo' to 'gevent'
    worker_concurrency=4,  # Number of concurrent workers
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,  # Better handling of interrupted tasks
    broker_connection_retry_on_startup=True
)

app.autodiscover_tasks(['modules.tasks'])
