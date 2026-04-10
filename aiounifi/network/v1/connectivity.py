"""Connectivity for UniFi Network API calls.

Error handling in this module intentionally uses a layered resolution strategy
for non-success HTTP responses:

1) Structured API error code (`code`) when present.
2) Structured API status name (`statusName`) when present.
3) Raw HTTP status integer mapping.
4) Generic `ResponseError` fallback.

Using the raw integer status avoids converting unknown status codes through
`HTTPStatus(...)`, which can raise `ValueError` for non-standard upstream
statuses. This keeps failure behavior stable even when intermediaries return
vendor-specific status codes.
"""

from __future__ import annotations

from http import HTTPStatus
import logging
from typing import TYPE_CHECKING, cast

from aiohttp import client_exceptions
import orjson

from ...errors import (
    AiounifiException,
    AuthenticationRateLimitError,
    BadGateway,
    Forbidden,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    Unauthorized,
)

if TYPE_CHECKING:
    from ...models.configuration import Configuration
    from .models.api import ApiErrorResponse, ApiRequest, ApiResponse

LOGGER = logging.getLogger(__name__)

STATUS_EXCEPTION_MAP: dict[int, type[AiounifiException]] = {
    HTTPStatus.UNAUTHORIZED: Unauthorized,
    HTTPStatus.FORBIDDEN: Forbidden,
    HTTPStatus.NOT_FOUND: ResponseError,
    HTTPStatus.TOO_MANY_REQUESTS: ResponseError,
    HTTPStatus.BAD_GATEWAY: BadGateway,
    HTTPStatus.SERVICE_UNAVAILABLE: ServiceUnavailable,
}

STATUS_NAME_EXCEPTION_MAP: dict[str, type[AiounifiException]] = {
    "UNAUTHORIZED": Unauthorized,
    "FORBIDDEN": Forbidden,
    "BAD_GATEWAY": BadGateway,
    "SERVICE_UNAVAILABLE": ServiceUnavailable,
}

ERROR_CODE_EXCEPTION_MAP: dict[str, type[AiounifiException]] = {
    "api.authentication.failed-limit-reached": AuthenticationRateLimitError,
    "api.authentication.invalid-credentials": Unauthorized,
    "api.authentication.missing-credentials": Unauthorized,
}


class Connectivity:
    """Manage HTTP requests against the UniFi Network API.

    For error responses, this class resolves exception types in a deterministic
    order from most specific semantics to broad transport fallback. Raised
    exceptions may include structured metadata attributes (`status_code`,
    `status_name`, `code`, `detail`, `timestamp`, `request_path`, `request_id`)
    when the response body matches the API error envelope.
    """

    def __init__(self, config: Configuration) -> None:
        """Initialize Network API connectivity."""
        self.config = config

    async def request(self, api_request: ApiRequest) -> ApiResponse:
        """Perform one request to the Network API and decode the response.

        On HTTP error responses (>= 400), exception selection is delegated to
        `_exception_type`, which applies the semantic-first resolution order
        documented in this module.
        """
        if not self.config.network_api_key:
            raise RequestError("network_api_key is required for network API requests")

        url = self._build_url(api_request.path)
        params = api_request.params
        headers = {
            "Accept": "application/json",
            "X-API-Key": self.config.network_api_key,
        }

        # Prepare request body if data is present
        json_data = None
        if api_request.data:
            json_data = orjson.dumps(api_request.data)
            headers["Content-Type"] = "application/json"

        LOGGER.debug(
            "sending network request %s %s params=%s", api_request.method, url, params
        )

        try:
            async with self.config.session.request(
                api_request.method,
                url,
                params=params,
                data=json_data,
                ssl=self.config.ssl_context,
                headers=headers,
            ) as response:
                body = await response.read()
        except client_exceptions.ClientError as err:
            raise RequestError(f"Error requesting data from {url}: {err}") from None

        if response.status >= HTTPStatus.BAD_REQUEST:
            error = self._parse_error_response(body)
            exception_type = self._exception_type(response.status, error)
            raise self._build_exception(
                exception_type, url, response.status, body, error
            )

        return api_request.decode(body)

    def _build_url(self, path: str) -> str:
        """Build direct Network API URL for a path."""
        return f"{self.config.network_api_url.rstrip('/')}{path}"

    def _build_exception(
        self,
        exception_type: type[AiounifiException],
        url: str,
        status: int,
        body: bytes,
        error: ApiErrorResponse | None = None,
    ) -> AiounifiException:
        """Build an exception and attach structured error fields when available."""
        message = self._error_message(url, status, body, error)
        exc = exception_type(message)

        # Always include HTTP status for programmatic handling.
        setattr(exc, "status_code", status)

        if error is None:
            error = self._parse_error_response(body)

        if error:
            setattr(exc, "status_name", error["statusName"])
            setattr(exc, "code", error["code"])
            setattr(exc, "detail", error["message"])
            setattr(exc, "timestamp", error["timestamp"])
            setattr(exc, "request_path", error["requestPath"])
            setattr(exc, "request_id", error["requestId"])

        return exc

    def _error_message(
        self,
        url: str,
        status: int,
        body: bytes,
        error: ApiErrorResponse | None = None,
    ) -> str:
        """Build a detailed error message from a structured API error payload."""
        default_message = f"Call {url} received {status}"

        if error is None:
            error = self._parse_error_response(body)

        if error:
            details = (
                f"{error['statusName']} {error['code']}: {error['message']} "
                f"(requestId={error['requestId']}, requestPath={error['requestPath']})"
            )
            return f"{default_message}: {details}"

        return default_message

    def _parse_error_response(self, body: bytes) -> ApiErrorResponse | None:
        """Parse a structured API error response if the payload matches expected keys."""

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

    def _exception_type(
        self, status: int, error: ApiErrorResponse | None
    ) -> type[AiounifiException]:
        """Resolve the most specific exception type for a failed response.

        Resolution order:
        1. Structured error code map (`ERROR_CODE_EXCEPTION_MAP`).
        2. Structured status-name map (`STATUS_NAME_EXCEPTION_MAP`).
        3. Raw HTTP status map (`STATUS_EXCEPTION_MAP`).
        4. `ResponseError` fallback.

        The `status` argument is treated as an integer and not converted to an
        `HTTPStatus` enum, so unknown/non-standard codes still map safely to
        the generic fallback.
        """
        if error:
            if exception_type := ERROR_CODE_EXCEPTION_MAP.get(error["code"]):
                return exception_type
            if exception_type := STATUS_NAME_EXCEPTION_MAP.get(error["statusName"]):
                return exception_type

        return STATUS_EXCEPTION_MAP.get(status, ResponseError)
