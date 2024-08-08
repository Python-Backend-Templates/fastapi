import os

from kombu import Exchange, Queue

TIMEZONE = "Europe/Moscow"
TASK_TRACK_STARTED = True
TASK_TIME_LIMIT = 30 * 60
WORKER_MAX_TASKS_PER_CHILD = 25

BROKER_URL = os.environ.get("CELERY_BROKER_URL")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND")

TASK_QUEUES = (
    Queue("high", Exchange("high"), routing_key="high"),
    Queue("normal", Exchange("normal"), routing_key="normal"),
    Queue("low", Exchange("low"), routing_key="low"),
)

DEFAULT_QUEUE = "normal"
DEFAULT_EXCHANGE = "normal"
DEFAULT_ROUTING_KEY = "normal"

CELERY_TASK_ROUTES = {
    # -- HIGH PRIORITY QUEUE -- #
    # -- NORMAL PRIORITY QUEUE -- #
    "celery.*": {"queue": "normal"},
    # -- LOW PRIORITY QUEUE -- #
}
