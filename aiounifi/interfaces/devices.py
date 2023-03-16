"""UniFi devices are network infrastructure.

Access points, gateways, power plugs, switches.
"""

from typing import Any, Final

from ..models.device import Device, DeviceUpgradeRequest
from ..models.message import MessageKey
from .api_handlers import APIHandler

URL: Final = "/stat/device"


class Devices(APIHandler[Device]):
    """Represents network devices."""

    obj_id_key = "mac"
    path = URL
    item_cls = Device
    process_messages = (MessageKey.DEVICE,)

    async def upgrade(self, mac: str) -> list[dict[str, Any]]:
        """Upgrade network device."""
        return await self.controller.request(DeviceUpgradeRequest.create(mac))
