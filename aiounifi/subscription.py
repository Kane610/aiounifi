"""Subscription primitives shared by legacy and Network API v1 handlers."""

from __future__ import annotations

from collections.abc import Callable
import enum

__all__ = [
    "CallbackType",
    "ID_FILTER_ALL",
    "ItemEvent",
    "SubscriptionHandler",
    "SubscriptionType",
    "UnsubscribeType",
]


class ItemEvent(enum.Enum):
    """The event action of the item."""

    ADDED = "added"
    CHANGED = "changed"
    DELETED = "deleted"


CallbackType = Callable[[ItemEvent, str], None]
SubscriptionType = tuple[CallbackType, tuple[ItemEvent, ...] | None]
UnsubscribeType = Callable[[], None]

ID_FILTER_ALL = "*"


class SubscriptionHandler:
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
        id_filter: tuple[str, ...] | str | None = None,
    ) -> UnsubscribeType:
        """Subscribe to item events."""
        if isinstance(event_filter, ItemEvent):
            event_filter = (event_filter,)
        subscription = (callback, event_filter)

        _id_filter: tuple[str, ...]
        if id_filter is None:
            _id_filter = (ID_FILTER_ALL,)
        elif isinstance(id_filter, str):
            _id_filter = (id_filter,)
        else:
            _id_filter = id_filter

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
