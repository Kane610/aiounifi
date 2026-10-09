"""HTTP transport for the Network API v1.

One attempt per request, with one exception: a `502 Bad Gateway` is what
nginx on the console answers when the Network application cannot keep up,
so it is retried a few times with a short backoff before `V1BadGateway` is
raised. Everything else is raised at once; retrying is the caller's job. A
failed response is mapped to an exception in this order, most specific
first:

1. The `code` of a structured error envelope.
2. The `statusName` of a structured error envelope.
3. The HTTP status as a plain integer.
4. `V1ResponseError`.

The status is used as an integer, never through `HTTPStatus(status)`, so a
non-standard code from a proxy still resolves to the fallback instead of
raising `ValueError`. A rejected API key is the case that needs step 3: the
console answers `{"error": {"code": 401, "message": "Unauthorized"}}`, not
the structured envelope.

There is no request budget to keep. Ubiquiti documents no request-rate limit
for the Network Integration API and its OpenAPI description declares no 429
response; the one limit it has is on failed authentications, which no amount
of waiting fixes. Should a console answer 429 anyway, it is raised as
`V1TooManyRequests` with `retry_after` taken from the `Retry-After` header,
so a polling caller can hold off for that long.
"""

from __future__ import annotations

from asyncio import sleep
from collections.abc import Mapping
from http import HTTPStatus
import logging
from typing import TYPE_CHECKING, cast

from aiohttp import client_exceptions
import orjson

from ...errors import NetworkApiError, RequestError
from .errors import (
    V1AuthenticationRateLimitError,
    V1BadGateway,
    V1Forbidden,
    V1NotFound,
    V1ResponseError,
    V1ServiceUnavailable,
    V1TooManyRequests,
    V1Unauthorized,
)

if TYPE_CHECKING:
    from ...models.configuration import Configuration
    from .models.api import ApiErrorResponse, ApiRequest, ApiResponse

LOGGER = logging.getLogger(__name__)

STATUS_EXCEPTION_MAP: dict[int, type[NetworkApiError]] = {
    HTTPStatus.UNAUTHORIZED: V1Unauthorized,
    HTTPStatus.FORBIDDEN: V1Forbidden,
    HTTPStatus.NOT_FOUND: V1NotFound,
    HTTPStatus.TOO_MANY_REQUESTS: V1TooManyRequests,
    HTTPStatus.BAD_GATEWAY: V1BadGateway,
    HTTPStatus.SERVICE_UNAVAILABLE: V1ServiceUnavailable,
}

STATUS_NAME_EXCEPTION_MAP: dict[str, type[NetworkApiError]] = {
    "UNAUTHORIZED": V1Unauthorized,
    "FORBIDDEN": V1Forbidden,
    "NOT_FOUND": V1NotFound,
    "TOO_MANY_REQUESTS": V1TooManyRequests,
    "BAD_GATEWAY": V1BadGateway,
    "SERVICE_UNAVAILABLE": V1ServiceUnavailable,
}

ERROR_CODE_EXCEPTION_MAP: dict[str, type[NetworkApiError]] = {
    "api.authentication.failed-limit-reached": V1AuthenticationRateLimitError,
    "api.authentication.invalid-credentials": V1Unauthorized,
    "api.authentication.missing-credentials": V1Unauthorized,
    "api.resource-not-found": V1NotFound,
}

ERROR_ENVELOPE_FIELDS = frozenset(
    {
        "statusCode",
        "statusName",
        "code",
        "message",
        "timestamp",
        "requestPath",
        "requestId",
    }
)


