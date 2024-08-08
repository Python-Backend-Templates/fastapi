import logging
from typing import Iterable

from sqlalchemy.exc import SQLAlchemyError

orm_logger = logging.getLogger("orm")


def apply_tags(tags: Iterable[str]):
    """
    Декоратор используется для добавления тегов к роутерам
    """

    def outer(func):
        def inner(*args, **kwargs):
            routers = func(*args, **kwargs)
            for router in routers:
                router.tags = list(set([*(router.tags or list()), *tags]))
            return routers

        return inner

    return outer


def handle_orm_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            orm_logger.error(
                f"Error while processing orm query - {str(e)}",
                extra={"func_args": args, "func_kwargs": kwargs},
                exc_info=e,
            )
            raise

    return wrapper
