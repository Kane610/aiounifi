"""Device port handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ItemsView, Iterator, ValuesView, final

from ..models.port import Port
from .api_handlers import ItemEvent, SubscriptionHandler

if TYPE_CHECKING:
    from ..controller import Controller


class Ports(SubscriptionHandler):
    """Represents network device ports."""

    item_cls = Port

    def __init__(self, controller: Controller) -> None:
        """Initialize API handler."""
        super().__init__()
        self.controller = controller
        self._items: dict[str, Port] = {}
        controller.devices.subscribe(self.process_device)

    def process_device(self, event: ItemEvent, device_id: str) -> None:
        """Add, update, remove."""
        if event in (ItemEvent.ADDED, ItemEvent.CHANGED):
            device = self.controller.devices[device_id]
            if "port_table" not in device.raw:
                return
            for raw_port in device.raw["port_table"]:
                port = Port(raw_port)
                if (port_idx := port.port_idx or port.ifname) is None:
                    continue
                obj_id = f"{device_id}_{port_idx}"
                self._items[obj_id] = port
                self.signal_subscribers(event, obj_id)

        else:
            matched_obj_ids = [
                obj_id for obj_id in self._items if obj_id.startswith(device_id)
            ]
            for obj_id in matched_obj_ids:
                self._items.pop(obj_id)
                self.signal_subscribers(event, obj_id)

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
