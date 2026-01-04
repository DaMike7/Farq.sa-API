from celery import Celery
from app.core.config import settings
from app.tasks.csv_import import import_csv_to_db

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.task_routes = {
    "app.tasks.csv_import.import_csv_to_db": "main-queue",
}

celery_app.autodiscover_tasks(["app.tasks"])