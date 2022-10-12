""""""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ItemsView, Iterator, ValuesView, final

from .api_handlers import (
    CallbackType,
    ID_FILTER_ALL,
    ItemEvent,
    SubscriptionType,
    UnsubscribeType,
)
from ..models.port import Port

if TYPE_CHECKING:
    from ..controller import Controller


class Ports:
    """Represents network device ports."""

    item_cls = Port

    def __init__(self, controller: Controller) -> None:
        """Initialize API handler."""
        controller.devices.subscribe(self.process_device)

        self.controller = controller
        self._items: dict[str, Port] = {}
        # self._items: dict[str, dict[int | str, Port]] = {}
        self._subscribers: dict[str, list[SubscriptionType]] = {ID_FILTER_ALL: []}

    def process_device(self, event: ItemEvent, device_id: str) -> None:
        """Add, update, remove."""
        self._items.setdefault(device_id, {})
        if event in (event.ADDED, event.CHANGED):
            for raw_port in self.controller.devices[device_id].raw["port_table"]:
                port = Port(raw_port)
                if (port_idx := port.port_idx or port.ifname) is None:
                    continue
                self._items[f"{device_id}_{port_idx}"] = port
                # self._items[device_id][port_idx] = port

        else:
            for port_id in self._items:
                if not port_id.startswith(device_id):
                    continue
                port = self._items.pop(port_id)
            # device_ports = self._items.pop(device_id)

    @final
    def items(self) -> ItemsView[str, Port]:
        """Return items dictionary."""
        return self._items.items()

    @final
    def values(self) -> ValuesView[Port]:
        """Return items."""
        return self._items.values()

    @final
    def get(self, obj_id: str, default: Any | None = None) -> Port | None:
        """Get item value based on key, return default if no match."""
        return self._items.get(obj_id, default)

    @final
    def __contains__(self, obj_id: str) -> bool:
        """Validate membership of item ID."""
        return obj_id in self._items

    @final
    def __getitem__(self, obj_id: str) -> Port:
        """Get item value based on key."""
        return self._items[obj_id]

    @final
    def __iter__(self) -> Iterator[str]:
        """Allow iterate over items."""
        return iter(self._items)

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
        """Subscribe to added events.

        "callback" - callback function to call when an event emits.
        Return function to unsubscribe.
        """
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
