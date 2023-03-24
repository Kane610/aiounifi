"""Device port handler."""

from typing import TYPE_CHECKING

from ..models.port import Port
from .api_handlers import APIHandler, ItemEvent

if TYPE_CHECKING:
    from ..controller import Controller


class Ports(APIHandler[Port]):
    """Represents network device ports."""

    item_cls = Port

    def __init__(self, controller: "Controller") -> None:
        """Initialize API handler."""
        super().__init__(controller)
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
            return

        matched_obj_ids = [
            obj_id for obj_id in self._items if obj_id.startswith(device_id)
        ]
        for obj_id in matched_obj_ids:
            self._items.pop(obj_id)
            self.signal_subscribers(event, obj_id)
