"""UniFi devices are network infrastructure.

Access points, Gateways, Switches.
"""

from __future__ import annotations

from collections.abc import Iterator, ValuesView
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

from ..events import Event as UniFiEvent
from .api import APIItem
from .request_object import RequestObject

if TYPE_CHECKING:
    from ..controller import Controller

LOGGER = logging.getLogger(__name__)


@dataclass
class DevicePowerCyclePortRequest(RequestObject):
    """Request object for power cycle PoE port."""

    @classmethod
    def create(cls, mac: str, port_idx: int) -> "DevicePowerCyclePortRequest":
        """Create power cycle of PoE request."""
        return cls(
            method="post",
            path="/cmd/devmgr",
            data={
                "cmd": "power-cycle",
                "mac": mac,
                "port_idx": port_idx,
            },
        )


@dataclass
class DeviceRestartRequest(RequestObject):
    """Request object for device restart."""

    @classmethod
    def create(cls, mac: str, soft=True) -> "DeviceRestartRequest":
        """Create device restart request.

        Hard is specifically for PoE switches and will additionally cycle PoE ports.
        """
        return cls(
            method="post",
            path="/cmd/devmgr",
            data={
                "cmd": "restart",
                "mac": mac,
                "reboot_type": "soft" if soft else "hard",
            },
        )


@dataclass
class DeviceUpgradeRequest(RequestObject):
    """Request object for device upgrade."""

    @classmethod
    def create(cls, mac: str) -> "DeviceUpgradeRequest":
        """Create device upgrade request."""
        return cls(
            method="post",
            path="/cmd/devmgr",
            data={
                "cmd": "upgrade",
                "mac": mac,
            },
        )


@dataclass
class DeviceSetOutletRelayRequest(RequestObject):
    """Request object for outlet relay state."""

    @classmethod
    def create(
        cls, device: Device, outlet_idx: int, state: bool
    ) -> "DeviceSetOutletRelayRequest":
        """Create device outlet relay state request.

        True:  outlet power output on.
        False: outlet power output off.
        """
        existing_override = False
        for outlet_override in device.outlet_overrides:
            if outlet_idx == outlet_override["index"]:
                outlet_override["relay_state"] = state
                existing_override = True
                break

        if not existing_override:
            device.outlet_overrides.append(
                {
                    "index": outlet_idx,
                    "name": device.outlets[outlet_idx].name,
                    "relay_state": state,
                }
            )

        return cls(
            method="put",
            path=f"/rest/device/{device.id}",
            data={"outlet_overrides": device.outlet_overrides},
        )


@dataclass
class DeviceSetOutletCycleEnabledRequest(RequestObject):
    """Request object for outlet cycle_enabled flag."""

    @classmethod
    def create(
        cls, device: Device, outlet_idx: int, state: bool
    ) -> "DeviceSetOutletCycleEnabledRequest":
        """Create device outlet outlet cycle_enabled flag request.

        True:  UniFi Network will power cycle this outlet if the internet goes down.
        False: UniFi Network will not power cycle this outlet if the internet goes down.
        """
        existing_override = False
        for outlet_override in device.outlet_overrides:
            if outlet_idx == outlet_override["index"]:
                outlet_override["cycle_enabled"] = state
                existing_override = True
                break

        if not existing_override:
            device.outlet_overrides.append(
                {
                    "index": outlet_idx,
                    "name": device.outlets[outlet_idx].name,
                    "cycle_enabled": state,
                }
            )

        return cls(
            method="put",
            path=f"/rest/device/{device.id}",
            data={"outlet_overrides": device.outlet_overrides},
        )


@dataclass
class DeviceSetPoePortModeRequest(RequestObject):
    """Request object for setting port POE mode."""

    @classmethod
    def create(
        cls, device: Device, port_idx: int, mode: str
    ) -> "DeviceSetPoePortModeRequest":
        """Create device set port poe mode request.

        Auto, 24v, passthrough, off.
        Make sure to not overwrite any existing configs.
        """
        existing_override = False
        for port_override in device.port_overrides:
            if port_idx == port_override["port_idx"]:
                port_override["poe_mode"] = mode
                existing_override = True
                break

        if not existing_override:
            device.port_overrides.append(
                {
                    "port_idx": port_idx,
                    "portconf_id": device.ports[port_idx].portconf_id,
                    "poe_mode": mode,
                }
            )

        return cls(
            method="put",
            path=f"/rest/device/{device.id}",
            data={"port_overrides": device.port_overrides},
        )


