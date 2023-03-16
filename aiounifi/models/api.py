"""API management class and base class for the different end points."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..controller import Controller


class APIItem:
    """Base class for all end points using APIItems class."""

    def __init__(self, raw: Any, controller: "Controller") -> None:
        """Initialize API item."""
        self.raw = raw
        self._controller = controller
        self._request = controller.request

    def update(self, raw: dict[str, Any] | None = None) -> None:
        """Update raw data and signal new data is available."""
        if raw:
            self.raw = raw
