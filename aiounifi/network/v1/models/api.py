"""Request and response typing for UniFi Network API."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypedDict, cast

import orjson

from ....errors import ResponseError


class ApiResponse(TypedDict, total=False):
    """Network API generic envelope."""

    offset: int
    limit: int
    count: int
    totalCount: int
    data: list[dict[str, Any]]
    traceId: str
    httpStatusCode: int


@dataclass
class ApiRequest:
    """Data class with required properties for network API requests."""

    method: str
    path: str
    params: Mapping[str, str | int] | None = None

    def decode(self, raw: bytes) -> ApiResponse:
        """Decode network API envelope."""
        data: dict[str, Any] = orjson.loads(raw)
        if not isinstance(data, dict):
            raise ResponseError("Network API response is not an object")
        if "data" not in data:
            raise ResponseError("Network API response missing data field")
        return cast(ApiResponse, data)
