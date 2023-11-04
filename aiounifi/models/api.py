"""API management class and base class for the different end points."""

from abc import ABC
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypedDict, TypeVar

import orjson


class TypedApiResponse(TypedDict, total=False):
    """Common response."""

    meta: dict[str, Any]
    data: list[dict[str, Any]]


@dataclass
class ApiRequest:
    """Data class with required properties of a request."""

    method: str
    path: str
    data: Mapping[str, Any] | None = None

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        """Create url to work with a specific controller."""
        if is_unifi_os:
            return f"/proxy/network/api/s/{site}{self.path}"
        return f"/api/s/{site}{self.path}"

    def decode(self, raw: bytes) -> TypedApiResponse:
        """Put data, received from the unifi controller, into a TypedApiResponse."""
        return_data: TypedApiResponse = orjson.loads(raw)
        return return_data


@dataclass
class ApiRequestV2(ApiRequest):
    """Data class with required properties of a V2 API request."""

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        """Create url to work with a specific controller."""
        if is_unifi_os:
            return f"/proxy/network/v2/api/site/{site}{self.path}"
        return f"/v2/api/site/{site}{self.path}"

    def handle_error(self, json: dict[str, Any]) -> dict[str, Any]:
        """Handle errors in the response, if any, and put them in a common format."""
        if "errorCode" in json:
            meta = {"rc": "error", "msg": json["message"]}
            return meta

        return {"rc": "ok", "msg": ""}

    def decode(self, raw: bytes) -> TypedApiResponse:
        """Put data, received from the unifi controller, into a TypedApiResponse."""
        json_data = orjson.loads(raw)
        return_data: TypedApiResponse = {}
        return_data["meta"] = self.handle_error(json_data)
        return_data["data"] = json_data if isinstance(json_data, list) else [json_data]
        return return_data


# @dataclass
# class ApiItem(ABC):
#     """Base class for all end points using APIItems class."""

#     raw: Any


class ApiItem(ABC):
    """Base class for all end points using APIItems class."""

    def __init__(self, raw: Any) -> None:
        """Initialize API item."""
        self.raw = raw


ApiItemT = TypeVar("ApiItemT", bound=ApiItem)
