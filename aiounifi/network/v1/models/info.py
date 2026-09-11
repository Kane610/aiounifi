"""Application info models for UniFi Network Integration API v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self, TypedDict, cast

import orjson

from ....errors import ResponseError
from ....models.api import ApiItem
from .api import ApiRequest, ApiResponse


class ApplicationInfoData(TypedDict):
    """Typed payload for GET /v1/info."""

    applicationVersion: str


@dataclass
class InfoRequest(ApiRequest):
    """Request for Integration API application info."""

    @classmethod
    def create(cls) -> Self:
        """Construct an application info request."""
        return cls(method="get", path="/v1/info")

    def decode(self, raw: bytes) -> ApiResponse:
        """Decode the non-paginated application info object."""
        data: dict[str, Any] = orjson.loads(raw)
        if not isinstance(data, dict) or "applicationVersion" not in data:
            raise ResponseError("Network API info response is invalid")
        return ApiResponse(
            data=[data],
            offset=0,
            limit=1,
            count=1,
            totalCount=1,
        )


class ApplicationInfo(ApiItem):
    """Represent application info from the Integration API."""

    raw: ApplicationInfoData

    @property
    def application_version(self) -> str:
        """UniFi Network application version."""
        return self.raw["applicationVersion"]

    @classmethod
    def from_response(cls, response: ApiResponse) -> ApplicationInfo:
        """Create application info from a decoded API response."""
        return cls(cast("ApplicationInfoData", response["data"][0]))
