from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Create Celery instance
celery_app = Celery(
    'capstone',
    broker=f'redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}',
    backend=f'redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}',
    include=['app.tasks'],
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'send-scheduled-notifications': {
        'task': 'app.tasks.send_scheduled_notifications',
        'schedule': crontab(minute='*'),  # Run every minute
    },
}

__all__ = ['celery_app']
