"""Clients are devices on a UniFi network."""

from __future__ import annotations

from typing import Any, Final

from ..models.client import (
    Client,
    ClientBlockRequest,
    ClientReconnectRequest,
    ClientRemoveRequest,
)
from ..models.event import EventKey
from ..models.message import MessageKey
from .api_handlers import APIHandler

URL: Final = "/stat/sta"


class Clients(APIHandler[Client]):
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

    async def block(self, mac: str) -> list[dict[str, Any]]:
        """Block client from controller."""
        return await self.controller.request(ClientBlockRequest.create(mac, block=True))

    async def unblock(self, mac: str) -> list[dict[str, Any]]:
        """Unblock client from controller."""
        return await self.controller.request(
            ClientBlockRequest.create(mac, block=False)
        )

    async def reconnect(self, mac: str) -> list[dict[str, Any]]:
        """Force a wireless client to reconnect to the network."""
        return await self.controller.request(ClientReconnectRequest.create(mac))

    async def remove_clients(self, macs: list[str]) -> list[dict[str, Any]]:
        """Make controller forget provided clients."""
        return await self.controller.request(ClientRemoveRequest.create(macs))
