"""API management class and base class for the different end points."""

from __future__ import annotations

from collections.abc import Callable, ItemsView, Iterator, ValuesView
import logging
from typing import Any, Final, final

from ..models.event import Event
from ..models.message import Message
from ..models.request_object import RequestObject

SubscriptionType = Callable[[str, str], None]
UnsubscribeType = Callable[[], None]

LOGGER = logging.getLogger(__name__)

SOURCE_DATA: Final = "data"
SOURCE_EVENT: Final = "event"


class APIHandler:
    """Base class for a map of API Items."""

    obj_id_key: str
    path: str
    item_cls: Any
    events: tuple = ()
    process_messages: tuple = ()
    remove_messages: tuple = ()

    def __init__(self, controller) -> None:
        """Initialize API items."""
        self.controller = controller
        self._items: dict[int | str, Any] = {}
        self._subscribers: list[SubscriptionType] = []

        if message_filter := self.process_messages + self.remove_messages:
            controller.messages.subscribe(self.process_message, message_filter)

        if self.events:
            controller.events.subscribe(self.process_event, self.events)

    @final
    async def update(self) -> None:
        """Refresh data."""
        raw = await self.controller.request(RequestObject("get", self.path, None))
        self.process_raw(raw)

    def process_raw(self, raw: list[dict[str, Any]]) -> set:
        """Process full raw response."""
        new_items = set()
        for raw_item in raw:
            if obj_id := self.process_item(raw_item):
                new_items.add(obj_id)
        return new_items

    def process_message(self, message: Message) -> str:
        """Process and forward websocket data."""
        if message.meta.message in self.process_messages:
            return self.process_item(message.data)

        if message.meta.message in self.remove_messages:
            return self.remove_item(message.data)

        return ""

    @final
    def process_event(self, event: Event) -> None:
        """Process event."""
        if (obj := self._items.get(event.mac)) is not None:
            obj.update(event=event)

    @final
    def process_item(self, raw: dict[str, Any]) -> str:
        """Process item data."""
        if self.obj_id_key not in raw:
            return ""

        if (obj_id := raw[self.obj_id_key]) in self._items:
            obj = self._items[obj_id]
            obj.update(raw=raw)
            return ""

        self._items[obj_id] = self.item_cls(raw, self.controller)

        for callback in self._subscribers:
            callback("added", obj_id)

        return obj_id

    @final
    def remove_item(self, raw: dict[str, Any]) -> str:
        """Remove item."""
        if (obj_id := raw[self.obj_id_key]) in self._items:
            obj = self._items.pop(obj_id)
            obj.clear_callbacks()
            return obj_id
        return ""

    def subscribe(self, callback: SubscriptionType) -> UnsubscribeType:
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
        """Return items dictionary."""
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
