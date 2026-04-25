"""API management class and base class for the different end points."""

from __future__ import annotations

from collections.abc import ItemsView, Iterator, ValuesView
from typing import TYPE_CHECKING, Any, Generic, final

from ..models.api import ApiItemT, ApiRequest
from ..subscription import (
    ID_FILTER_ALL,
    CallbackType,
    ItemEvent,
    SubscriptionHandler,
    SubscriptionType,
    UnsubscribeType,
)

if TYPE_CHECKING:
    from ..controller import Controller
    from ..models.message import Message, MessageKey

__all__ = [
    "ID_FILTER_ALL",
    "APIHandler",
    "CallbackType",
    "ItemEvent",
    "SubscriptionHandler",
    "SubscriptionType",
    "UnsubscribeType",
]


class APIHandler(SubscriptionHandler, Generic[ApiItemT]):
    """Base class for a map of API Items."""

    obj_id_key: str
    item_cls: type[ApiItemT]
    api_request: ApiRequest
    process_messages: tuple[MessageKey, ...] = ()
    remove_messages: tuple[MessageKey, ...] = ()

    def __init__(self, controller: Controller) -> None:
        """Initialize API handler."""
        super().__init__()
        self.controller = controller
        self._items: dict[str, ApiItemT] = {}

        if message_filter := self.process_messages + self.remove_messages:
            controller.messages.subscribe(self.process_message, message_filter)

    @final
    async def update(self) -> None:
        """Refresh data."""
        raw = await self.controller.request(self.api_request)
        self.process_raw(raw.get("data", []))

    @final
    def process_raw(self, raw: list[dict[str, Any]]) -> None:
        """Process full raw response."""
        for raw_item in raw:
            self.process_item(raw_item)

    @final
    def process_message(self, message: Message) -> None:
        """Process and forward websocket data."""
        if message.meta.message in self.process_messages:
            self.process_item(message.data)

        elif message.meta.message in self.remove_messages:
            self.remove_item(message.data)

    @final
    def process_item(self, raw: dict[str, Any]) -> None:
        """Process item data."""
        if self.obj_id_key not in raw:
            return

        obj_id: str
        obj_is_known = (obj_id := raw[self.obj_id_key]) in self._items
        self._items[obj_id] = self.item_cls(raw)

        self.signal_subscribers(
            ItemEvent.CHANGED if obj_is_known else ItemEvent.ADDED,
            obj_id,
        )

    @final
    def remove_item(self, raw: dict[str, Any]) -> None:
        """Remove item."""
        obj_id: str
        if (obj_id := raw[self.obj_id_key]) in self._items:
            self._items.pop(obj_id)
            self.signal_subscribers(ItemEvent.DELETED, obj_id)

    @final
    def items(self) -> ItemsView[str, ApiItemT]:
        """Return items dictionary."""
        return self._items.items()

    @final
    def values(self) -> ValuesView[ApiItemT]:
        """Return items."""
        return self._items.values()

    @final
    def get(self, obj_id: str, default: Any | None = None) -> ApiItemT | None:
        """Get item value based on key, return default if no match."""
        return self._items.get(obj_id, default)

    @final
    def __contains__(self, obj_id: str) -> bool:
        """Validate membership of item ID."""
        return obj_id in self._items

    @final
    def __getitem__(self, obj_id: str) -> ApiItemT:
        """Get item value based on key."""
        return self._items[obj_id]

    @final
    def __iter__(self) -> Iterator[str]:
        """Allow iterate over items."""
        return iter(self._items)
