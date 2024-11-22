import os

from celery import Celery

app = Celery(
    "celery_app",
    broker=os.environ.get("CELERY_BROKER_URL"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", None),
)
app.config_from_object("config.celery_config")
app.autodiscover_tasks()

app.conf.beat_schedule = {}
