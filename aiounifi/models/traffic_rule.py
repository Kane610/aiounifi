"""Traffic rules as part of a UniFi network."""

from dataclasses import dataclass
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequestV2


class TypedFirewallZone(TypedDict):
    """Firewall zone type definition."""

    _id: str
    name: str


class FirewallZone(ApiItem):
    """Represent a firewall zone."""

    raw: TypedFirewallZone

    @property
    def id(self) -> str:
        return self.raw["_id"]

    @property
    def name(self) -> str:
        """Firewall zone name."""
        return self.raw["name"]


class TypedFirewallPolicy(TypedDict):
    """Firewall policy type definition."""

    _id: str
    action: str
    name: str
    enabled: bool


class FirewallPolicy(ApiItem):
    """Represent a firewall policy."""

    raw: TypedFirewallPolicy

    @property
    def id(self) -> str:
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


@dataclass
class FirewallZoneListRequest(ApiRequestV2):
    """Request object for listing firewall zones."""

    @classmethod
    def create(cls) -> Self:
        """Create firewall zone list request."""
        return cls(method="get", path="/firewall/zone", data=None)


@dataclass
class FirewallZoneUpdateRequest(ApiRequestV2):
    """Request object for updating a firewall zone."""

    @classmethod
    def create(cls, zone: FirewallZone) -> Self:
        """Create firewall zone update request."""
        return cls(
            method="put",
            path=f"/firewall/zone/{zone['name']}",
            data=zone,
        )


@dataclass
class FirewallPolicyListRequest(ApiRequestV2):
    """Request object for listing firewall policies."""

    @classmethod
    def create(cls) -> Self:
        """Create firewall policy list request."""
        return cls(method="get", path="/firewall-policies", data=None)


@dataclass
class FirewallPolicyUpdateRequest(ApiRequestV2):
    """Request object for updating a firewall policy."""

    @classmethod
    def create(cls, policy: TypedFirewallPolicy) -> Self:
        json = []
        json.append(policy)
        """Create firewall policy update request."""
        return cls(
            method="put",
            path="/firewall-policies/batch",
            data=json,
        )


class BandwidthLimit(TypedDict):
    """Bandwidth limit type definition."""

    download_limit_kbps: int
    enabled: bool
    upload_limit_kbps: int


class PortRange(TypedDict):
    """Port range type definition."""

    port_start: int
    port_stop: int


class IPAddress(TypedDict):
    """IP Address for which traffic rule is applicable type definition."""

    ip_or_subnet: str
    ip_version: str
    port_ranges: list[PortRange]
    ports: list[int]


class IPRange(TypedDict):
    """IP Range type definition."""

    ip_start: str
    ip_stop: str
    ip_version: str


class Schedule(TypedDict):
    """Schedule to enable/disable traffic rule type definition."""

    date_end: str
    date_start: str
    mode: str
    repeat_on_days: list[str]
    time_all_day: bool
    time_range_end: str
    time_range_start: str


class TargetDevice(TypedDict):
    """Target device to which the traffic rule applies."""

    client_mac: NotRequired[str]
    network_id: NotRequired[str]
    type: str


class TypedTrafficRule(TypedDict):
    """Traffic rule type definition."""

    _id: str
    action: str
    app_category_ids: list[str]
    app_ids: list[str]
    bandwidth_limit: BandwidthLimit
    description: str
    domains: list[str]
    enabled: bool
    ip_addresses: list[IPAddress]
    ip_ranges: list[IPRange]
    matching_target: str
    network_ids: list[str]
    regions: list[str]
    schedule: Schedule
    target_devices: list[TargetDevice]
    zone: NotRequired[str]


@dataclass
class TrafficRuleListRequest(ApiRequestV2):
    """Request object for traffic rule list."""

    @classmethod
    def create(cls) -> Self:
        """Create traffic rule request."""
        return cls(method="get", path="/trafficrules", data=None)


@dataclass
class TrafficRuleCreateRequest(ApiRequestV2):
    """Request object for traffic rule creation."""

    @classmethod
    def create(cls, traffic_rule: TypedTrafficRule) -> Self:
        """Create traffic rule create request."""
        return cls(
            method="post",
            path="/trafficrules",
            data=traffic_rule,
        )


@dataclass
class TrafficRuleUpdateRequest(ApiRequestV2):
    """Request object for traffic rule update."""

    @classmethod
    def create(cls, traffic_rule: TypedTrafficRule) -> Self:
        """Create traffic rule update request."""
        return cls(
            method="put",
            path=f"/trafficrules/{traffic_rule['_id']}",
            data=traffic_rule,
        )


@dataclass
class TrafficRuleDeleteRequest(ApiRequestV2):
    """Request object for traffic rule deletion."""

    @classmethod
    def create(cls, traffic_rule_id: str) -> Self:
        """Create traffic rule delete request."""
        return cls(
            method="delete",
            path=f"/trafficrules/{traffic_rule_id}",
            data=None,
        )


@dataclass
class TrafficRuleEnableRequest(ApiRequestV2):
    """Request object for traffic rule enable."""

    @classmethod
    def create(cls, traffic_rule: TypedTrafficRule, enable: bool) -> Self:
        """Create traffic rule enable request."""
        traffic_rule["enabled"] = enable
        return cls(
            method="put",
            path=f"/trafficrules/{traffic_rule['_id']}",
            data=traffic_rule,
        )


class TrafficRule(ApiItem):
    """Represent a traffic rule configuration."""

    raw: TypedTrafficRule

    @property
    def id(self) -> str:
        """ID of traffic rule."""
        return self.raw["_id"]

    @property
    def description(self) -> str:
        """Description given by user to traffic rule."""
        return self.raw["description"]

    @property
    def enabled(self) -> bool:
        """Is traffic rule enabled."""
        return self.raw["enabled"]

    @property
    def action(self) -> str:
        """What action is defined by this traffic rule."""
        return self.raw["action"]

    @property
    def matching_target(self) -> str:
        """What target is matched by this traffic rule."""
        return self.raw["matching_target"]

    @property
    def target_devices(self) -> list[TargetDevice]:
        """What target devices are affected by this traffic rule."""
        return self.raw["target_devices"]

    @property
    def zone(self) -> str | None:
        """Zone for which this traffic rule applies."""
        return self.raw.get("zone")
