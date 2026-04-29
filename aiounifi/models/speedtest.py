"""UniFi speedtest models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict

from .api import ApiItem, ApiRequest, ApiRequestV2, TypedApiResponse


class TypedSpeedtestStatus(TypedDict):
    """Speedtest status type definition."""

    download_mbps: float
    upload_mbps: float
    latency_ms: float
    time: int
    id: NotRequired[str]
    interface_name: NotRequired[str]
    wan_networkgroup: NotRequired[str]


@dataclass
class SpeedtestStatusRequest(ApiRequestV2):
    """Request object for hardware speedtest status."""

    @classmethod
    def create(cls) -> SpeedtestStatusRequest:
        """Create hardware speedtest status request."""
        return cls(method="get", path="/speedtest")

    def decode(self, raw: bytes) -> TypedApiResponse:
        """Decode response and extract nested data if present."""
        data = super().decode(raw)

        if data.get("data"):
            latest_by_interface: dict[str, dict[str, Any]] = {}
            for result in data["data"]:
                interface = result.get("interface_name", "default")
                result["interface_name"] = interface

                if interface not in latest_by_interface or result.get(
                    "time", 0
                ) >= latest_by_interface[interface].get("time", 0):
                    latest_by_interface[interface] = result

            data["data"] = list(latest_by_interface.values())

        return data


@dataclass
class SpeedtestTriggerRequest(ApiRequest):
    """Request object for triggering a hardware speedtest."""

    @classmethod
    def create(cls) -> SpeedtestTriggerRequest:
        """Create speedtest trigger request."""
        return cls(method="post", path="/cmd/devmgr/speedtest", data={})


class SpeedtestStatus(ApiItem):
    """Represents a speedtest status."""

    raw: TypedSpeedtestStatus

    @property
    def download(self) -> float:
        """Download speed in Mbps."""
        return float(self.raw.get("download_mbps", 0.0))

    @property
    def upload(self) -> float:
        """Upload speed in Mbps."""
        return float(self.raw.get("upload_mbps", 0.0))

    @property
    def ping(self) -> float:
        """Ping in ms."""
        return float(self.raw.get("latency_ms", 0.0))

    @property
    def timestamp(self) -> int:
        """Timestamp of the test."""
        return int(self.raw.get("time", 0))
