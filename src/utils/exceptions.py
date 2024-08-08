import logging
from typing import Any, Dict

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.utils import is_body_allowed_for_status_code
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from config.i18n import _

logger = logging.getLogger("exceptions")


class CustomException(HTTPException):
    pass


class Custom400Exception(CustomException):
    def __init__(
        self, detail: Any = None, headers: Dict[str, str] | None = None
    ) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, headers)


class Custom401Exception(CustomException):
    def __init__(
        self, detail: Any = None, headers: Dict[str, str] | None = None
    ) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, headers)


class Custom403Exception(CustomException):
    def __init__(
        self, detail: Any = None, headers: Dict[str, str] | None = None
    ) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, headers)


class Custom404Exception(CustomException):
    def __init__(
        self, detail: Any = None, headers: Dict[str, str] | None = None
    ) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, headers)


def custom_exception_handler(request: Request, exc: HTTPException) -> Response:
    headers = getattr(exc, "headers", None)
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=headers)
    return JSONResponse(
        {"detail": exc.detail}, status_code=exc.status_code, headers=headers
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = {}
    for error in exc._errors:
        errors["__".join(error.get("loc")[1:])] = error.get("msg")
    logger.info(
        f"Validation error has occured - {str(exc)}",
        extra={"built_msg": errors},
        exc_info=exc,
    )
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(errors)},
    )


async def internal_exception_handler(request: Request, exc: Exception):
    logger.critical(
        f"An internal error has occured - {str(exc)}",
        exc_info=exc,
    )
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": _("An internal error has occurred.")},
    )
