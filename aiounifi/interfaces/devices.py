"""UniFi devices are network infrastructure.

Access points, gateways, power plugs, switches.
"""

from typing import Any

from ..models.device import Device, DeviceListRequest, DeviceUpgradeRequest
from ..models.message import MessageKey
from .api_handlers import APIHandler


class Devices(APIHandler[Device]):
    """Represents network devices."""

    obj_id_key = "mac"
    path = ""
    item_cls = Device
    process_messages = (MessageKey.DEVICE,)
    api_request = DeviceListRequest.create()

    async def upgrade(self, mac: str) -> list[dict[str, Any]]:
        """Upgrade network device."""
        return await self.controller.request(DeviceUpgradeRequest.create(mac))
