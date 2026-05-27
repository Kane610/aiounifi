"""Object-oriented network configurations as part of a UniFi network."""

from dataclasses import dataclass
from enum import StrEnum
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequestV2


class ObjectOrientedNetworkInternetMode(StrEnum):
    TURN_OFF_INTERNET = "TURN_OFF_INTERNET"
    # Add other modes as needed


class ObjectOrientedNetworkSecureInternetT(TypedDict):
    """Internet access configuration."""

    mode: ObjectOrientedNetworkInternetMode
    schedule: NotRequired[dict[str, str]]


class ObjectOrientedNetworkTarget(TypedDict):
    """Target affected by object-oriented network configuration."""

    type: str
    value: str


class ObjectOrientedNetworkSecureT(TypedDict):
    """Security configuration."""

    enabled: NotRequired[bool]
    internet: NotRequired[ObjectOrientedNetworkSecureInternetT]


@dataclass
class ObjectOrientedNetworkSecureInternet:
    mode: ObjectOrientedNetworkInternetMode
    schedule: dict[str, str] | None = None

    @classmethod
    def from_dict(
        cls, data: ObjectOrientedNetworkSecureInternetT
    ) -> "ObjectOrientedNetworkSecureInternet":
        return cls(
            mode=ObjectOrientedNetworkInternetMode(data["mode"]),
            schedule=data.get("schedule"),
        )


@dataclass
class ObjectOrientedNetworkSecure:
    available: bool = False
    enabled: bool | None = None
    internet: ObjectOrientedNetworkSecureInternet | None = None

    @classmethod
    def from_dict(
        cls, data: ObjectOrientedNetworkSecureT
    ) -> "ObjectOrientedNetworkSecure":
        internet = data.get("internet")
        return cls(
            available=bool(data),
            enabled=data.get("enabled"),
            internet=ObjectOrientedNetworkSecureInternet.from_dict(internet)
            if internet
            else None,
        )


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
    targets: NotRequired[list[str | ObjectOrientedNetworkTarget]]
    qos: NotRequired[ObjectOrientedNetworkQos]
    route: NotRequired[ObjectOrientedNetworkRoute]
    secure: NotRequired[ObjectOrientedNetworkSecureT]


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
    def target_type(self) -> str | None:
        """Target type for object-oriented network configuration."""
        return self.raw.get("target_type")

    @property
    def targets(self) -> list[str | ObjectOrientedNetworkTarget]:
        """Targets affected by object-oriented network configuration."""
        return self.raw.get("targets", [])

    @property
    def secure(self) -> ObjectOrientedNetworkSecureT:
        """Security configuration."""
        default: ObjectOrientedNetworkSecureT = {"enabled": False}
        return default | self.raw.get("secure", {})

    @property
    def qos(self) -> ObjectOrientedNetworkQos:
        """QoS configuration."""
        default: ObjectOrientedNetworkQos = {"enabled": False}
        return default | self.raw.get("qos", {})

    @property
    def route(self) -> ObjectOrientedNetworkRoute:
        """Routing configuration."""
        default: ObjectOrientedNetworkRoute = {"enabled": False}
        return default | self.raw.get("route", {})
