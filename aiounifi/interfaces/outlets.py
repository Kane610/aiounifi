"""Device outlet handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ItemsView, Iterator, ValuesView, final

from ..models.outlet import Outlet
from .api_handlers import ItemEvent, SubscriptionHandler

if TYPE_CHECKING:
    from ..controller import Controller


class Outlets(SubscriptionHandler):
    """Represents network device ports."""

    item_cls = Outlet

    def __init__(self, controller: Controller) -> None:
        """Initialize API handler."""
        super().__init__()
        self.controller = controller
        self._items: dict[str, Outlet] = {}
        controller.devices.subscribe(self.process_device)

    def process_device(self, event: ItemEvent, device_id: str) -> None:
        """Add, update, remove."""
        if event in (ItemEvent.ADDED, ItemEvent.CHANGED):
            device = self.controller.devices[device_id]
            for raw_outlet in device.outlet_table:
                outlet = Outlet(raw_outlet)
                obj_id = f"{device_id}_{outlet.index}"
                self._items[obj_id] = outlet
                self.signal_subscribers(event, obj_id)

        else:
            matched_obj_ids = [
                obj_id for obj_id in self._items if obj_id.startswith(device_id)
            ]
            for obj_id in matched_obj_ids:
                self._items.pop(obj_id)
                self.signal_subscribers(event, obj_id)

    @final
    def items(self) -> ItemsView[str, Outlet]:
        """Return items dictionary."""
        return self._items.items()

    @final
    def values(self) -> ValuesView[Outlet]:
        """Return items."""
        return self._items.values()

    @final
    def get(self, obj_id: str, default: Any | None = None) -> Outlet | None:
        """Get item value based on key, return default if no match."""
        return self._items.get(obj_id, default)

    @final
    def __contains__(self, obj_id: str) -> bool:
        """Validate membership of item ID."""
        return obj_id in self._items

    @final
    def __getitem__(self, obj_id: str) -> Outlet:
        """Get item value based on key."""
        return self._items[obj_id]

    @final
    def __iter__(self) -> Iterator[str]:
        """Allow iterate over items."""
        return iter(self._items)
