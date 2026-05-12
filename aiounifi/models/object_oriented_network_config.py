"""Object-oriented network configurations as part of a UniFi network."""

from dataclasses import dataclass
from typing import Any, NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequestV2


class ObjectOrientedNetworkInternet(TypedDict):
    """Internet access configuration."""

    mode: str
    schedule: NotRequired[dict[str, Any]]


class ObjectOrientedNetworkSecure(TypedDict):
    """Security configuration."""

    enabled: NotRequired[bool]
    internet: NotRequired[ObjectOrientedNetworkInternet]


class ObjectOrientedNetworkQos(TypedDict):
    """QoS configuration."""

    enabled: NotRequired[bool]


class ObjectOrientedNetworkRoute(TypedDict):
    """Routing configuration."""

    enabled: NotRequired[bool]
    kill_switch: NotRequired[bool]


class TypedObjectOrientedNetworkConfig(TypedDict):
    """Object-oriented network configuration type definition."""

    _id: NotRequired[str]
    id: NotRequired[str]
    enabled: bool
    name: str
    target_type: NotRequired[str]
    targets: NotRequired[list[Any]]
    qos: NotRequired[ObjectOrientedNetworkQos]
    route: NotRequired[ObjectOrientedNetworkRoute]
    secure: NotRequired[ObjectOrientedNetworkSecure]


@dataclass
class ObjectOrientedNetworkConfigListRequest(ApiRequestV2):
    """Request object for object-oriented network configuration list."""

    @classmethod
    def create(cls) -> Self:
        """Create object-oriented network configuration request."""
        return cls(method="get", path="/object-oriented-network-configs", data=None)


@dataclass
class ObjectOrientedNetworkConfigUpdateRequest(ApiRequestV2):
    """Request object for object-oriented network configuration update."""

    @classmethod
    def create(
        cls, config: TypedObjectOrientedNetworkConfig, enable: bool | None = None
    ) -> Self:
        """Create object-oriented network configuration update request."""
        if enable is not None:
            config["enabled"] = enable
        return cls(
            method="put",
            path=f"/object-oriented-network-config/{config.get('_id') or config['id']}",
            data=config,
        )


class ObjectOrientedNetworkConfig(ApiItem):
    """Represent an object-oriented network configuration."""

    raw: TypedObjectOrientedNetworkConfig

    @property
    def id(self) -> str:
        """ID of object-oriented network configuration."""
        return self.raw.get("_id") or self.raw["id"]

    @property
    def name(self) -> str:
        """Name of object-oriented network configuration."""
        return self.raw["name"]

    @property
    def enabled(self) -> bool:
        """Is object-oriented network configuration enabled."""
        return self.raw["enabled"]

    @property
    def target_type(self) -> str:
        """Target type for object-oriented network configuration."""
        return self.raw.get("target_type", "CLIENTS")

    @property
    def targets(self) -> list[Any]:
        """Targets affected by object-oriented network configuration."""
        return self.raw.get("targets", [])

    @property
    def secure(self) -> ObjectOrientedNetworkSecure:
        """Security configuration."""
        default: ObjectOrientedNetworkSecure = {"enabled": False}
        return self.raw.get("secure", default)

    @property
    def qos(self) -> ObjectOrientedNetworkQos:
        """QoS configuration."""
        default: ObjectOrientedNetworkQos = {"enabled": False}
        return self.raw.get("qos", default)

    @property
    def route(self) -> ObjectOrientedNetworkRoute:
        """Routing configuration."""
        default: ObjectOrientedNetworkRoute = {"enabled": False}
        return self.raw.get("route", default)
