"""Exception types for the UniFi Network API v1.

Each class inherits from both `NetworkApiError` (which carries structured
metadata fields) and the matching base exception from `aiounifi.errors`, so
callers can catch either the broad base type or the structured v1 variant.
"""

from ...errors import (
    AuthenticationRateLimitError,
    BadGateway,
    Forbidden,
    NetworkApiError,
    ResponseError,
    ServiceUnavailable,
    Unauthorized,
)


class V1Unauthorized(NetworkApiError, Unauthorized):
    """Authentication failed on the Network API v1."""


class V1Forbidden(NetworkApiError, Forbidden):
    """Access forbidden on the Network API v1."""


class V1BadGateway(NetworkApiError, BadGateway):
    """Bad gateway response from the Network API v1."""


class V1ServiceUnavailable(NetworkApiError, ServiceUnavailable):
    """Service unavailable on the Network API v1."""


class V1ResponseError(NetworkApiError, ResponseError):
    """Generic non-success response from the Network API v1."""


class V1AuthenticationRateLimitError(NetworkApiError, AuthenticationRateLimitError):
    """Authentication rate limit reached on the Network API v1."""
