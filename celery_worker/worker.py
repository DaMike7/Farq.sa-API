# celery_worker/worker.py

from celery import Celery
import logging

logger = logging.getLogger(__name__)

logger.info("Initializing Celery worker with explicit Redis URL")

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["app.tasks.csv_import"],  # Explicitly include tasks
)

# Force config
celery_app.conf.update(
    task_routes={
        "app.tasks.csv_import.import_csv_to_db": "main-queue",
    },
    task_default_queue="main-queue",
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
)

logger.info("Celery worker initialized with broker: redis://redis:6379/0")