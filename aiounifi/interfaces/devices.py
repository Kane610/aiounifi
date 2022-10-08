"""UniFi devices are network infrastructure.

Access points, gateways, power plugs, switches.
"""

from __future__ import annotations

from typing import Any, Final

from ..models.device import Device, DeviceUpgradeRequest
from ..models.event import EventKey
from ..models.message import MessageKey
from .api_handlers import APIHandler

URL: Final = "/stat/device"


class Devices(APIHandler[Device]):
    """Represents network devices."""

    obj_id_key = "mac"
    path = URL
    item_cls = Device
    events = (
        EventKey.ACCESS_POINT_ADOPTED,
        EventKey.ACCESS_POINT_CONFIGURED,
        EventKey.ACCESS_POINT_CONNECTED,
        EventKey.ACCESS_POINT_DELETED,
        EventKey.ACCESS_POINT_LOST_CONTACT,
        EventKey.ACCESS_POINT_RESTARTED,
        EventKey.ACCESS_POINT_RESTARTED_UNKNOWN,
        EventKey.ACCESS_POINT_UPGRADED,
        EventKey.GATEWAY_ADOPTED,
        EventKey.GATEWAY_CONFIGURED,
        EventKey.GATEWAY_CONNECTED,
        EventKey.GATEWAY_DELETED,
        EventKey.GATEWAY_LOST_CONTACT,
        EventKey.GATEWAY_RESTARTED,
        EventKey.GATEWAY_RESTARTED_UNKNOWN,
        EventKey.GATEWAY_UPGRADED,
        EventKey.SWITCH_ADOPTED,
        EventKey.SWITCH_CONFIGURED,
        EventKey.SWITCH_CONNECTED,
        EventKey.SWITCH_DELETED,
        EventKey.SWITCH_LOST_CONTACT,
        EventKey.SWITCH_OVERHEAT,
        EventKey.SWITCH_POE_OVERLOAD,
        EventKey.SWITCH_POE_DISCONNECT,
        EventKey.SWITCH_RESTARTED,
        EventKey.SWITCH_RESTARTED_UNKNOWN,
        EventKey.SWITCH_UPGRADED,
    )
    process_messages = (MessageKey.DEVICE,)

    async def upgrade(self, mac: str) -> list[dict[str, Any]]:
        """Upgrade network device."""
        return await self.controller.request(DeviceUpgradeRequest.create(mac))
