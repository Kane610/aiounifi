"""Clients are devices on a UniFi network."""

from __future__ import annotations

from typing import Final

from ..models.client import Client
from .api import APIItems

URL: Final = "/stat/sta"  # Active clients

URL_CLIENT_STATE_MANAGER: Final = "/cmd/stamgr"


class Clients(APIItems):
    """Represents client network devices."""

    KEY = "mac"
    path = URL
    item_cls = Client

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
