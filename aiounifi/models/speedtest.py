"""UniFi speedtest models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from .api import ApiItem, ApiRequest, ApiRequestV2


class TypedSpeedtestStatus(TypedDict, total=False):
    """Speedtest status type definition."""

    # V2 Endpoint keys
    status: str
    status_text: str
    download_mbps: float
    upload_mbps: float
    latency_ms: float
    time: int
    id: str
    interface_name: str
    wan_networkgroup: str

    # Legacy Health Endpoint keys
    xput_down: float
    xput_up: float
    speedtest_ping: float
    speedtest_lastrun: int
    speedtest_status: str


@dataclass
class SpeedtestStatusRequest(ApiRequestV2):
    """Request object for hardware speedtest status."""

    @classmethod
    def create(cls) -> SpeedtestStatusRequest:
        """Create hardware speedtest status request."""
        return cls(method="get", path="/speedtest")


@dataclass
class SpeedtestStatusLegacyRequest(ApiRequest):
    """Request object for software controller speedtest status (health)."""

    @classmethod
    def create(cls) -> SpeedtestStatusLegacyRequest:
        """Create software speedtest status request."""
        return cls(method="get", path="/stat/health")


@dataclass
class SpeedtestTriggerRequest(ApiRequest):
    """Request object for triggering a hardware speedtest."""

    @classmethod
    def create(cls) -> SpeedtestTriggerRequest:
        """Create speedtest trigger request."""
        return cls(method="post", path="/cmd/devmgr/speedtest", data={})


@dataclass
class SpeedtestTriggerLegacyRequest(ApiRequest):
    """Request object for triggering a legacy/software speedtest."""

    @classmethod
    def create(cls) -> SpeedtestTriggerLegacyRequest:
        """Create legacy speedtest trigger request."""
        return cls(method="post", path="/cmd/devmgr", data={"cmd": "speedtest"})


class SpeedtestStatus(ApiItem):
    """Represents a speedtest status."""

    raw: TypedSpeedtestStatus

    @property
    def status(self) -> str:
        """Status of the speedtest."""
        return str(self.raw.get("status_text", self.raw.get("status", self.raw.get("speedtest_status", "unknown"))))

    @property
    def download(self) -> float:
        """Download speed in Mbps."""
        return float(self.raw.get("download_mbps", self.raw.get("xput_down", 0.0)))

    @property
    def upload(self) -> float:
        """Upload speed in Mbps."""
        return float(self.raw.get("upload_mbps", self.raw.get("xput_up", 0.0)))

    @property
    def ping(self) -> float:
        """Ping in ms."""
        return float(self.raw.get("latency_ms", self.raw.get("speedtest_ping", 0.0)))

    @property
    def timestamp(self) -> int:
        """Timestamp of the test."""
        return int(self.raw.get("time", self.raw.get("speedtest_lastrun", 0)))

