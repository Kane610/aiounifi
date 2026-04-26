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


class V1RequestProtocol(RequestProtocol[ResponseT_co], Protocol[ResponseT_co]):
    """Request contract for Network API v1 requests supporting query params."""

    params: Mapping[str, str | int] | None
