"""API management class and base class for the different end points."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
from typing import Final, final

from ..events import Event as UniFiEvent

SubscriptionType = Callable[..., None]

LOGGER = logging.getLogger(__name__)

SOURCE_DATA: Final = "data"
SOURCE_EVENT: Final = "event"


class APIItem:
    """Base class for all end points using APIItems class."""

    def __init__(
        self,
        raw: dict,
        request: Callable[..., Awaitable[list[dict]]],
    ) -> None:
        """Initialize API item."""
        self.raw = raw
        self._request = request
        self._event: UniFiEvent | None = None
        self._source = SOURCE_DATA
        self._callbacks: list[SubscriptionType] = []
        self._subscribers: list[SubscriptionType] = []

    @final
    @property
    def event(self) -> UniFiEvent | None:
        """Read only event data."""
        return self._event

    @final
    @property
    def last_updated(self) -> str:
        """Which source, data or event last called update."""
        return self._source

    def update(
        self,
        raw: dict | None = None,
        event: UniFiEvent | None = None,
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

    def subscribe(self, callback: SubscriptionType) -> Callable:
        """Subscribe to events.

        Return function to unsubscribe.
        """
        self._subscribers.append(callback)

        def unsubscribe():
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
