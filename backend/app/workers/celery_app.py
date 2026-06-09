from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "careeros_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Auto-discover tasks in workers module
celery_app.autodiscover_tasks(["app.workers"])

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Configure periodic sync checks (Celery Beat)
    beat_schedule={
        "sync-emails-every-10-minutes": {
            "task": "app.workers.tasks.trigger_all_users_sync",
            "schedule": 600.0, # Every 10 minutes
        },
        "detect-followups-once-a-day": {
            "task": "app.workers.tasks.detect_all_users_followups",
            "schedule": 86400.0, # Every 24 hours
        }
    }
)
