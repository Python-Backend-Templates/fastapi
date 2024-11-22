import os

DB_USER: str = os.environ.get("DB_USER", "")
DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")
DB_NAME: str = os.environ.get("DB_NAME", "")
DB_HOST: str = os.environ.get("DB_HOST", "")
DB_PORT: str = os.environ.get("DB_PORT", "")
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

TIMEZONE = os.environ.get("TIMEZONE")

DEBUG = bool(int(os.environ.get("DEBUG", 0)))
PROD = bool(int(os.environ.get("PROD", 1)))

LOGGING_MAX_BYTES = int(os.environ.get("LOGGING_MAX_BYTES", 1024 * 3))
LOGGING_BACKUP_COUNT = int(os.environ.get("LOGGING_BACKUP_COUNT", 1))
LOGGING_LOGGERS = os.environ.get("LOGGING_LOGGERS", "").split(",")
LOGGING_SENSITIVE_FIELDS = os.environ.get("LOGGING_SENSITIVE_FIELDS", "").split(",")
LOGGING_PATH = os.environ.get("LOG_PATH")

PORT = os.environ.get("ASGI_PORT")
