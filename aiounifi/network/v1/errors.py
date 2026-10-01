"""Exceptions raised by the UniFi Network Integration API v1.

Each class inherits from both `NetworkApiError`, which carries the structured
fields of the API error envelope, and the matching legacy base exception, so
callers can catch either the broad type or the structured v1 variant.
"""

from ...errors import (
    AuthenticationRateLimitError,
    BadGateway,
    EndpointNotFound,
    Forbidden,
    NetworkApiError,
    ResponseError,
    ServiceUnavailable,
    Unauthorized,
)


class V1Unauthorized(NetworkApiError, Unauthorized):
    """The API key is missing or rejected."""


class V1Forbidden(NetworkApiError, Forbidden):
    """The API key may not access the resource."""


class V1NotFound(NetworkApiError, EndpointNotFound):
    """The resource or endpoint does not exist."""


class V1BadGateway(NetworkApiError, BadGateway):
    """Bad gateway response from the console."""


class V1ServiceUnavailable(NetworkApiError, ServiceUnavailable):
    """The Network application is not available."""


class V1ResponseError(NetworkApiError, ResponseError):
    """Any other non-success response."""


class V1AuthenticationRateLimitError(NetworkApiError, AuthenticationRateLimitError):
    """Too many failed authentication attempts."""
