"""Clients are devices on a UniFi network."""

from typing import Awaitable, Callable, List, Optional

from .api import APIItem, APIItems

URL = "/stat/sta"  # Active clients
URL_ALL = "/rest/user"  # All known and configured clients

URL_CLIENT_STATE_MANAGER = "/cmd/stamgr"


class Clients(APIItems):
    """Represents client network devices."""

    KEY = "mac"

    def __init__(
        self,
        raw: List[dict],
        request: Callable[..., Awaitable[List[dict]]],
    ) -> None:
        """Initialize active clients manager."""
        super().__init__(raw, request, URL, Client)

    async def async_block(self, mac: str) -> List[dict]:
        """Block client from controller."""
        data = {"mac": mac, "cmd": "block-sta"}
        return await self._request("post", URL_CLIENT_STATE_MANAGER, json=data)

    async def async_unblock(self, mac: str) -> List[dict]:
        """Unblock client from controller."""
        data = {"mac": mac, "cmd": "unblock-sta"}
        return await self._request("post", URL_CLIENT_STATE_MANAGER, json=data)

    async def async_reconnect(self, mac: str) -> List[dict]:
        """Force a wireless client to reconnect to the network."""
        data = {"mac": mac, "cmd": "kick-sta"}
        return await self._request("post", URL_CLIENT_STATE_MANAGER, json=data)

    async def remove_clients(self, macs: List[str]) -> List[dict]:
        """Make controller forget provided clients."""
        data = {"macs": macs, "cmd": "forget-sta"}
        return await self._request("post", URL_CLIENT_STATE_MANAGER, json=data)


class ClientsAll(APIItems):
    """Represents all client network devices."""

    KEY = "mac"

    def __init__(
        self,
        raw: List[dict],
        request: Callable[..., Awaitable[List[dict]]],
    ) -> None:
        """Initialize all clients manager."""
        super().__init__(raw, request, URL_ALL, Client)


class Client(APIItem):
    """Represents a client network device."""

    @property
    def access_point_mac(self) -> str:
        """MAC address of access point."""
        return self.raw.get("ap_mac", "")

    @property
    def association_time(self) -> Optional[int]:
        """When was client associated with controller."""
        return self.raw.get("assoc_time")

    @property
    def blocked(self) -> bool:
        """Is client blocked."""
        return self.raw.get("blocked", False)

    @property
    def device_name(self) -> str:
        """Device name of client."""
        return self.raw.get("device_name", "")

    @property
    def essid(self) -> str:
        """ESSID client is connected to."""
        return self.raw.get("essid", "")

    @property
    def first_seen(self) -> Optional[int]:
        """When was client first seen."""
        return self.raw.get("first_seen")

    @property
    def fixed_ip(self) -> str:
        """List IP if fixed IP is configured."""
        return self.raw.get("fixed_ip", "")

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
    def latest_association_time(self) -> Optional[int]:
        """When was client last associated with controller."""
        return self.raw.get("latest_assoc_time")

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
    def rx_bytes_r(self) -> int:
        """Bytes recently received over wireless connection."""
        return self.raw.get("rx_bytes-r", 0)

    @property
    def tx_bytes(self) -> int:
        """Bytes transferred over wireless connection."""
        return self.raw.get("tx_bytes", 0)

    @property
    def tx_bytes_r(self) -> int:
        """Bytes recently transferred over wireless connection."""
        return self.raw.get("tx_bytes-r", 0)

    @property
    def uptime(self) -> int:
        """Uptime of client."""
        return self.raw.get("uptime", 0)

    @property
    def wired_rx_bytes(self) -> int:
        """Bytes received over wired connection."""
        return self.raw.get("wired-rx_bytes", 0)

    @property
    def wired_rx_bytes_r(self) -> int:
        """Bytes recently received over wired connection."""
        return self.raw.get("wired-rx_bytes-r", 0)

    @property
    def wired_tx_bytes(self) -> int:
        """Bytes transferred over wired connection."""
        return self.raw.get("wired-tx_bytes", 0)

    @property
    def wired_tx_bytes_r(self) -> int:
        """Bytes recently transferred over wired connection."""
        return self.raw.get("wired-tx_bytes-r", 0)

    def __repr__(self) -> str:
        """Return the representation."""
        name = self.name or self.hostname
        return f"<Client {name}: {self.mac} {self.raw}>"
