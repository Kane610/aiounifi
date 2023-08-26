"""Traffic rules as part of a UniFi network."""

from dataclasses import dataclass

from typing_extensions import NotRequired, TypedDict
from typing import TYPE_CHECKING, Any

from .api import ApiItem, ApiRequest

class BandwidthLimit(TypedDict):
    """Bandwith limit type definition"""
    download_limit_kbps: int
    enabled: bool
    upload_limit_kbps: int

class PortRange(TypedDict):
    port_start: int
    port_stop: int
class IPAdress(TypedDict):
    ip_or_subnet: str
    ip_version: str
    port_ranges: list[PortRange]
    ports: list[int]

class IPRange(TypedDict):
    ip_start: str
    ip_stop: str
    ip_version: str

class Schedule(TypedDict):
    date_end: str
    date_start: str
    mode: str
    repeat_on_days: list[str]
    time_all_day: bool
    time_range_end: str
    time_range_start: str

class TargetDevice(TypedDict):
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
    ip_addresses: list[IPAdress]
    ip_ranges: list[IPRange]
    matching_target: str
    network_ids: list[str]
    regions: list[str]
    schedule: Schedule
    target_devices: list[TargetDevice]


@dataclass
class TrafficRuleRequest(ApiRequest):
    """Data class with required properties of a traffic rule API request."""
    '''We need a way to indicate if, for our model, the v2 API must be called.
    Therefore an intermediate dataclass 'TrafficRuleRequest' is made,
    for passing the correct path. This way, we do not need to alter any of the
    other classes that not need to know about the version of the api used.
    With the refactoring of the aiounifi-library, this is now possible.
    '''

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        return f"/proxy/network/v2/api/site/{site}{self.path}"

@dataclass
class TrafficRuleListRequest(TrafficRuleRequest):
    """Request object for traffic rule list."""

    @classmethod
    def create(cls) -> "TrafficRuleListRequest":
        """Create traffic rule request."""
        return cls(method="get", path="/trafficrules", data=None)

@dataclass
class TrafficRuleEnableRequest(TrafficRuleRequest):
    """Request object for traffic rule enable."""

    @classmethod
    def create(cls, traffic_rule: dict[str, Any], enable: bool) -> "TrafficRuleEnableRequest":
        """Create traffic rule enable request."""
        traffic_rule['enabled'] = enable
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
        """What action is defined by this traffic rule"""
        return self.raw["action"]

    @property
    def matching_target(self) -> str:
        """What target is matched by this traffic rule"""
        return self.raw["matching_target"]

    @property
    def target_devices(self) -> list[dict[str, str]]:
        """What target devices are affected by this traffic rule"""
        return self.raw["target_devices"]

