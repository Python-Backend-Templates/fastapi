import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Literal, Mapping, Tuple, Type, TypeAlias, TypeVar

import httpx
from httpx import AsyncHTTPTransport, HTTPError
from httpx._client import AsyncClient
from pydantic import BaseModel, ValidationError

from utils.exceptions import Custom400Exception, Custom404Exception

Headers: TypeAlias = Dict[str, str]
Data: TypeAlias = Dict[str, str]
JSON: TypeAlias = Mapping[str, Any]
Params: TypeAlias = Dict[str, str]
Response: TypeAlias = Dict[str, Any]
PathParams: TypeAlias = Dict[str, str]


TResponse = TypeVar("TResponse", bound=BaseModel)


class ThirdPartyRequest(BaseModel):
    headers: Headers | None = None
    data: Data | None = None
    json_: JSON | None = None
    params: Params | None = None
    path_params: PathParams | None = None


class ThirdPartyEmptyResponse(BaseModel):
    pass


class IThirdPartyAPICall(ABC, Generic[TResponse]):
    @abstractmethod
    async def __call__(self, entry: ThirdPartyRequest) -> TResponse:
        """
        ### Args:
            entry: dataclass with request data

        ### Raises:
            Custom400Exception - if there were an error sending request
                or response is not succesful;
            Custom404Exception - if response is not successful with 404 status code.
        """


class ThirdPartyAPICall(IThirdPartyAPICall[TResponse]):
    def __init__(
        self,
        url: str,
        method: Literal["get", "post"],
        response_class: Type[BaseModel],
        max_retries: int,
        timeout: int,
        error_message: str,
        logger: logging.Logger,
        log_headers: Tuple[str, ...] = tuple(),
    ) -> None:
        self.url = url
        self.method = method
        self.response_class = response_class
        self.max_retries = max_retries
        self.timeout = timeout
        self.error_message = error_message
        self.logger = logger
        self.log_headers = log_headers

    async def __call__(self, entry: ThirdPartyRequest) -> TResponse:
        response = await self._send(entry)
        self._check_success(response, entry)
        result = self._result(response, entry)
        self._log(error=False, entry=entry, response=response)
        return result

    async def _send(self, entry: ThirdPartyRequest) -> httpx.Response:
        try:
            transport = AsyncHTTPTransport(retries=self.max_retries)
            async with AsyncClient(transport=transport) as client:
                kwargs = {
                    "url": self._build_url(entry),
                    "headers": entry.headers,
                    "params": entry.params,
                    "timeout": self.timeout,
                }
                if self.method == "post":
                    kwargs["data"] = entry.data
                    kwargs["json"] = entry.json_  # type:ignore[assignment]
                return await getattr(client, self.method)(**kwargs)
        except HTTPError as e:
            self._log(error=True, entry=entry, exc=e)

    def _build_url(self, entry: ThirdPartyRequest) -> str:
        if not entry.path_params:
            return self.url
        url = self.url
        for param, value in entry.path_params.items():
            url = url.replace("{" + param + "}", value)
        return url

    def _check_success(
        self,
        response: httpx.Response,
        entry: ThirdPartyRequest,
    ) -> None:
        if response.status_code // 100 != 2:
            self._log(error=True, entry=entry, response=response)

    def _result(  # type:ignore[return]
        self,
        response: httpx.Response,
        entry: ThirdPartyRequest,
    ) -> TResponse:
        try:
            obj = response.json()
        except Exception:
            return ThirdPartyEmptyResponse()

        logging.debug(obj)
        try:
            return self.response_class(**obj)
        except ValidationError as e:
            self._log(error=True, entry=entry, response=response, exc=e)

    def _log(
        self,
        *,
        error: bool,
        entry: ThirdPartyRequest,
        response: httpx.Response | None = None,
        exc: Exception | None = None,
    ) -> None:
        msg = (
            f"API Call Failed - {str(exc)}."
            if exc
            else "API Call Failed." if error else "API Call Succeeded."
        )
        logging.debug(msg)
        (self.logger.error if error else self.logger.info)(
            msg,
            extra={
                "url": self.url,
                "method": self.method,
                "request": entry.model_dump(),
                "status_code": response.status_code if response is not None else None,
                "response": (
                    response.content.decode()
                    if response is not None and response.content
                    else None
                ),
                "headers": (
                    {
                        header: response.headers.get(header, None)
                        for header in self.log_headers
                    }
                    if response
                    else None
                ),
            },
        )
        if error:
            exc_class = (
                Custom404Exception
                if response is not None and response.status_code == 404
                else Custom400Exception
            )
            raise exc_class(self.error_message)
