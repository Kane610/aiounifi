"""Clients are devices on a UniFi network."""

from typing import Any

from ..models.client import (
    Client,
    ClientBlockRequest,
    ClientListRequest,
    ClientReconnectRequest,
    ClientRemoveRequest,
)
from ..models.message import MessageKey
from .api_handlers import APIHandler


class Clients(APIHandler[Client]):
    """Represents client network devices."""

    obj_id_key = "mac"
    path = ""
    item_cls = Client
    process_messages = (MessageKey.CLIENT,)
    remove_messages = (MessageKey.CLIENT_REMOVED,)
    api_request = ClientListRequest.create()

    async def block(self, mac: str) -> dict[str, Any]:
        """Block client from controller."""
        return await self.controller.request(ClientBlockRequest.create(mac, block=True))

    async def unblock(self, mac: str) -> dict[str, Any]:
        """Unblock client from controller."""
        return await self.controller.request(
            ClientBlockRequest.create(mac, block=False)
        )

    async def reconnect(self, mac: str) -> dict[str, Any]:
        """Force a wireless client to reconnect to the network."""
        return await self.controller.request(ClientReconnectRequest.create(mac))

    async def remove_clients(self, macs: list[str]) -> dict[str, Any]:
        """Make controller forget provided clients."""
        return await self.controller.request(ClientRemoveRequest.create(macs))
