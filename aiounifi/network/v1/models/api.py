"""Request and response typing for UniFi Network API."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict, cast

import orjson

from ....errors import ResponseError


class ApiResponse(TypedDict):
    """Network API generic envelope."""

    data: list[dict[str, Any]]
    offset: int
    limit: int
    count: int
    totalCount: int
    traceId: NotRequired[str]
    httpStatusCode: NotRequired[int]


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
        required_fields = ("offset", "limit", "count", "totalCount", "data")
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ResponseError(
                f"Network API response missing required field(s): {missing}"
            )
        return cast(ApiResponse, data)
