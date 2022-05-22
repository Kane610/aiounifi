"""API management class and base class for the different end points."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, ItemsView, Iterator, ValuesView
import logging
from pprint import pformat
from typing import Any, Final, final

from ..events import Event as UniFiEvent

LOGGER = logging.getLogger(__name__)

SOURCE_DATA: Final = "data"
SOURCE_EVENT: Final = "event"


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
