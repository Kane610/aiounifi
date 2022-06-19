"""UniFi devices are network infrastructure.

Access points, Gateways, Switches.
"""

from __future__ import annotations

from typing import Final

from ..models.device import Device
from .api import APIItems

URL: Final = "/stat/device"

URL_DEVICE_MANAGER: Final = "/cmd/devmgr"


class Devices(APIItems):
    """Represents network devices."""

    KEY = "mac"
    path = URL
    item_cls = Device

    async def upgrade(self, mac: str) -> list[dict]:
        """Upgrade network device."""
        data = {"mac": mac, "cmd": "upgrade"}
        return await self.controller.request("post", URL_DEVICE_MANAGER, json=data)
