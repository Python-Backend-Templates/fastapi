from celery import Celery

app = Celery("celery_app")
app.config_from_object("config.celery_config")
app.autodiscover_tasks()
