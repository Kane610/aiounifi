"""API management class and base class for the different end points."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, ItemsView, Iterator, ValuesView
import logging
from pprint import pformat
from typing import Any, Final, final

from .events import Event as UniFiEvent

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
        self._raw = raw
        self._request = request
        self._event: UniFiEvent | None = None
        self._source = SOURCE_DATA
        self._callbacks: list[Callable] = []

    @final
    @property
    def raw(self) -> dict:
        """Read only raw data."""
        return self._raw

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
            self._raw = raw
            self._source = SOURCE_DATA

        elif event:
            self._event = event
            self._source = SOURCE_EVENT

        else:
            return None

        for signal_update in self._callbacks:
            signal_update()

    @final
    def register_callback(self, callback: Callable) -> None:
        """Register callback for signalling.

        Callback will be used by update.
        """
        self._callbacks.append(callback)

    @final
    def remove_callback(self, callback: Callable) -> None:
        """Remove registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    @final
    def clear_callbacks(self) -> None:
        """Clear all registered callbacks."""
        self._callbacks.clear()


class APIItems:
    """Base class for a map of API Items."""

    KEY = ""

    def __init__(
        self,
        raw: list,
        request: Callable[..., Awaitable[list[dict]]],
        path: str,
        item_cls: Any,
    ) -> None:
        """Initialize API items."""
        self._request = request
        self._path = path
        self._item_cls = item_cls
        self._items: dict[int | str, Any] = {}
        self.process_raw(raw)
        LOGGER.debug(pformat(raw))

    @final
    async def update(self) -> None:
        """Refresh data."""
        raw = await self._request("get", self._path)
        self.process_raw(raw)

    @final
    def process_raw(self, raw: list[dict]) -> set:
        """Process data."""
        new_items = set()

        for raw_item in raw:
            key = raw_item[self.KEY]

            if (obj := self._items.get(key)) is not None:
                obj.update(raw=raw_item)

            else:
                self._items[key] = self._item_cls(raw_item, self._request)
                new_items.add(key)

        return new_items

    @final
    def process_event(self, events: list[UniFiEvent]) -> set:
        """Process event."""
        new_items = set()

        for event in events:

            if (obj := self._items.get(event.mac)) is not None:
                obj.update(event=event)
                new_items.add(event.mac)

        return new_items

    @final
    def remove(self, raw: list) -> set:
        """Remove list of items."""
        removed_items = set()

        for raw_item in raw:
            key = raw_item[self.KEY]

            if key in self._items:
                item = self._items.pop(key)
                item.clear_callbacks()
                removed_items.add(key)

        return removed_items

    @final
    def items(self) -> ItemsView[int | str, Any]:
        """Return item values."""
        return self._items.items()

    @final
    def values(self) -> ValuesView[Any]:
        """Return item values."""
        return self._items.values()

    @final
    def get(
        self,
        obj_id: int | str,
        default: Any | None = None,
    ) -> Any | None:
        """Get item value based on key, return default if no match."""
        return self._items.get(obj_id, default)

    @final
    def __contains__(self, obj_id: int | str) -> bool:
        """Validate membership of item ID."""
        return obj_id in self._items

    @final
    def __getitem__(self, obj_id: int | str) -> Any:
        """Get item value based on key."""
        return self._items[obj_id]

    @final
    def __iter__(self) -> Iterator[int | str]:
        """Allow iterate over items."""
        return iter(self._items)
