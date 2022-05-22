"""WLANs as part of a UniFi network."""

from collections.abc import Awaitable, Callable
from typing import Final

from .api import APIItems
from ..models.wlan import Wlan

URL: Final = "/rest/wlanconf"  # List WLAN configuration


class Wlans(APIItems):
    """Represents WLAN configurations."""

    KEY = "name"

    def __init__(
        self,
        raw: list[dict],
        request: Callable[..., Awaitable[list[dict]]],
    ) -> None:
        """Initialize WLAN manager."""
        super().__init__(raw, request, URL, Wlan)

    async def enable(self, wlan: Wlan) -> list[dict]:
        """Block client from controller."""
        wlan_url = f"{URL}/{wlan.id}"
        data = {"enabled": True}
        return await self._request("put", wlan_url, json=data)

    async def disable(self, wlan: Wlan) -> list[dict]:
        """Unblock client from controller."""
        wlan_url = f"{URL}/{wlan.id}"
        data = {"enabled": False}
        return await self._request("put", wlan_url, json=data)
