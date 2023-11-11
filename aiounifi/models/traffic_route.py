"""Traffic route as part of a UniFi network."""

from dataclasses import dataclass
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequestV2
class IPAddress(TypedDict):
    """IP Address for which traffic route is applicable type definition."""

    ip_or_subnet: str
    ip_version: str
    port_ranges: list[PortRange]
    ports: list[int]

class IPRange(TypedDict):
    """IP Range type definition."""

    ip_start: str
    ip_stop: str
    ip_version: str
class TargetDevice(TypedDict):
    """Target device to which the traffic route applies."""

    client_mac: NotRequired[str]
    network_id: NotRequired[str]
    type: str


class TypedTrafficRoute(TypedDict):
    """Traffic route type definition."""

    _id: str
    description: str
    domains: list[str]
    enabled: bool
    ip_addresses: list[IPAddress]
    ip_ranges: list[IPRange]
    matching_target: str
    network_id: str
    regions: list[str]
    target_devices: list[TargetDevice]

class TypedTrafficRouteUpsert(TypedTrafficRoute):
    """Traffic route Upsert type definition."""

    next_hop: str
@dataclass
class TrafficRouteListRequest(ApiRequestV2):
    """Request object for traffic route list."""

    @classmethod
    def create(cls) -> Self:
        """Create traffic route request."""
        return cls(method="get", path="/trafficroutes", data=None)


@dataclass
class TrafficRouteEnableRequest(ApiRequestV2):
    """Request object for traffic route enable."""

    @classmethod
    def create(cls, traffic_route: TypedTrafficRouteUpsert, enable: bool) -> Self:
        """Create traffic route enable request."""
        traffic_route["enabled"] = enable
        return cls(
            method="put",
            path=f"/trafficroutes/{traffic_route['_id']}",
            data=traffic_route,
        )


class TrafficRoute(ApiItem):
    """Represent a traffic route configuration."""

    raw: TypedTrafficRoute

    @property
    def id(self) -> str:
        """ID of traffic route."""
        return self.raw["_id"]

    @property
    def description(self) -> str:
        """Description given by user to traffic route."""
        return self.raw["description"]

    @property
    def enabled(self) -> bool:
        """Is traffic route enabled."""
        return self.raw["enabled"]

    @property
    def action(self) -> str:
        """What action is defined by this traffic route."""
        return self.raw["action"]

    @property
    def matching_target(self) -> str:
        """What target is matched by this traffic route."""
        return self.raw["matching_target"]

    @property
    def target_devices(self) -> list[TargetDevice]:
        """What target devices are affected by this traffic route."""
        return self.raw["target_devices"]
