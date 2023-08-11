"""Port forwarding in a UniFi network."""
from dataclasses import dataclass
from typing import TypedDict

from typing_extensions import Self

from .api import ApiItem, ApiRequest


class TypedPortForward(TypedDict):
    """Port forward type definition."""

    _id: str
    dst_port: str
    enabled: bool
    fwd_port: str
    fwd: str
    name: str
    pfwd_interface: str
    proto: str
    site_id: str
    src: str


@dataclass
class PortForwardEnableRequest(ApiRequest):
    """Request object for enabling port forward."""

    @classmethod
    def create(cls, data: TypedPortForward, enable: bool) -> Self:
        """Create enable port forward request."""
        data["enabled"] = enable
        return cls(
            method="post",
            path="/rest/portforward",
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
        return self.raw["enabled"]

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
