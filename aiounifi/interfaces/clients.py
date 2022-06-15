"""Clients are devices on a UniFi network."""

from __future__ import annotations

from typing import Final

from ..models.client import Client
from ..models.event import EventKey, MessageKey
from .api import APIItems

URL: Final = "/stat/sta"
URL_CLIENT_STATE_MANAGER: Final = "/cmd/stamgr"


class Clients(APIItems):
    """Represents client network devices."""

    obj_id_key = "mac"
    path = URL
    item_cls = Client
    events = (
        EventKey.WIRED_CLIENT_CONNECTED,
        EventKey.WIRED_CLIENT_DISCONNECTED,
        EventKey.WIRED_CLIENT_BLOCKED,
        EventKey.WIRED_CLIENT_UNBLOCKED,
        EventKey.WIRELESS_CLIENT_CONNECTED,
        EventKey.WIRELESS_CLIENT_DISCONNECTED,
        EventKey.WIRELESS_CLIENT_BLOCKED,
        EventKey.WIRELESS_CLIENT_UNBLOCKED,
        EventKey.WIRELESS_CLIENT_ROAM,
        EventKey.WIRELESS_CLIENT_ROAMRADIO,
        EventKey.WIRELESS_GUEST_CONNECTED,
        EventKey.WIRELESS_GUEST_DISCONNECTED,
        EventKey.WIRELESS_GUEST_ROAM,
        EventKey.WIRELESS_GUEST_ROAMRADIO,
    )
    process_messages = (MessageKey.CLIENT,)
    remove_messages = (MessageKey.CLIENT_REMOVED,)

    async def block(self, mac: str) -> list[dict]:
        """Block client from controller."""
        data = {"mac": mac, "cmd": "block-sta"}
        return await self.controller.request(
            "post", URL_CLIENT_STATE_MANAGER, json=data
        )

    async def unblock(self, mac: str) -> list[dict]:
        """Unblock client from controller."""
        data = {"mac": mac, "cmd": "unblock-sta"}
        return await self.controller.request(
            "post", URL_CLIENT_STATE_MANAGER, json=data
        )

    async def reconnect(self, mac: str) -> list[dict]:
        """Force a wireless client to reconnect to the network."""
        data = {"mac": mac, "cmd": "kick-sta"}
        return await self.controller.request(
            "post", URL_CLIENT_STATE_MANAGER, json=data
        )

    async def remove_clients(self, macs: list[str]) -> list[dict]:
        """Make controller forget provided clients."""
        data = {"macs": macs, "cmd": "forget-sta"}
        return await self.controller.request(
            "post", URL_CLIENT_STATE_MANAGER, json=data
        )