class Device(APIItem):
    """Represents a network device."""

    def __init__(
        self,
        raw: dict,
        controller: Controller,
    ) -> None:
        """Initialize device."""
        super().__init__(raw, controller)
        self.ports = Ports(raw.get("port_table", []))
        self.outlets = Outlets(raw.get("outlet_table", []))

    def update(
        self,
        raw: dict | None = None,
        event: UniFiEvent | None = None,
    ) -> None:
        """Refresh data."""
        if raw:
            self.ports.update(raw.get("port_table", []))
            self.outlets.update(raw.get("outlet_table", []))
        super().update(raw, event)

    @property
    def board_revision(self) -> int:
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
    def downlink_table(self) -> list[dict]:
        """All devices with device as uplink."""
        return self.raw.get("downlink_table", [])

    @property
    def id(self) -> str:
        """ID of device."""
        return self.raw["device_id"]

    @property
    def ip(self) -> str:
        """IP of device."""
        return self.raw["ip"]

    @property
    def fan_level(self) -> int | None:
        """Fan level of device."""
        return self.raw.get("fan_level")

    @property
    def has_fan(self) -> bool:
        """Do device have a fan."""
        return self.raw.get("has_fan", False)

    @property
    def last_seen(self) -> int | None:
        """When was device last seen."""
        return self.raw.get("last_seen")

    @property
    def lldp_table(self) -> list[dict]:
        """All clients and devices directly attached to device."""
        return self.raw.get("lldp_table", [])

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
    def next_heartbeat_at(self) -> int | None:
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
    def outlet_overrides(self) -> list:
        """Overridden outlet configuration."""
        return self.raw.get("outlet_overrides", [])

    @property
    def outlet_table(self) -> list:
        """List of outlets."""
        return self.raw.get("outlet_table", [])

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
    def uplink(self) -> dict[str, bool | int | list[str] | str]:
        """Information about uplink."""
        return self.raw["uplink"]

    @property
    def uplink_depth(self) -> int | None:
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

    async def set_outlet_relay_state(self, outlet_idx: int, state: bool) -> list[dict]:
        """Set outlet relay state."""
        LOGGER.debug("Override outlet %d with relay_state %s", outlet_idx, str(state))
        return await self._controller.request(
            DeviceSetOutletRelayRequest.create(self, outlet_idx, state)
        )

    async def set_outlet_cycle_enabled(
        self, outlet_idx: int, state: bool
    ) -> list[dict]:
        """Set outlet cycle_enabled flag."""
        LOGGER.debug("Override outlet %d with cycle_enabled %s", outlet_idx, str(state))
        return await self._controller.request(
            DeviceSetOutletCycleEnabledRequest.create(self, outlet_idx, state)
        )

    async def set_port_poe_mode(self, port_idx: int, mode: str) -> list[dict]:
        """Set port poe mode."""
        LOGGER.debug("Override port %d with mode %s", port_idx, mode)
        return await self._controller.request(
            DeviceSetPoePortModeRequest.create(self, port_idx, mode)
        )

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
    def port_idx(self) -> int | None:
        """Port index."""
        return self.raw.get("port_idx")

    @property
    def poe_class(self) -> str:
        """Port POE class."""
        return self.raw.get("poe_class", "")

    @property
    def poe_enable(self) -> bool | None:
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

    def __init__(self, raw: list[dict]) -> None:
        """Initialize port manager."""
        self.ports: dict[int | str, Port] = {}
        for raw_port in raw:
            port = Port(raw_port)

            if (index := port.port_idx) is not None:
                self.ports[index] = port
            elif ifname := port.ifname:
                self.ports[ifname] = port

    def update(self, raw: list[dict]) -> None:
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

    def __iter__(self) -> Iterator[int | str]:
        """Iterate over ports."""
        return iter(self.ports)


class Outlet:
    """Represents an outlet."""

    def __init__(self, raw: dict) -> None:
        """Initialize outlet."""
        self.raw = raw

    @property
    def name(self) -> str:
        """Name of outlet."""
        return self.raw["name"]

    @property
    def index(self) -> int:
        """Outlet index."""
        return self.raw["index"]

    @property
    def has_relay(self) -> bool | None:
        """Is the outlet controllable."""
        if "has_relay" in self.raw:
            return self.raw["has_relay"]
        return None

    @property
    def relay_state(self) -> bool:
        """Is outlet power on."""
        return self.raw["relay_state"]

    @property
    def cycle_enabled(self) -> bool | None:
        """Modem Power Cycle."""
        if "cycle_enabled" in self.raw:
            return self.raw["cycle_enabled"]
        return None

    # Metering capabilities of outlet

    @property
    def has_metering(self) -> bool | None:
        """Is metering supported.

        Reported false by UP1 and UP6 which does not have power metering.
        Not reported by UPD Pro which does report power metering.
        """
        if "has_metering" in self.raw:
            return self.raw["has_metering"]
        return None

    @property
    def caps(self) -> int:
        """Unknown."""
        return self.raw["outlet_caps"]

    @property
    def voltage(self) -> str | None:
        """Voltage draw of outlet."""
        if "outlet_voltage" in self.raw:
            return self.raw["outlet_voltage"]
        return None

    @property
    def current(self) -> str | None:
        """Usage of outlet."""
        if "outlet_current" in self.raw:
            return self.raw["outlet_current"]
        return None

    @property
    def power(self) -> str | None:
        """Power consumption of the outlet."""
        if "outlet_power" in self.raw:
            return self.raw["outlet_power"]
        return None

    @property
    def power_factor(self) -> str | None:
        """Power factor."""
        if "outlet_power_factor" in self.raw:
            return self.raw["outlet_power_factor"]
        return None


class Outlets:
    """Represents outlets on a device."""

    def __init__(self, raw: list[dict]) -> None:
        """Initialize outlet manager."""
        self.outlets: dict[int, Outlet] = {}
        for raw_outlet in raw:
            outlet = Outlet(raw_outlet)
            self.outlets[outlet.index] = outlet

    def update(self, raw: list[dict]) -> None:
        """Update outlets."""
        for raw_outlet in raw:
            index = raw_outlet["index"]
            self.outlets[index].raw = raw_outlet

    def values(self) -> ValuesView[Outlet]:
        """Return outlets."""
        return self.outlets.values()

    def __getitem__(self, obj_id: int) -> Outlet:
        """Get specific outlet based on key."""
        return self.outlets[obj_id]

    def __iter__(self) -> Iterator[int]:
        """Iterate over outlets."""
        return iter(self.outlets)
