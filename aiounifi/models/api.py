"""API management class and base class for the different end points."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import TYPE_CHECKING, Any, Final, final

from .event import Event

if TYPE_CHECKING:
    from ..controller import Controller

SubscriptionType = Callable[..., None]
UnsubscribeType = Callable[[], None]

LOGGER = logging.getLogger(__name__)

SOURCE_DATA: Final = "data"
SOURCE_EVENT: Final = "event"


class APIItem:
    """Base class for all end points using APIItems class."""

    def __init__(
        self,
        raw: Any,
        controller: Controller,
    ) -> None:
        """Initialize API item."""
        self.raw = raw
        self._controller = controller
        self._request = controller.request
        self._event: Event | None = None
        self._source = SOURCE_DATA
        self._callbacks: list[SubscriptionType] = []
        self._subscribers: list[SubscriptionType] = []

    @final
    @property
    def event(self) -> Event | None:
        """Read only event data."""
        return self._event

    @final
    @property
    def last_updated(self) -> str:
        """Which source, data or event last called update."""
        return self._source

    def update(
        self,
        raw: dict[str, Any] | None = None,
        event: Event | None = None,
    ) -> None:
        """Update raw data and signal new data is available."""
        if raw:
            self.raw = raw
            self._source = SOURCE_DATA

        elif event:
            self._event = event
            self._source = SOURCE_EVENT

        else:
            return None

        for signal_update in self._callbacks + self._subscribers:
            signal_update()

    def subscribe(self, callback: SubscriptionType) -> UnsubscribeType:
        """Subscribe to events.

        Return function to unsubscribe.
        """
        self._subscribers.append(callback)

        def unsubscribe() -> None:
            self._subscribers.remove(callback)

        return unsubscribe

    @final
    def register_callback(self, callback: SubscriptionType) -> None:
        """Register callback for signalling.

        Callback will be used by update.
        """
        self._callbacks.append(callback)

    @final
    def remove_callback(self, callback: SubscriptionType) -> None:
        """Remove registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    @final
    def clear_callbacks(self) -> None:
        """Clear all registered callbacks."""
        self._callbacks.clear()
