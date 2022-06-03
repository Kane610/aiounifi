"""API management class and base class for the different end points."""

from __future__ import annotations

from collections.abc import Callable, ItemsView, Iterator, ValuesView
import logging
from typing import Any, Final, final

from aiounifi.models.event import MessageKey

from ..events import Event as UniFiEvent

SubscriptionType = Callable[[str, str], None]

LOGGER = logging.getLogger(__name__)

SOURCE_DATA: Final = "data"
SOURCE_EVENT: Final = "event"


class APIItems:
    """Base class for a map of API Items."""

    obj_id_key: str
    path: str
    item_cls: Any
    events: tuple = ()
    messages: tuple = ()
    removes: tuple = ()

    def __init__(self, controller) -> None:
        """Initialize API items."""
        self.controller = controller
        self._items: dict[int | str, Any] = {}
        self._subscribers: list[SubscriptionType] = []

        if self.events:
            controller.events.subscribe(
                self.process_event, MessageKey.EVENT, event_filter=self.events
            )
        if self.messages:
            controller.events.subscribe(self.process_raw, self.messages)
        if self.removes:
            controller.events.subscribe(self.remove, self.removes)

    @final
    async def update(self) -> None:
        """Refresh data."""
        raw = await self.controller.request("get", self.path)
        self.process_raw(raw)

    @final
    def process_raw(self, raw: list[dict[str, Any]]) -> set:
        """Process data."""
        new_items = set()

        for raw_item in raw:
            key = raw_item[self.obj_id_key]

            if (obj := self._items.get(key)) is not None:
                obj.update(raw=raw_item)
                continue

            self._items[key] = self.item_cls(raw_item, self.controller.request)
            new_items.add(key)

            for callback in self._subscribers:
                callback("added", key)

        return new_items

    @final
    def process_event(self, event: UniFiEvent) -> set:
        """Process event."""
        new_item = set()
        if (obj := self._items.get(event.mac)) is not None:
            obj.update(event=event)
            new_item.add(event.mac)
        return new_item

    @final
    def remove(self, raw: list[dict[str, Any]]) -> set:
        """Remove list of items."""
        removed_items = set()

        for raw_item in raw:
            key = raw_item[self.obj_id_key]

            if key in self._items:
                item = self._items.pop(key)
                item.clear_callbacks()
                removed_items.add(key)

        return removed_items

    def subscribe(self, callback: SubscriptionType) -> Callable:
        """Subscribe to added events.

        "callback" - callback function to call when an event emits.
        Return function to unsubscribe.
        """
        self._subscribers.append(callback)

        def unsubscribe():
            self._subscribers.remove(callback)

        return unsubscribe

    @final
    def items(self) -> ItemsView[int | str, Any]:
        """Return item dictionary."""
        return self._items.items()

    @final
    def values(self) -> ValuesView[Any]:
        """Return items."""
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
