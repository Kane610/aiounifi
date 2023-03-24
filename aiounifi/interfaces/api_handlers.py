"""API management class and base class for the different end points."""

from abc import ABC
from collections.abc import Callable, ItemsView, Iterator, ValuesView
import enum
from typing import TYPE_CHECKING, Any, Generic, Type, final

from ..models.api import ApiItemT, ApiRequest

if TYPE_CHECKING:
    from ..controller import Controller
    from ..models.message import Message, MessageKey


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
        self._subscribers: dict[str, list[SubscriptionType]] = {ID_FILTER_ALL: []}

    def signal_subscribers(self, event: ItemEvent, obj_id: str) -> None:
        """Signal subscribers."""
        subscribers: list[SubscriptionType] = (
            self._subscribers.get(obj_id, []) + self._subscribers[ID_FILTER_ALL]
        )
        for callback, event_filter in subscribers:
            if event_filter is not None and event not in event_filter:
                continue
            callback(event, obj_id)

    def subscribe(
        self,
        callback: CallbackType,
        event_filter: tuple[ItemEvent, ...] | ItemEvent | None = None,
        id_filter: tuple[str] | str | None = None,
    ) -> UnsubscribeType:
        """Subscribe to added events."""
        if isinstance(event_filter, ItemEvent):
            event_filter = (event_filter,)
        subscription = (callback, event_filter)

        _id_filter: tuple[str]
        if id_filter is None:
            _id_filter = (ID_FILTER_ALL,)
        elif isinstance(id_filter, str):
            _id_filter = (id_filter,)

        for obj_id in _id_filter:
            if obj_id not in self._subscribers:
                self._subscribers[obj_id] = []
            self._subscribers[obj_id].append(subscription)

        def unsubscribe() -> None:
            for obj_id in _id_filter:
                if obj_id not in self._subscribers:
                    continue
                if subscription not in self._subscribers[obj_id]:
                    continue
                self._subscribers[obj_id].remove(subscription)

        return unsubscribe


class APIHandler(SubscriptionHandler, Generic[ApiItemT]):
    """Base class for a map of API Items."""

    obj_id_key: str
    path: str
    item_cls: Type[ApiItemT]
    process_messages: tuple["MessageKey", ...] = ()
    remove_messages: tuple["MessageKey", ...] = ()

    def __init__(self, controller: "Controller") -> None:
        """Initialize API handler."""
        super().__init__()
        self.controller = controller
        self._items: dict[str, ApiItemT] = {}

        if message_filter := self.process_messages + self.remove_messages:
            controller.messages.subscribe(self.process_message, message_filter)

    @final
    async def update(self) -> None:
        """Refresh data."""
        raw = await self.controller.request(ApiRequest("get", self.path, None))
        self.process_raw(raw)

    @final
    def process_raw(self, raw: list[dict[str, Any]]) -> None:
        """Process full raw response."""
        for raw_item in raw:
            self.process_item(raw_item)

    @final
    def process_message(self, message: "Message") -> None:
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
