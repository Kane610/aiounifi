"""UniFi devices are network infrastructure.

Access points, Gateways, Switches.
"""

import logging
from typing import (
    Awaitable,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
    ValuesView,
)

from .api import APIItem, APIItems
from .events import Event as UniFiEvent

LOGGER = logging.getLogger(__name__)

URL = "/stat/device"


class Devices(APIItems):
    """Represents network devices."""

    KEY = "mac"

    def __init__(
        self,
        raw: List[dict],
        request: Callable[..., Awaitable[List[dict]]],
    ) -> None:
        """Initialize device manager."""
        super().__init__(raw, request, URL, Device)


class Device(APIItem):
    """Represents a network device."""

    def __init__(
        self,
        raw: dict,
        request: Callable[..., Awaitable[List[dict]]],
    ) -> None:
        """Initialize device."""
        super().__init__(raw, request)
        self.ports = Ports(raw.get("port_table", []))

    def update(
        self,
        raw: Optional[dict] = None,
        event: Optional[UniFiEvent] = None,
    ) -> None:
        """Refresh data."""
        if raw:
            self.ports.update(raw.get("port_table", []))
        super().update(raw, event)

    @property
    def board_rev(self) -> int:
        """Board revision of device."""
        return self.raw["board_rev"]

    @property
    def considered_lost_at(self) -> int:
        """When device is considered lost."""
        return self.raw["considered_lost_at"]

    @property
    def disabled(self) -> bool:
        """Is device disabled."""
        return self.raw.get("disabled", False)

    @property
    def id(self) -> str:
        """ID of device."""
        return self.raw["device_id"]

    @property
    def ip(self) -> str:
        """IP of device."""
        return self.raw["ip"]

    @property
    def fan_level(self) -> Optional[int]:
        """Fan level of device."""
        return self.raw.get("fan_level")

    @property
    def has_fan(self) -> bool:
        """Do device have a fan."""
        return self.raw.get("has_fan", False)

    @property
    def last_seen(self) -> Optional[int]:
        """When was device last seen."""
        return self.raw.get("last_seen")

    @property
    def mac(self) -> str:
        """MAC address of device."""
        return self.raw["mac"]

    @property
    def model(self) -> str:
        """Model of device."""
        return self.raw["model"]

    @property
    def name(self) -> str:
        """Name of device."""
        return self.raw.get("name", "")

    @property
    def next_heartbeat_at(self) -> Optional[int]:
        """Next heart beat full UNIX time."""
        return self.raw.get("next_heartbeat_at")

    @property
    def next_interval(self) -> int:
        """Next heart beat in seconds."""
        return self.raw.get("next_interval", 30)

    @property
    def overheating(self) -> bool:
        """Is device overheating."""
        return self.raw.get("overheating", False)

    @property
    def port_overrides(self) -> list:
        """Overridden port configuration."""
        return self.raw.get("port_overrides", [])

    @property
    def port_table(self) -> list:
        """List of ports and data."""
        return self.raw.get("port_table", [])

    @property
    def state(self) -> int:
        """State of device."""
        return self.raw["state"]

    @property
    def sys_stats(self) -> dict:
        """Output from top."""
        return self.raw["sys_stats"]

    @property
    def type(self) -> str:
        """Type of device."""
        return self.raw["type"]

    @property
    def version(self) -> str:
        """Firmware version."""
        return self.raw["version"]

    @property
    def upgradable(self) -> bool:
        """Is a new firmware available."""
        return self.raw.get("upgradable", False)

    @property
    def upgrade_to_firmware(self) -> str:
        """Firmware version to update to."""
        return self.raw.get("upgrade_to_firmware", "")

    @property
    def uplink_depth(self) -> Optional[int]:
        """Hops to gateway."""
        return self.raw.get("uplink_depth")

    @property
    def user_num_sta(self) -> int:
        """Amount of connected clients."""
        return self.raw["user-num_sta"]

    @property
    def wlan_overrides(self) -> list:
        """Wlan configuration override."""
        return self.raw.get("wlan_overrides", [])

    async def async_set_port_poe_mode(self, port_idx: int, mode: str) -> List[dict]:
        """Set port poe mode.

        Auto, 24v, passthrough, off.
        Make sure to not overwrite any existing configs.
        """
        LOGGER.debug("Override port %d with mode %s", port_idx, mode)

        existing_override = False
        for port_override in self.port_overrides:
            if port_idx == port_override["port_idx"]:
                port_override["poe_mode"] = mode
                existing_override = True
                break

        if not existing_override:
            self.port_overrides.append(
                {
                    "port_idx": port_idx,
                    "portconf_id": self.ports[port_idx].portconf_id,
                    "poe_mode": mode,
                }
            )

        url = f"/rest/device/{self.id}"
        data = {"port_overrides": self.port_overrides}

        return await self._request("put", url, json=data)

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Device {self.name}: {self.mac}>"


class Port:
    """Represents a network port."""

    def __init__(self, raw: dict) -> None:
        """Initialize port."""
        self.raw = raw

    @property
    def ifname(self) -> str:
        """Port name used by USG."""
        return self.raw.get("ifname", "")

    @property
    def media(self) -> str:
        """Media port is connected to."""
        return self.raw.get("media", "")

    @property
    def name(self) -> str:
        """Port name."""
        return self.raw["name"]

    @property
    def port_idx(self) -> Optional[int]:
        """Port index."""
        return self.raw.get("port_idx")

    @property
    def poe_class(self) -> str:
        """Port POE class."""
        return self.raw.get("poe_class", "")

    @property
    def poe_enable(self) -> Optional[bool]:
        """Is POE supported/requested by client."""
        return self.raw.get("poe_enable")

    @property
    def poe_mode(self) -> str:
        """Is POE auto, pasv24, passthrough, off or None."""
        return self.raw.get("poe_mode", "")

    @property
    def poe_power(self) -> str:
        """POE power usage."""
        return self.raw.get("poe_power", "")

    @property
    def poe_voltage(self) -> str:
        """POE voltage usage."""
        return self.raw.get("poe_voltage", "")

    @property
    def portconf_id(self) -> str:
        """Port configuration ID."""
        return self.raw.get("portconf_id", "")

    @property
    def port_poe(self) -> bool:
        """Is POE used."""
        return self.raw.get("port_poe") is True

    @property
    def up(self) -> str:
        """Is port up."""
        return self.raw.get("up", "")

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<{self.name}: Poe {self.poe_enable}>"


class Ports:
    """Represents ports on a device."""

    def __init__(self, raw: List[dict]) -> None:
        """Initialize port manager."""
        self.ports: Dict[Union[int, str], Port] = {}
        for raw_port in raw:
            port = Port(raw_port)

            if (index := port.port_idx) is not None:
                self.ports[index] = port
            elif ifname := port.ifname:
                self.ports[ifname] = port

    def update(self, raw: List[dict]) -> None:
        """Update ports."""
        for raw_port in raw:
            index = None

            if "port_idx" in raw_port:
                index = raw_port["port_idx"]

            elif "ifname" in raw_port:
                index = raw_port["ifname"]

            if index in self.ports:
                self.ports[index].raw = raw_port

    def values(self) -> ValuesView[Port]:
        """Return ports."""
        return self.ports.values()

    def __getitem__(self, obj_id: int) -> Port:
        """Get specific port based on key."""
        return self.ports[obj_id]

    def __iter__(self) -> Iterator[Union[int, str]]:
        """Iterate over ports."""
        return iter(self.ports)
