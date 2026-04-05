"""Request and response typing for official UniFi API."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypedDict, cast

import orjson

from ...errors import ResponseError


class OfficialApiResponse(TypedDict, total=False):
    """Official API generic envelope."""

    offset: int
    limit: int
    count: int
    totalCount: int
    data: list[dict[str, Any]]
    traceId: str
    httpStatusCode: int


@dataclass
class OfficialApiRequest:
    """Data class with required properties for official API requests."""

    method: str
    path: str
    params: Mapping[str, str | int] | None = None

    def decode(self, raw: bytes) -> OfficialApiResponse:
        """Decode official API envelope."""
        data: dict[str, Any] = orjson.loads(raw)
        if not isinstance(data, dict):
            raise ResponseError("Official API response is not an object")
        if "data" not in data:
            raise ResponseError("Official API response missing data field")
        return cast(OfficialApiResponse, data)
