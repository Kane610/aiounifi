"""Shared request typing contracts for legacy and Network API clients."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, TypeVar

ResponseT_co = TypeVar("ResponseT_co", covariant=True)


class RequestProtocol(Protocol[ResponseT_co]):
    """Structural contract for request objects executed by connectivity layers."""

    method: str
    path: str
    data: Mapping[str, Any] | None

    def decode(self, raw: bytes) -> ResponseT_co:
        """Decode the raw response payload into a typed response object."""


class LegacyRequestProtocol(RequestProtocol[ResponseT_co], Protocol[ResponseT_co]):
    """Request contract for legacy and v2 requests requiring site expansion."""

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        """Build the endpoint path for a specific site and deployment."""


class V1RequestProtocol(RequestProtocol[ResponseT_co], Protocol[ResponseT_co]):
    """Request contract for Network API v1 requests supporting query params."""

    params: Mapping[str, str | int] | None
