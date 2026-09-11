"""Connectivity for official UniFi Network Integration API calls."""

from __future__ import annotations

from http import HTTPStatus
import logging
from typing import TYPE_CHECKING, Any, cast

from aiohttp import client_exceptions
import orjson

from ...errors import (
    BadGateway,
    Forbidden,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    Unauthorized,
)
from .models.api import ApiErrorResponse, ApiRequest, ApiResponse

if TYPE_CHECKING:
    from ...models.configuration import Configuration

LOGGER = logging.getLogger(__name__)

API_KEY_HEADER = "X-API-KEY"

STATUS_EXCEPTION_MAP: dict[int, type[Exception]] = {
    HTTPStatus.UNAUTHORIZED: Unauthorized,
    HTTPStatus.FORBIDDEN: Forbidden,
    HTTPStatus.NOT_FOUND: ResponseError,
    HTTPStatus.TOO_MANY_REQUESTS: ResponseError,
    HTTPStatus.BAD_GATEWAY: BadGateway,
    HTTPStatus.SERVICE_UNAVAILABLE: ServiceUnavailable,
}


class Connectivity:
    """HTTP transport for the UniFi Network Integration API.

    API key authentication is handled here: every request sends `X-API-KEY`
    and no classic `/api/login` session is used.
    """

    def __init__(self, config: Configuration) -> None:
        """Initialize Integration API connectivity."""
        self.config = config
        self._session = config.session

    async def request(self, api_request: ApiRequest) -> ApiResponse:
        """Perform one Integration API request and decode the response."""
        api_key = self.config.api_key.strip()
        if not api_key:
            raise RequestError("api_key is required for network API requests")

        url = self._build_url(api_request.path)
        headers = {
            "Accept": "application/json",
            API_KEY_HEADER: api_key,
        }

        json_data: dict[str, Any] | None = (
            dict(api_request.data) if api_request.data else None
        )
        if json_data is not None:
            headers["Content-Type"] = "application/json"

        LOGGER.debug(
            "sending network request %s %s params=%s",
            api_request.method,
            url,
            api_request.params,
        )

        try:
            async with self._session.request(
                api_request.method,
                url,
                params=api_request.params,
                json=json_data,
                ssl=self.config.ssl_context,
                headers=headers,
            ) as response:
                body = await response.read()
        except client_exceptions.ClientError as err:
            raise RequestError(f"Error requesting data from {url}: {err}") from None

        LOGGER.debug("data (from %s) %s", url, body)

        if response.status >= HTTPStatus.BAD_REQUEST:
            error = self._parse_error_response(body)
            exception_type = STATUS_EXCEPTION_MAP.get(response.status, ResponseError)
            raise exception_type(self._error_message(url, response.status, error))

        try:
            return api_request.decode(body)
        except orjson.JSONDecodeError as err:
            raise ResponseError(
                f"Call {url} returned a non-JSON response for {api_request.path}"
            ) from err

    def _build_url(self, path: str) -> str:
        """Build local console Integration API URL."""
        return f"{self.config.url.rstrip('/')}/proxy/network/integration{path}"

    def _error_message(
        self,
        url: str,
        status: int,
        error: ApiErrorResponse | None,
    ) -> str:
        """Build an error message from a structured API error payload."""
        default_message = f"Call {url} received {status}"
        if error:
            return (
                f"{default_message}: {error['statusName']} {error['code']}: "
                f"{error['message']}"
            )
        return default_message

    def _parse_error_response(self, body: bytes) -> ApiErrorResponse | None:
        """Parse a structured API error response if the payload matches."""
        try:
            parsed = orjson.loads(body)
        except orjson.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        required_fields = {
            "statusCode",
            "statusName",
            "code",
            "message",
            "timestamp",
            "requestPath",
            "requestId",
        }
        if not required_fields.issubset(parsed):
            return None

        return cast("ApiErrorResponse", parsed)
