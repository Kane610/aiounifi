"""Aiounifi errors."""


class AiounifiException(Exception):
    """Base error for aiounifi."""


class RequestError(AiounifiException):
    """Unable to fulfill request.

    Raised when host or API cannot be reached.
    """


class ResponseError(AiounifiException):
    """Invalid response."""


class Unauthorized(AiounifiException):
    """Username is not authorized."""


class LoginRequired(AiounifiException):
    """User is logged out."""


class Forbidden(AiounifiException):
    """Forbidden request."""


class NoPermission(AiounifiException):
    """Users permissions are read only."""


class ServiceUnavailable(RequestError):
    """Service is unavailable.

    Common error if controller is restarting and behind a proxy.
    """


class BadGateway(RequestError):
    """Invalid response from the upstream server."""


# Raised when login attempt limit is reached (HTTP 429 AUTHENTICATION_FAILED_LIMIT_REACHED)
class AuthenticationRateLimitError(AiounifiException):
    """Raised when login attempt limit is reached (HTTP 429)."""


class TwoFaTokenRequired(AiounifiException):
    """2 factor authentication token required."""


class NetworkApiError(AiounifiException):
    """Structured error from the UniFi Network API v1.

    Attributes are populated from the API error envelope when available,
    allowing callers to inspect error details programmatically without
    parsing exception message strings.
    """

    status_code: int = 0
    status_name: str = ""
    code: str = ""
    detail: str = ""
    timestamp: str = ""
    request_path: str = ""
    request_id: str = ""


class WebsocketError(AiounifiException):
    """Websocket error."""
