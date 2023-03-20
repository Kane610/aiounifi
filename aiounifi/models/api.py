"""API management class and base class for the different end points."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..controller import Controller


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


class APIItem:
    """Base class for all end points using APIItems class."""

    def __init__(self, raw: Any, controller: "Controller") -> None:
        """Initialize API item."""
        self.raw = raw
        self._controller = controller

    def update(self, raw: dict[str, Any] | None = None) -> None:
        """Update raw data and signal new data is available."""
        if raw:
            self.raw = raw
