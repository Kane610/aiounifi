"""API management class and base class for the different end points."""

from abc import ABC
from dataclasses import dataclass
from typing import Any, TypeVar


@dataclass
class ApiRequest:
    """Data class with required properties of a request."""

    method: str
    path: str
    data: dict[str, Any] | None

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        """Create url to work with a specific controller."""
        if is_unifi_os:
            return f"/proxy/network/api/s/{site}{self.path}"
        return f"/api/s/{site}{self.path}"


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
