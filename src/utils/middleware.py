import http
import json
import logging
import math
import time
from typing import Dict

from fastapi import Request, Response
from starlette.types import Receive, Scope, Send

from config.settings import PORT
from utils.logging import EMPTY_VALUE, RequestJsonLogSchema

requests_logger = logging.getLogger("requests")


def headers_from_scope(scope: Scope) -> Dict:
    return dict((k.decode().lower(), v.decode()) for k, v in scope["headers"])


class TranslationMiddleware:
    def __init__(self, app):
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if not scope["type"] == "http":
            await self._app(scope, receive, send)

        headers = self._get_headers(scope)
        self._activate_translation(headers)

        await self._app(scope, receive, send)

    def _get_headers(self, scope: Scope) -> Dict:
        return headers_from_scope(scope)

    def _activate_translation(self, headers: Dict) -> None:
        from config.i18n import activate_translation

        activate_translation(headers.get("accept-language", None))


class LoggingMiddleware:
    """
    Middleware для обработки запросов и ответов
    с целью журналирования (https://habr.com/ru/articles/575454/)
    """

    @staticmethod
    async def get_protocol(request: Request) -> str:
        protocol = str(request.scope.get("type", ""))
        http_version = str(request.scope.get("http_version", ""))
        if protocol.lower() == "http" and http_version:
            return f"{protocol.upper()}/{http_version}"
        return EMPTY_VALUE

    @staticmethod
    async def set_body(request: Request, body: bytes) -> None:
        async def receive():
            return {"type": "http.request", "body": body}

        request._receive = receive

    async def get_body(self, request: Request) -> Dict:
        body = await request.body()
        await self.set_body(request, body)
        return await request.json()

    async def __call__(self, request: Request, call_next, *args, **kwargs):
        if "docs" in str(request.url):
            return await call_next(request)
        start_time = time.time()
        exception_object = None
        # Request Side
        try:
            raw_request_body = await request.body()
            # Последующие действия нужны,
            # чтобы не перезатереть тело запроса
            # и не уйти в зависание event-loop'a
            # при последующем получении тела ответа
            await self.set_body(request, raw_request_body)
            request_body = await self.get_body(request)
        except Exception:
            request_body = EMPTY_VALUE

        server: tuple = request.get("server", ("localhost", PORT))
        request_headers: dict = dict(request.headers.items())
        # Response Side
        try:
            response = await call_next(request)
        except Exception as ex:
            response_body = bytes(http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase.encode())
            response = Response(
                content=response_body,
                status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR.real,
            )
            exception_object = ex
            response_headers = {}
        else:
            response_headers = dict(response.headers.items())
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        duration: int = math.ceil((time.time() - start_time) * 1000)
        response_body_str = response_body.decode()
        try:
            response_body_map = json.loads(response_body_str)
        except json.JSONDecodeError:
            response_body_map = None
        # Инициализация и формирования полей для запроса-ответа
        request_json_fields = RequestJsonLogSchema(
            request_uri=str(request.url),
            request_referer=request_headers.get("referer", EMPTY_VALUE),
            request_protocol=await self.get_protocol(request),
            request_method=request.method,
            request_path=request.url.path,
            request_host=f"{server[0]}:{server[1]}",
            request_size=int(request_headers.get("content-length", 0)),
            request_content_type=request_headers.get("content-type", EMPTY_VALUE),
            request_headers=request_headers,
            request_body=request_body or {},
            request_direction="in",
            remote_ip=request.client[0],
            remote_port=request.client[1],
            response_status_code=response.status_code,
            response_size=int(response_headers.get("content-length", 0)),
            response_headers=response_headers,
            response_body=response_body_map or {},
            duration=duration,
        ).model_dump()
        # Хочется на каждый запрос читать
        # и понимать в сообщении самое главное,
        # поэтому message мы сразу делаем типовым
        message = (
            f'{"Ошибка" if exception_object else "Ответ"} '
            f"с кодом {response.status_code} "
            f'на запрос {request.method} "{str(request.url)}", '
            f"за {duration} мс"
        )
        getattr(requests_logger, "error" if exception_object else "info")(
            message,
            extra={
                "request_json_fields": request_json_fields,
                "to_mask": True,
            },
            exc_info=exception_object,
        )
        return response
