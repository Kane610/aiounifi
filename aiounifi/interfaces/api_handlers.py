"""API management class and base class for the different end points."""

from __future__ import annotations

from abc import ABC
from collections import defaultdict
from collections.abc import Callable, ItemsView, Iterator, ValuesView
import contextlib
import enum
import logging
from typing import TYPE_CHECKING, Any, Generic, final

from ..models.api import ApiItemT, ApiRequest

if TYPE_CHECKING:
    from ..controller import Controller
    from ..models.message import Message, MessageKey

logger = logging.getLogger(__name__)


class ItemEvent(enum.Enum):
    """The event action of the item."""

    ADDED = "added"
    CHANGED = "changed"
    DELETED = "deleted"


CallbackType = Callable[[ItemEvent, str], None]
SubscriptionType = tuple[CallbackType, tuple[ItemEvent, ...] | None]
UnsubscribeType = Callable[[], None]

ID_FILTER_ALL = "*"


class SubscriptionHandler(ABC):
    """Manage subscription and notification to subscribers."""

    def __init__(self) -> None:
        """Initialize subscription handler."""
        self._subscribers: defaultdict[str, list[SubscriptionType]] = defaultdict(list)

    def signal_subscribers(self, event: ItemEvent, obj_id: str) -> None:
        """Signal subscribers."""
        # Check specific ID subscribers and wildcard subscribers
        for subscription_list in [
            self._subscribers[obj_id],
            self._subscribers[ID_FILTER_ALL],
        ]:
            for callback, event_filter in subscription_list:
                if event_filter is not None and event not in event_filter:
                    continue
                try:
                    callback(event, obj_id)
                except Exception as e:
                    logger.error("Error in subscription callback: %s", e)

    def subscribe(
        self,
        callback: CallbackType,
        event_filter: tuple[ItemEvent, ...] | ItemEvent | None = None,
        id_filter: tuple[str, ...] | str | None = None,
    ) -> UnsubscribeType:
        """Subscribe to events with simplified logic."""
        if isinstance(event_filter, ItemEvent):
            event_filter = (event_filter,)

        subscription = (callback, event_filter)

        # Normalize id_filter to tuple
        id_filters: tuple[str, ...]
        if id_filter is None:
            id_filters = (ID_FILTER_ALL,)
        elif isinstance(id_filter, str):
            id_filters = (id_filter,)
        else:
            id_filters = id_filter

        # Add subscription to all specified IDs
        for obj_id in id_filters:
            self._subscribers[obj_id].append(subscription)

        def unsubscribe() -> None:
            """Remove subscription from all IDs."""
            for obj_id in id_filters:
                with contextlib.suppress(ValueError):
                    self._subscribers[obj_id].remove(subscription)

        return unsubscribe


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
