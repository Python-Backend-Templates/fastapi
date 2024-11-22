import functools
import logging
from typing import Any, Callable, Iterable

from sqlalchemy.exc import SQLAlchemyError

orm_logger = logging.getLogger("orm")
common_logger = logging.getLogger("common")


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


def handle_any_error(
    func: Callable | None = None,
    *,
    logger: logging.Logger = common_logger,
):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logging.debug(str(e))
                logger.error(
                    f"Unexpected error - {str(e)}",
                    exc_info=e,
                )
                raise

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator


def session(func) -> Callable:
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        from config.di import Container

        if "session" in kwargs.keys():
            return await func(*args, **kwargs)

        async with Container.db().session() as session:
            kwargs["session"] = session
            return await func(*args, **kwargs)

    return wrapper
