"""Port forwarding in a UniFi network."""
from dataclasses import dataclass
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequest


class TypedPortForward(TypedDict):
    """Port forward type definition."""

    _id: str
    dst_port: str
    enabled: NotRequired[bool]
    fwd_port: str
    fwd: str
    name: str
    pfwd_interface: str
    proto: str
    site_id: str
    src: str


@dataclass
class PortForwardListRequest(ApiRequest):
    """Request object for port forward list."""

    @classmethod
    def create(cls) -> Self:
        """Create port forward list request."""
        return cls(method="get", path="/rest/portforward")


@dataclass
class PortForwardEnableRequest(ApiRequest):
    """Request object for enabling port forward."""

    @classmethod
    def create(cls, port_forward: "PortForward", enable: bool) -> Self:
        """Create enable port forward request."""
        data = port_forward.raw.copy()
        data["enabled"] = enable
        return cls(
            method="put",
            path=f"/rest/portforward/{data['_id']}",
            data=data,
        )


class PortForward(ApiItem):
    """Represents a port forward configuration."""

    raw: TypedPortForward

    @property
    def id(self) -> str:
        """Unique ID of port forward."""
        return self.raw["_id"]

    @property
    def destination_port(self) -> str:
        """Destination port."""
        return self.raw["dst_port"]

    @property
    def enabled(self) -> bool:
        """Is port forward enabled."""
        return self.raw.get("enabled", False)

    @property
    def forward_port(self) -> str:
        """Forwarded port."""
        return self.raw["fwd_port"]

    @property
    def forward_ip(self) -> str:
        """IP address to forward."""
        return self.raw["fwd"]

    @property
    def name(self) -> str:
        """Name of port forward."""
        return self.raw["name"]

    @property
    def port_forward_interface(self) -> str:
        """Interface to expose port forward."""
        return self.raw["pfwd_interface"]

    @property
    def protocol(self) -> str:
        """Protocol to forward.

        tcp_udp
        """
        return self.raw["proto"]

    @property
    def site_id(self) -> str:
        """Site id port forward belongs to."""
        return self.raw["site_id"]

    @property
    def source(self) -> str:
        """Source."""
        return self.raw["src"]