class Connectivity:
    """Send requests to the Network API v1 with an API key."""

    bad_gateway_retries = 2
    """How many times a 502 is retried before it is raised."""
    bad_gateway_backoff = 0.5
    """Seconds before the first retry of a 502; doubled for each retry after."""

    def __init__(self, config: Configuration) -> None:
        """Initialize."""
        self.config = config

    @property
    def base_url(self) -> str:
        """Root of the Integration API on the console."""
        return f"{self.config.url}/proxy/network/integration"

    async def request(self, api_request: ApiRequest) -> ApiResponse:
        """Send one request and decode the response."""
        api_key = (self.config.api_key or "").strip()
        if not api_key:
            raise RequestError("An api_key is required for Network API v1 requests")

        url = f"{self.base_url}{api_request.path}"
        headers = {"Accept": "application/json", "X-API-KEY": api_key}
        body: bytes | None = None
        if api_request.data is not None:
            body = orjson.dumps(api_request.data)
            headers["Content-Type"] = "application/json"

        LOGGER.debug(
            "sending %s %s params=%s", api_request.method, url, api_request.params
        )

        for attempt in range(self.bad_gateway_retries + 1):
            try:
                async with self.config.session.request(
                    api_request.method,
                    url,
                    params=api_request.params,
                    data=body,
                    headers=headers,
                    ssl=self.config.ssl_context,
                ) as response:
                    raw = await response.read()
            except client_exceptions.ClientError as err:
                raise RequestError(f"Error requesting data from {url}: {err}") from None

            if (
                response.status != HTTPStatus.BAD_GATEWAY
                or attempt == self.bad_gateway_retries
            ):
                break
            delay = self.bad_gateway_backoff * 2**attempt
            LOGGER.debug("%s answered 502, retrying in %.1fs", url, delay)
            await sleep(delay)

        LOGGER.debug("data (from %s) %s", url, raw[:4000])

        if response.status >= HTTPStatus.BAD_REQUEST:
            error = self._parse_error(raw)
            exception_type = self._exception_type(response.status, error)
            exception = self._build_exception(
                exception_type, url, response.status, error
            )
            exception.retry_after = self._retry_after(response.headers)
            raise exception

        try:
            return api_request.decode(raw)
        except orjson.JSONDecodeError as err:
            raise V1ResponseError(
                f"Call {url} returned a non-JSON response: {raw[:200]!r}"
            ) from err

    @staticmethod
    def _parse_error(raw: bytes) -> ApiErrorResponse | None:
        """Return the structured error envelope, if the body is one."""
        try:
            parsed = orjson.loads(raw)
        except orjson.JSONDecodeError:
            return None
        if isinstance(parsed, dict) and parsed.keys() >= ERROR_ENVELOPE_FIELDS:
            return cast("ApiErrorResponse", parsed)
        return None

    @staticmethod
    def _exception_type(
        status: int, error: ApiErrorResponse | None
    ) -> type[NetworkApiError]:
        """Pick the exception for a failed response."""
        if error is not None:
            if exception_type := ERROR_CODE_EXCEPTION_MAP.get(error["code"]):
                return exception_type
            if exception_type := STATUS_NAME_EXCEPTION_MAP.get(error["statusName"]):
                return exception_type
        return STATUS_EXCEPTION_MAP.get(status, V1ResponseError)

    @staticmethod
    def _retry_after(headers: Mapping[str, str]) -> int | None:
        """Seconds from a `Retry-After` header, if it holds a number."""
        value = headers.get("Retry-After", "")
        return int(value) if value.isdigit() else None

    @staticmethod
    def _build_exception(
        exception_type: type[NetworkApiError],
        url: str,
        status: int,
        error: ApiErrorResponse | None,
    ) -> NetworkApiError:
        """Build the exception and copy the envelope fields onto it."""
        message = f"Call {url} received {status}"
        if error is not None:
            message = (
                f"{message}: {error['statusName']} {error['code']}: "
                f"{error['message']} (requestId={error['requestId']})"
            )
        exception = exception_type(message)
        exception.status_code = status
        if error is not None:
            exception.status_name = error["statusName"]
            exception.code = error["code"]
            exception.detail = error["message"]
            exception.timestamp = error["timestamp"]
            exception.request_path = error["requestPath"]
            exception.request_id = error["requestId"]
        return exception
