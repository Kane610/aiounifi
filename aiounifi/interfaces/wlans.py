"""WLANs as part of a UniFi network."""

from typing import Any

from ..models.wlan import Wlan, WlanEnableRequest
from .api_handlers import APIHandler


class Wlans(APIHandler[Wlan]):
    """Represents WLAN configurations."""

    obj_id_key = "name"
    path = "/rest/wlanconf"
    item_cls = Wlan

    async def enable(self, wlan: Wlan) -> list[dict[str, Any]]:
        """Block client from controller."""
        return await self.controller.request(
            WlanEnableRequest.create(wlan.id, enable=True)
        )

    async def disable(self, wlan: Wlan) -> list[dict[str, Any]]:
        """Unblock client from controller."""
        return await self.controller.request(
            WlanEnableRequest.create(wlan.id, enable=False)
        )
