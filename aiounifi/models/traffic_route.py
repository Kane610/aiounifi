"""Traffic routes as part of a UniFi network."""
from dataclasses import dataclass
from enum import StrEnum
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequestV2


class MatchingTarget(StrEnum):
    """Possible matching targets for a traffic rule."""

    DOMAIN = "DOMAIN"
    IP = "IP"
    INTERNET = "INTERNET"
    REGION = "REGION"


class PortRange(TypedDict):
    """Port range type definition."""

    port_start: int
    port_stop: int


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


class Domain(TypedDict):
    """A target domain for a traffic route."""

    domain: str
    port_ranges: list[PortRange]
    ports: list[int]


class TypedTrafficRoute(TypedDict):
    """Traffic route type definition."""

    _id: str
    description: str
    domains: list[Domain]
    enabled: bool
    ip_addresses: list[IPAddress]
    ip_ranges: list[IPRange]
    matching_target: MatchingTarget
    network_id: str
    next_hop: str
    regions: list[str]
    target_devices: list[TargetDevice]


@dataclass
class TrafficRouteListRequest(ApiRequestV2):
    """Request object for traffic route list."""

    @classmethod
    def create(cls) -> Self:
        """Create traffic route request."""
        return cls(method="get", path="/trafficroutes", data=None)


@dataclass
class TrafficRouteSaveRequest(ApiRequestV2):
    """Request object for saving a traffic route.

    To modify a route, you must make sure the `raw` attribute of the TypedTrafficRoute is modified.
    The properties provide convient access for reading, however do not provide means of setting values.
    """

    @classmethod
    def create(
        cls, traffic_route: TypedTrafficRoute, enable: bool | None = None
    ) -> Self:
        """Create traffic route save request."""
        if enable is not None:
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
    def domains(self) -> list[Domain]:
        """What IP addresses are matched against by this traffic route.

        Note: Domain matching requires the client devices to use the UniFi gateway as the DNS server.
        """
        return self.raw["domains"]

    @property
    def enabled(self) -> bool:
        """Is traffic route enabled."""
        return self.raw["enabled"]

    @property
    def ip_addresses(self) -> list[IPAddress]:
        """What IP addresses are matched against by this traffic route."""
        return self.raw["ip_addresses"]

    @property
    def ip_ranges(self) -> list[IPRange]:
        """What IP addresses are matched against by this traffic route."""
        return self.raw["ip_ranges"]

    @property
    def matching_target(self) -> MatchingTarget:
        """What target is matched by this traffic route."""
        return self.raw["matching_target"]

    @property
    def network_id(self) -> str:
        """Network ID that this rule applies to."""
        return self.raw["network_id"]

    @property
    def next_hop(self) -> str:
        """Used for defining a static route."""
        return self.raw["next_hop"]

    @property
    def regions(self) -> list[str]:
        """Regions that the rule applies to."""
        return self.raw["regions"]

    @property
    def target_devices(self) -> list[TargetDevice]:
        """What target devices are affected by this traffic route."""
        return self.raw["target_devices"]
