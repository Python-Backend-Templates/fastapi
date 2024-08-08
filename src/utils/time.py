from datetime import datetime, timedelta

import pytz

from config import settings


def get_current_time() -> datetime:
    return datetime.now(tz=pytz.timezone(settings.TIMEZONE))


def timestamp_to_datetime(timestamp: float) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=pytz.timezone(settings.TIMEZONE))


def get_current_time_with_delta(**delta_kwargs) -> datetime:
    return get_current_time() + timedelta(**delta_kwargs)
