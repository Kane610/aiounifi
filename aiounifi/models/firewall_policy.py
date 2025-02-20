"""Firewall policies as part of a UniFi network."""

from dataclasses import dataclass
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequestV2


class FirewallPolicySchedule(TypedDict):
    """Schedule settings for firewall policy."""

    mode: str
    repeat_on_days: list[str]
    time_all_day: bool


class FirewallPolicyEndpoint(TypedDict):
    """Source or destination endpoint configuration."""

    match_opposite_ports: bool
    matching_target: str
    port_matching_type: str
    zone_id: str
    client_macs: NotRequired[list[str]]


class TypedFirewallPolicy(TypedDict):
    """Firewall policy type definition."""

    _id: str
    action: str
    name: str
    enabled: bool
    connection_state_type: str
    connection_states: list[str]
    create_allow_respond: bool
    description: NotRequired[str]
    destination: FirewallPolicyEndpoint
    source: FirewallPolicyEndpoint
    icmp_typename: str
    icmp_v6_typename: str
    index: int
    ip_version: str
    logging: bool
    match_ip_sec: bool
    match_opposite_protocol: bool
    predefined: bool
    protocol: str
    schedule: FirewallPolicySchedule


class FirewallPolicy(ApiItem):
    """Represent a firewall policy."""

    raw: TypedFirewallPolicy

    @property
    def id(self) -> str:
        """Unique id of firewall policy."""
        return self.raw["_id"]

    @property
    def name(self) -> str:
        """Firewall policy name."""
        return self.raw["name"]

    @property
    def enabled(self) -> bool:
        """Is firewall policy enabled."""
        return self.raw["enabled"]

    @property
    def action(self) -> str:
        """Firewall policy action."""
        return self.raw["action"]

    @property
    def predefined(self) -> bool:
        """Is this a predefined policy."""
        return self.raw["predefined"]

    @property
    def description(self) -> str:
        """Policy description."""
        return self.raw.get("description", "")

    @property
    def protocol(self) -> str:
        """Policy protocol."""
        return self.raw["protocol"]

    @property
    def connection_state_type(self) -> str:
        """Connection state type."""
        return self.raw["connection_state_type"]

    @property
    def connection_states(self) -> list[str]:
        """List of connection states."""
        return self.raw["connection_states"]

    @property
    def create_allow_respond(self) -> bool:
        """Whether to create allow respond rule."""
        return self.raw["create_allow_respond"]

    @property
    def destination(self) -> FirewallPolicyEndpoint:
        """Destination endpoint configuration."""
        return self.raw["destination"]

    @property
    def source(self) -> FirewallPolicyEndpoint:
        """Source endpoint configuration."""
        return self.raw["source"]

    @property
    def icmp_typename(self) -> str:
        """ICMP type name."""
        return self.raw["icmp_typename"]

    @property
    def icmp_v6_typename(self) -> str:
        """ICMPv6 type name."""
        return self.raw["icmp_v6_typename"]

    @property
    def index(self) -> int:
        """Policy index/priority."""
        return self.raw["index"]

    @property
    def ip_version(self) -> str:
        """IP version (IPv4/IPv6/BOTH)."""
        return self.raw["ip_version"]

    @property
    def logging(self) -> bool:
        """Whether logging is enabled."""
        return self.raw["logging"]

    @property
    def match_ip_sec(self) -> bool:
        """Whether to match IPSec traffic."""
        return self.raw["match_ip_sec"]

    @property
    def match_opposite_protocol(self) -> bool:
        """Whether to match opposite protocol."""
        return self.raw["match_opposite_protocol"]

    @property
    def schedule(self) -> FirewallPolicySchedule:
        """Policy schedule configuration."""
        return self.raw["schedule"]


@dataclass
class FirewallPolicyListRequest(ApiRequestV2):
    """Request object for listing firewall policies."""

    @classmethod
    def create(cls) -> Self:
        """Create firewall policy list request."""
        return cls(method="get", path="/firewall-policies", data=None)


@dataclass
class FirewallPolicyUpdateRequest(ApiRequestV2):
    """Request object for updating a firewall policy. Note: You can't update the default policies - only ones you've created."""

    @classmethod
    def create(cls, policy: TypedFirewallPolicy) -> Self:
        """Create method for firewall policy update request."""
        return cls(
            method="put",
            path=f"/firewall-policies/{policy['_id']}",
            data=policy,
        )
