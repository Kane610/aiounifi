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

    def prepare_data(self, raw: bytes) -> TypedApiResponse:
        """Put data, received from the unifi controller, into a TypedApiResponse."""
        json_data = orjson.loads(raw)
        return_data: TypedApiResponse = {}

        return_data["meta"] = json_data.get("meta", None)
        return_data["data"] = json_data.get("data", None)

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
