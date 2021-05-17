"""Clients are devices on a UniFi network."""

from typing import Optional

from .api import APIItem, APIItems

URL = "/stat/sta"  # Active clients
URL_ALL = "/rest/user"  # All known and configured clients

URL_CLIENT_STATE_MANAGER = "/cmd/stamgr"


class Clients(APIItems):
    """Represents client network devices."""

    KEY = "mac"

    def __init__(self, raw: list, request) -> None:
        """Initialize active clients manager."""
        super().__init__(raw, request, URL, Client)

    async def async_block(self, mac: str) -> None:
        """Block client from controller."""
        data = {"mac": mac, "cmd": "block-sta"}
        await self._request("post", URL_CLIENT_STATE_MANAGER, json=data)

    async def async_unblock(self, mac: str) -> None:
        """Unblock client from controller."""
        data = {"mac": mac, "cmd": "unblock-sta"}
        await self._request("post", URL_CLIENT_STATE_MANAGER, json=data)

    async def async_reconnect(self, mac: str) -> None:
        """Force a wireless client to reconnect to the network."""
        data = {"mac": mac, "cmd": "kick-sta"}
        await self._request("post", URL_CLIENT_STATE_MANAGER, json=data)


class ClientsAll(APIItems):
    """Represents all client network devices."""

    KEY = "mac"

    def __init__(self, raw: list, request) -> None:
        """Initialize all clients manager."""
        super().__init__(raw, request, URL_ALL, Client)


class Client(APIItem):
    """Represents a client network device."""

    @property
    def blocked(self) -> bool:
        """Is client blocked."""
        return self.raw.get("blocked", False)

    @property
    def essid(self) -> str:
        """ESSID client is connected to."""
        return self.raw.get("essid", "")

    @property
    def hostname(self) -> str:
        """Hostname of client."""
        return self.raw.get("hostname", "")

    @property
    def ip(self) -> str:
        """IP of client."""
        return self.raw.get("ip", "")

    @property
    def is_guest(self) -> bool:
        """Is client guest."""
        return self.raw.get("is_guest", False)

    @property
    def is_wired(self) -> bool:
        """Is client wired."""
        return self.raw.get("is_wired", False)

    @property
    def last_seen(self) -> Optional[int]:
        """When was client last seen."""
        return self.raw.get("last_seen")

    @property
    def mac(self) -> str:
        """MAC address of client."""
        return self.raw.get("mac", "")

    @property
    def name(self) -> str:
        """Name of client."""
        return self.raw.get("name", "")

    @property
    def oui(self) -> str:
        """Vendor string for client MAC."""
        return self.raw.get("oui", "")

    @property
    def site_id(self) -> str:
        """Site ID client belongs to."""
        return self.raw.get("site_id", "")

    @property
    def sw_depth(self) -> Optional[int]:
        """How many layers of switches client is in."""
        return self.raw.get("sw_depth")

    @property
    def sw_mac(self) -> str:
        """MAC for switch client is connected to."""
        return self.raw.get("sw_mac", "")

    @property
    def sw_port(self) -> Optional[int]:
        """Switch port client is connected to."""
        return self.raw.get("sw_port")

    @property
    def rx_bytes(self) -> int:
        """Bytes received over wireless connection."""
        return self.raw.get("rx_bytes", 0)

    @property
    def tx_bytes(self) -> int:
        """Bytes transferred over wireless connection."""
        return self.raw.get("tx_bytes", 0)

    @property
    def uptime(self) -> int:
        """Uptime of client."""
        return self.raw.get("uptime", 0)

    @property
    def wired_rx_bytes(self) -> int:
        """Bytes received over wired connection."""
        return self.raw.get("wired-rx_bytes", 0)

    @property
    def wired_tx_bytes(self) -> int:
        """Bytes transferred over wired connection."""
        return self.raw.get("wired-tx_bytes", 0)

    def __repr__(self) -> str:
        """Return the representation."""
        name = self.name or self.hostname
        return f"<Client {name}: {self.mac} {self.raw}>"
