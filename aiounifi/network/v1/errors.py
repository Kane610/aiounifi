"""Errors for the official UniFi Network Integration API."""

from dataclasses import dataclass
from http import HTTPStatus

from aiounifi.errors import AiounifiException, LoginRequired, RequestError, Unauthorized


class NetworkApiError(AiounifiException):
    """Raised when the official Network Integration API returns an error."""


@dataclass
class ApiErrorBody:
    """Error payload returned by the official Network Integration API."""

    status_code: int
    code: str | None = None
    message: str | None = None
    status_name: str | None = None
    timestamp: str | None = None
    request_id: str | None = None

    @property
    def http_status(self) -> HTTPStatus | None:
        """Return HTTP status enum when the status code is valid."""
        try:
            return HTTPStatus(self.status_code)
        except ValueError:
            return None


def raise_for_status(status: int, body: object) -> None:
    """Raise the appropriate exception for a non-success HTTP response."""
    error = parse_error_body(status, body)
    message = error.message or HTTPStatus(status).phrase

    if status == HTTPStatus.UNAUTHORIZED:
        raise Unauthorized(message)
    if status == HTTPStatus.FORBIDDEN:
        raise LoginRequired(message)
    raise NetworkApiError(message)


def parse_error_body(status: int, body: object) -> ApiErrorBody:
    """Parse a structured Integration API error payload."""
    if not isinstance(body, dict):
        return ApiErrorBody(status_code=status, message=str(body) if body else None)

    return ApiErrorBody(
        status_code=status,
        code=body.get("code"),
        message=body.get("message"),
        status_name=body.get("statusName"),
        timestamp=body.get("timestamp"),
        request_id=body.get("requestId"),
    )
