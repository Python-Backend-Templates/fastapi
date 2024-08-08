from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Sequence,
    Union,
)

from fastapi import FastAPI as _FastAPI
from fastapi import routing
from fastapi.applications import AppType, logger
from fastapi.datastructures import Default, State
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
    websocket_request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from fastapi.params import Depends
from fastapi.utils import generate_unique_id
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan

from utils.routing import APIRouter


class FastAPI(_FastAPI):
    def __init__(
        self: AppType,
        *,
        debug: bool = False,
        routes: List[BaseRoute] | None = None,
        title: str = "FastAPI",
        summary: str | None = None,
        description: str = "",
        version: str = "0.1.0",
        openapi_url: str | None = "/openapi.json",
        openapi_tags: List[Dict[str, Any]] | None = None,
        servers: List[Dict[str, str | Any]] | None = None,
        dependencies: Sequence[Depends] | None = None,
        default_response_class: type[Response] = Default(JSONResponse),
        redirect_slashes: bool = True,
        docs_url: str | None = "/docs",
        redoc_url: str | None = "/redoc",
        swagger_ui_oauth2_redirect_url: str | None = "/docs/oauth2-redirect",
        swagger_ui_init_oauth: Dict[str, Any] | None = None,
        middleware: Sequence[Middleware] | None = None,
        exception_handlers: (
            Dict[
                int | type[Exception],
                Callable[[Request, Any], Coroutine[Any, Any, Response]],
            ]
            | None
        ) = None,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
        lifespan: Lifespan[AppType] | None = None,
        terms_of_service: str | None = None,
        contact: Dict[str, str | Any] | None = None,
        license_info: Dict[str, str | Any] | None = None,
        openapi_prefix: str = "",
        root_path: str = "",
        root_path_in_servers: bool = True,
        responses: Dict[int | str, Dict[str, Any]] | None = None,
        callbacks: List[BaseRoute] | None = None,
        webhooks: APIRouter | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        swagger_ui_parameters: Dict[str, Any] | None = None,
        generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(
            generate_unique_id
        ),
        separate_input_output_schemas: bool = True,
        **extra: Any
    ) -> None:
        self.debug = debug
        self.title = title
        self.summary = summary
        self.description = description
        self.version = version
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
        self.openapi_url = openapi_url
        self.openapi_tags = openapi_tags
        self.root_path_in_servers = root_path_in_servers
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.swagger_ui_oauth2_redirect_url = swagger_ui_oauth2_redirect_url
        self.swagger_ui_init_oauth = swagger_ui_init_oauth
        self.swagger_ui_parameters = swagger_ui_parameters
        self.servers = servers or []
        self.separate_input_output_schemas = separate_input_output_schemas
        self.extra = extra
        self.openapi_version = "3.1.0"
        self.openapi_schema: Optional[Dict[str, Any]] = None
        if self.openapi_url:
            assert self.title, "A title must be provided for OpenAPI, e.g.: 'My API'"
            assert self.version, "A version must be provided for OpenAPI, e.g.: '2.1.0'"
        if openapi_prefix:
            logger.warning(
                '"openapi_prefix" has been deprecated in favor of "root_path", which '
                "follows more closely the ASGI standard, is simpler, and more "
                "automatic. Check the docs at "
                "https://fastapi.tiangolo.com/advanced/sub-applications/"
            )
        self.webhooks = webhooks or routing.APIRouter()
        self.root_path = root_path or openapi_prefix
        self.state: State = State()
        self.dependency_overrides: Dict[Callable[..., Any], Callable[..., Any]] = {}
        self.router: routing.APIRouter = APIRouter(
            routes=routes,
            redirect_slashes=redirect_slashes,
            dependency_overrides_provider=self,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            default_response_class=default_response_class,
            dependencies=dependencies,
            callbacks=callbacks,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
            generate_unique_id_function=generate_unique_id_function,
        )
        self.exception_handlers: Dict[
            Any, Callable[[Request, Any], Union[Response, Awaitable[Response]]]
        ] = ({} if exception_handlers is None else dict(exception_handlers))
        self.exception_handlers.setdefault(HTTPException, http_exception_handler)
        self.exception_handlers.setdefault(
            RequestValidationError, request_validation_exception_handler
        )
        self.exception_handlers.setdefault(
            WebSocketRequestValidationError,
            # Starlette still has incorrect type specification for the handlers
            websocket_request_validation_exception_handler,  # type: ignore
        )

        self.user_middleware: List[Middleware] = (
            [] if middleware is None else list(middleware)
        )
        self.middleware_stack: Union[ASGIApp, None] = None
        self.setup()
