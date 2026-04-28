"""Library to communicate with a UniFi controller."""

from .controller import Controller
from .errors import (
    AiounifiException,
    AuthenticationRateLimitError,
    BadGateway,
    Forbidden,
    LoginRequired,
    NetworkApiError,
    NoPermission,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    TwoFaTokenRequired,
    Unauthorized,
    WebsocketError,
)
from .network import ApiClient

__all__ = [
    "AiounifiException",
    "ApiClient",
    "AuthenticationRateLimitError",
    "BadGateway",
    "Controller",
    "Forbidden",
    "LoginRequired",
    "NetworkApiError",
    "NoPermission",
    "RequestError",
    "ResponseError",
    "ServiceUnavailable",
    "TwoFaTokenRequired",
    "Unauthorized",
    "WebsocketError",
]
