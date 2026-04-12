"""UniFi speedtest models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from .api import ApiItem, ApiRequest, ApiRequestV2, TypedApiResponse


class TypedSpeedtestStatus(TypedDict, total=False):
    """Speedtest status type definition."""

    status: str
    status_text: str
    download_mbps: float
    upload_mbps: float
    latency_ms: float
    time: int
    id: str
    interface_name: str
    wan_networkgroup: str


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

        if "data" in data and data["data"] and "data" in data["data"][0]:
            data["data"] = data["data"][0]["data"]

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
    def status(self) -> str:
        """Status of the speedtest."""
        val = self.raw.get("status_text", self.raw.get("status"))
        if val is not None:
            return str(val)
        # V2 endpoints don't seem to return a status explicitly for completed historical runs
        if "download_mbps" in self.raw:
            return "Completed"
        return "unknown"

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
