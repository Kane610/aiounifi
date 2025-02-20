"""Firewall zones as part of a UniFi network."""

from dataclasses import dataclass
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequestV2


class TypedFirewallZone(TypedDict):
    """Firewall zone type definition."""

    _id: str
    name: str
    attr_no_edit: bool
    default_zone: bool
    network_ids: list[str]
    zone_key: NotRequired[str]


class FirewallZone(ApiItem):
    """Represent a firewall zone."""

    raw: TypedFirewallZone

    @property
    def id(self) -> str:
        """Unique ID of firewall zone."""
        return self.raw["_id"]

    @property
    def name(self) -> str:
        """Firewall zone name."""
        return self.raw["name"]

    @property
    def attr_no_edit(self) -> bool:
        """Whether zone is editable."""
        return self.raw["attr_no_edit"]

    @property
    def default_zone(self) -> bool:
        """Whether this is a default zone."""
        return self.raw["default_zone"]

    @property
    def network_ids(self) -> list[str]:
        """List of network IDs associated with zone."""
        return self.raw["network_ids"]

    @property
    def zone_key(self) -> str | None:
        """Zone key identifier."""
        return self.raw.get("zone_key")


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
    def create(cls, zone: TypedFirewallZone) -> Self:
        """Create firewall zone update request."""
        return cls(
            method="put",
            path=f"/firewall/zone/{zone['_id']}",
            data=zone,
        )
