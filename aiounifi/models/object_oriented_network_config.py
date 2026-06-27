"""Object-oriented network configurations as part of a UniFi network."""

from dataclasses import dataclass
from enum import StrEnum
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequestV2


class ObjectOrientedNetworkInternetMode(StrEnum):
    """Possible internet access modes for security configuration."""

    TURN_OFF_INTERNET = "TURN_OFF_INTERNET"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> Self:
        """Set default enum member if an unknown internet mode is provided."""
        return cls.UNKNOWN


class ObjectOrientedNetworkSecureInternetT(TypedDict):
    """Internet access configuration."""

    mode: ObjectOrientedNetworkInternetMode
    schedule: NotRequired[dict[str, str]]


@dataclass
class ObjectOrientedNetworkSecureInternet:
    """Represent internet access configuration."""

    mode: ObjectOrientedNetworkInternetMode
    schedule: dict[str, str] | None = None

    @classmethod
    def from_dict(cls, data: ObjectOrientedNetworkSecureInternetT) -> Self:
        """Create internet access configuration."""
        return cls(
            mode=ObjectOrientedNetworkInternetMode(data.get("mode", "unknown")),
            schedule=data.get("schedule"),
        )


class ObjectOrientedNetworkTarget(TypedDict):
    """Target affected by object-oriented network configuration."""

    type: str
    value: str


class ObjectOrientedNetworkSecureT(TypedDict):
    """Security configuration."""

    enabled: NotRequired[bool]
    internet: NotRequired[ObjectOrientedNetworkSecureInternetT]


@dataclass
class ObjectOrientedNetworkSecure:
    """Represent security configuration."""

    available: bool = False
    enabled: bool = False
    internet: ObjectOrientedNetworkSecureInternet | None = None

    @classmethod
    def from_dict(cls, data: ObjectOrientedNetworkSecureT | None) -> Self:
        """Create security configuration."""
        if not data:
            return cls()

        internet = data.get("internet")
        return cls(
            available=True,
            enabled=data.get("enabled") is True,
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
    secure: NotRequired[ObjectOrientedNetworkSecureT | None]


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
    def secure(self) -> ObjectOrientedNetworkSecure:
        """Security configuration."""
        return ObjectOrientedNetworkSecure.from_dict(self.raw.get("secure"))

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
