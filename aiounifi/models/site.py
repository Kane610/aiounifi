"""Site is a specific grouping in a UniFi network."""
from dataclasses import dataclass
from typing import Self, TypedDict

from .api import ApiItem, ApiRequest


class TypedSite(TypedDict):
    """Site description."""

    _id: str
    attr_hidden_id: str
    attr_no_delete: bool
    desc: str
    name: str
    role: str


@dataclass
class SiteListRequest(ApiRequest):
    """Request object for site list."""

    @classmethod
    def create(cls) -> Self:
        """Create site list request."""
        return cls(method="get", path="/self/sites")

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        """Url to list sites is global for controller."""
        if is_unifi_os:
            return f"/proxy/network/api{self.path}"
        return f"/api{self.path}"


class Site(ApiItem):
    """Represents a network device."""

    raw: TypedSite

    @property
    def site_id(self) -> str:
        """Site ID."""
        return self.raw["_id"]

    @property
    def description(self) -> str:
        """Site description."""
        return self.raw["desc"]

    @property
    def hidden_id(self) -> str:
        """Unknown."""
        return self.raw["attr_hidden_id"]

    @property
    def name(self) -> str:
        """Site name."""
        return self.raw["name"]

    @property
    def no_delete(self) -> bool:
        """Can not delete site."""
        return self.raw["attr_no_delete"]

    @property
    def role(self) -> str:
        """User role."""
        return self.raw["role"]
