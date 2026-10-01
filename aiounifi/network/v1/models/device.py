"""UniFi devices: gateways, switches and access points."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict

from ....models.api import ApiItem
from .api import DEFAULT_PAGE_LIMIT, DEFAULT_PAGE_OFFSET, ApiRequest, page_params


class PortPoe(TypedDict):
    """PoE state of a port."""

    standard: str
    type: int
    enabled: bool
    state: str


class DevicePort(TypedDict):
    """One port of a switch or gateway, from the detail endpoint."""

    idx: int
    state: str
    connector: str
    maxSpeedMbps: int
    speedMbps: NotRequired[int]
    poe: NotRequired[PortPoe]


class DeviceRadio(TypedDict):
    """One radio of an access point, from the detail endpoint."""

    wlanStandard: str
    frequencyGHz: float
    channelWidthMHz: int
    channel: NotRequired[int]


class DeviceInterfaces(TypedDict):
    """Interfaces block of the detail endpoint."""

    ports: NotRequired[list[DevicePort]]
    radios: NotRequired[list[DeviceRadio]]


class DeviceUplink(TypedDict):
    """Uplink block of the detail endpoint."""

    deviceId: str


class DeviceData(TypedDict):
    """One device.

    The list endpoint returns `features` and `interfaces` as lists of names.
    The detail endpoint returns them as objects, and adds `adoptedAt`,
    `provisionedAt`, `configurationId` and `uplink`.
    """

    id: str
    macAddress: str
    name: str
    model: str
    state: str
    supported: bool
    ipAddress: NotRequired[str]
    firmwareVersion: NotRequired[str]
    firmwareUpdatable: NotRequired[bool]
    features: NotRequired[list[str] | dict[str, Any]]
    interfaces: NotRequired[list[str] | DeviceInterfaces]
    adoptedAt: NotRequired[str]
    provisionedAt: NotRequired[str]
    configurationId: NotRequired[str]
    uplink: NotRequired[DeviceUplink]


class UplinkRates(TypedDict):
    """Uplink throughput."""

    txRateBps: int
    rxRateBps: int


class RadioStatistics(TypedDict):
    """Per-radio statistics."""

    frequencyGHz: float
    txRetriesPct: float


class StatisticsInterfaces(TypedDict):
    """Interfaces block of the statistics endpoint."""

    radios: NotRequired[list[RadioStatistics]]


class DeviceStatisticsData(TypedDict):
    """Payload of GET .../devices/{id}/statistics/latest."""

    uptimeSec: int
    lastHeartbeatAt: str
    nextHeartbeatAt: str
    loadAverage1Min: NotRequired[float]
    loadAverage5Min: NotRequired[float]
    loadAverage15Min: NotRequired[float]
    cpuUtilizationPct: NotRequired[float]
    memoryUtilizationPct: NotRequired[float]
    uplink: NotRequired[UplinkRates]
    interfaces: NotRequired[StatisticsInterfaces]


@dataclass
class ListDevicesRequest(ApiRequest):
    """List the devices adopted on a site."""

    @classmethod
    def create(
        cls,
        site_id: str,
        offset: int = DEFAULT_PAGE_OFFSET,
        limit: int = DEFAULT_PAGE_LIMIT,
        filter_value: str | None = None,
    ) -> ListDevicesRequest:
        """Create a request for one page of devices."""
        return cls(
            method="get",
            path=f"/v1/sites/{site_id}/devices",
            params=page_params(offset, limit, filter_value),
        )


@dataclass
class GetDeviceRequest(ApiRequest):
    """Get one device with its ports and radios."""

    @classmethod
    def create(cls, site_id: str, device_id: str) -> GetDeviceRequest:
        """Create the request."""
        return cls(method="get", path=f"/v1/sites/{site_id}/devices/{device_id}")


@dataclass
class GetDeviceStatisticsRequest(ApiRequest):
    """Get the latest statistics of one device."""

    @classmethod
    def create(cls, site_id: str, device_id: str) -> GetDeviceStatisticsRequest:
        """Create the request."""
        return cls(
            method="get",
            path=f"/v1/sites/{site_id}/devices/{device_id}/statistics/latest",
        )


@dataclass
class DeviceActionRequest(ApiRequest):
    """Run an action on a device. The console accepts only `RESTART`."""

    @classmethod
    def create_restart(cls, site_id: str, device_id: str) -> DeviceActionRequest:
        """Restart a device."""
        return cls(
            method="post",
            path=f"/v1/sites/{site_id}/devices/{device_id}/actions",
            data={"action": "RESTART"},
        )


@dataclass
class PortActionRequest(ApiRequest):
    """Run an action on a port. The console accepts only `POWER_CYCLE`."""

    @classmethod
    def create_power_cycle(
        cls, site_id: str, device_id: str, port_idx: int
    ) -> PortActionRequest:
        """Power cycle the PoE output of a port."""
        return cls(
            method="post",
            path=f"/v1/sites/{site_id}/devices/{device_id}/interfaces/ports/{port_idx}/actions",
            data={"action": "POWER_CYCLE"},
        )


class Device(ApiItem):
    """A UniFi device."""

    raw: DeviceData

    @property
    def device_id(self) -> str:
        """UUID used in device-scoped paths."""
        return self.raw["id"]

    @property
    def mac_address(self) -> str:
        """MAC address."""
        return self.raw["macAddress"]

    @property
    def name(self) -> str:
        """Display name."""
        return self.raw["name"]

    @property
    def model(self) -> str:
        """Model name, for example `U6 Pro`."""
        return self.raw["model"]

    @property
    def state(self) -> str:
        """`ONLINE`, `OFFLINE`, `PENDING_ADOPTION`, `UPDATING`, ..."""
        return self.raw["state"]

    @property
    def supported(self) -> bool:
        """Whether the API supports this device."""
        return self.raw["supported"]

    @property
    def ip_address(self) -> str | None:
        """IP address."""
        return self.raw.get("ipAddress")

    @property
    def firmware_version(self) -> str | None:
        """Installed firmware version."""
        return self.raw.get("firmwareVersion")

    @property
    def firmware_updatable(self) -> bool:
        """Whether a firmware update is available."""
        return self.raw.get("firmwareUpdatable", False)

    @property
    def features(self) -> list[str]:
        """Feature names: `switching`, `accessPoint` and `gateway`."""
        features = self.raw.get("features", [])
        return list(features) if isinstance(features, dict) else features

    @property
    def ports(self) -> list[DevicePort]:
        """Ports, known only after `get_details`."""
        interfaces = self.raw.get("interfaces")
        if isinstance(interfaces, dict):
            return interfaces.get("ports", [])
        return []

    @property
    def radios(self) -> list[DeviceRadio]:
        """Radios, known only after `get_details`."""
        interfaces = self.raw.get("interfaces")
        if isinstance(interfaces, dict):
            return interfaces.get("radios", [])
        return []

    @property
    def uplink_device_id(self) -> str | None:
        """UUID of the upstream device, known only after `get_details`."""
        uplink = self.raw.get("uplink")
        return uplink["deviceId"] if uplink else None

    @property
    def adopted_at(self) -> str | None:
        """When the device was adopted, ISO 8601."""
        return self.raw.get("adoptedAt")


class DeviceStatistics(ApiItem):
    """Latest statistics of a device."""

    raw: DeviceStatisticsData

    @property
    def uptime_sec(self) -> int:
        """Seconds since boot."""
        return self.raw["uptimeSec"]

    @property
    def last_heartbeat_at(self) -> str:
        """Last time the device reported in, ISO 8601."""
        return self.raw["lastHeartbeatAt"]

    @property
    def cpu_utilization_pct(self) -> float | None:
        """CPU load, percent."""
        return self.raw.get("cpuUtilizationPct")

    @property
    def memory_utilization_pct(self) -> float | None:
        """Memory use, percent."""
        return self.raw.get("memoryUtilizationPct")

    @property
    def load_average_1min(self) -> float | None:
        """One-minute load average."""
        return self.raw.get("loadAverage1Min")

    @property
    def uplink_tx_rate_bps(self) -> int | None:
        """Uplink transmit rate, bits per second."""
        uplink = self.raw.get("uplink")
        return uplink["txRateBps"] if uplink else None

    @property
    def uplink_rx_rate_bps(self) -> int | None:
        """Uplink receive rate, bits per second."""
        uplink = self.raw.get("uplink")
        return uplink["rxRateBps"] if uplink else None

    @property
    def radios(self) -> list[RadioStatistics]:
        """Per-radio statistics, empty for devices without radios."""
        interfaces = self.raw.get("interfaces")
        return interfaces.get("radios", []) if interfaces else []
