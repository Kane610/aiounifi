"""Device outlet handler."""

from typing import TYPE_CHECKING

from ..models.outlet import Outlet
from .api_handlers import APIHandler, ItemEvent

if TYPE_CHECKING:
    from ..controller import Controller


class Outlets(APIHandler[Outlet]):
    """Represents network device ports."""

    item_cls = Outlet

    def __init__(self, controller: "Controller") -> None:
        """Initialize API handler."""
        super().__init__(controller)
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
            return

        matched_obj_ids = [
            obj_id for obj_id in self._items if obj_id.startswith(device_id)
        ]
        for obj_id in matched_obj_ids:
            self._items.pop(obj_id)
            self.signal_subscribers(event, obj_id)
