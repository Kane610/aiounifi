"""API management class and base class for the different end points."""

from abc import ABC
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypedDict, TypeVar

import orjson

from ..errors import (
    AiounifiException,
    LoginRequired,
    NoPermission,
    TwoFaTokenRequired,
    Unauthorized,
)

ERRORS = {
    "api.err.Invalid": Unauthorized,
    "api.err.LoginRequired": LoginRequired,
    "api.err.NoPermission": NoPermission,
    "api.err.Ubic2faTokenRequired": TwoFaTokenRequired,
}


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
        data: TypedApiResponse = orjson.loads(raw)

        if "meta" in data and data["meta"]["rc"] == "error":
            raise ERRORS.get(data["meta"]["msg"], AiounifiException)(data)

        return data


@dataclass
class ApiRequestV2(ApiRequest):
    """Data class with required properties of a V2 API request."""

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        """Create url to work with a specific controller."""
        if is_unifi_os:
            return f"/proxy/network/v2/api/site/{site}{self.path}"
        return f"/v2/api/site/{site}{self.path}"

    def decode(self, raw: bytes) -> TypedApiResponse:
        """Put data, received from the unifi controller, into a TypedApiResponse."""
        data = orjson.loads(raw)

        if "errorCode" in data:
            raise ERRORS.get(data["message"], AiounifiException)(data)

        return TypedApiResponse(
            meta={"rc": "ok", "msg": ""},
            data=data if isinstance(data, list) else [data],
        )


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
