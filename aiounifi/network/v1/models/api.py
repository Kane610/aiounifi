"""Request and response types shared by all Network API v1 resources."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict, cast

import orjson

from ....errors import ResponseError

DEFAULT_PAGE_OFFSET = 0
DEFAULT_PAGE_LIMIT = 25
MAX_PAGE_LIMIT = 200


class ApiResponse(TypedDict):
    """Normalised response.

    List endpoints return this envelope as is. Endpoints that return one
    object, or nothing, are wrapped into the same shape by `ApiRequest.decode`
    so every interface reads `data` the same way.
    """

    data: list[dict[str, Any]]
    offset: NotRequired[int]
    limit: NotRequired[int]
    count: NotRequired[int]
    totalCount: NotRequired[int]


class ApiErrorResponse(TypedDict):
    """Error envelope returned with most 4xx and 5xx responses."""

    statusCode: int
    statusName: str
    code: str
    message: str
    timestamp: str
    requestPath: str
    requestId: str


@dataclass
class ApiRequest:
    """One request to the Network API v1."""

    method: str
    path: str
    params: Mapping[str, str | int] | None = None
    data: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        """Reject paths outside the versioned API."""
        if not self.path.startswith("/v1/"):
            raise ValueError(
                f"ApiRequest.path must start with '/v1/', got {self.path!r}"
            )

    def decode(self, raw: bytes) -> ApiResponse:
        """Decode a response body into the normalised envelope."""
        if not raw.strip():
            return ApiResponse(data=[])

        decoded: Any = orjson.loads(raw)

        if isinstance(decoded, dict) and isinstance(decoded.get("data"), list):
            return cast("ApiResponse", decoded)

        if isinstance(decoded, dict):
            return ApiResponse(data=[decoded])

        raise ResponseError(f"Unexpected Network API response for {self.path}")


def page_params(
    offset: int = DEFAULT_PAGE_OFFSET,
    limit: int = DEFAULT_PAGE_LIMIT,
    filter_value: str | None = None,
) -> dict[str, str | int]:
    """Build the query parameters of a list request.

    The console clamps `limit` to 200 itself; clamping here keeps the request
    honest about what it will get back.
    """
    params: dict[str, str | int] = {
        "offset": max(offset, DEFAULT_PAGE_OFFSET),
        "limit": max(min(limit, MAX_PAGE_LIMIT), 1),
    }
    if filter_value:
        params["filter"] = filter_value
    return params
