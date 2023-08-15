"""DPI Restrictions as part of a UniFi network."""

from dataclasses import dataclass

from typing_extensions import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequest


@dataclass
class DpiRestrictionGroupListRequest(ApiRequest):
    """Request object for DPI restriction group list."""

    @classmethod
    def create(cls) -> Self:
        """Create DPI restriction group list request."""
        return cls(method="get", path="/rest/dpigroup")


class TypedDPIRestrictionGroup(TypedDict):
    """DPI restriction group type definition."""

    _id: str
    attr_no_delete: NotRequired[bool]
    attr_hidden_id: str
    name: str
    site_id: str
    dpiapp_ids: NotRequired[list[str]]


class DPIRestrictionGroup(ApiItem):
    """Represents a DPI Group configuration."""

    raw: TypedDPIRestrictionGroup

    @property
    def id(self) -> str:
        """DPI group ID."""
        return self.raw["_id"]

    @property
    def attr_no_delete(self) -> bool | None:
        """Can be deleted."""
        if "attr_no_delete" in self.raw:
            return self.raw["attr_no_delete"]
        return None

    @property
    def attr_hidden_id(self) -> str:
        """Attr hidden ID."""
        return self.raw.get("attr_hidden_id", "")

    @property
    def name(self) -> str:
        """DPI group name."""
        return self.raw["name"]

    @property
    def site_id(self) -> str:
        """Site ID."""
        return self.raw["site_id"]

    @property
    def dpiapp_ids(self) -> list[str] | None:
        """DPI app IDs belonging to group."""
        if "dpiapp_ids" in self.raw:
            return self.raw["dpiapp_ids"]
        return None
