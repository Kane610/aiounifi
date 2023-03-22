"""DPI Restrictions as part of a UniFi network."""

from dataclasses import dataclass
from typing import TypedDict

from .api import ApiItem, ApiRequest


class TypedDPIRestrictionApp(TypedDict):
    """DPI restriction app type definition."""

    _id: str
    apps: list[str]
    blocked: bool
    cats: list[str]
    enabled: bool
    log: bool
    site_id: str


@dataclass
class DPIRestrictionAppEnableRequest(ApiRequest):
    """Request object for enabling DPI Restriction App."""

    @classmethod
    def create(cls, app_id: str, enable: bool) -> "DPIRestrictionAppEnableRequest":
        """Create enabling DPI Restriction App request."""
        return cls(
            method="put",
            path=f"/rest/dpiapp/{app_id}",
            data={"enabled": enable},
        )


class DPIRestrictionApp(ApiItem):
    """Represents a DPI App configuration."""

    raw: TypedDPIRestrictionApp

    @property
    def id(self) -> str:
        """DPI app ID."""
        return self.raw["_id"]

    @property
    def apps(self) -> list[str]:
        """List of apps."""
        return self.raw["apps"]

    @property
    def blocked(self) -> bool:
        """Is blocked."""
        return self.raw["blocked"]

    @property
    def cats(self) -> list[str]:
        """Categories."""
        return self.raw["cats"]

    @property
    def enabled(self) -> bool:
        """Is enabled."""
        return self.raw["enabled"]

    @property
    def log(self) -> bool:
        """Is logging enabled."""
        return self.raw["log"]

    @property
    def site_id(self) -> str:
        """Site ID."""
        return self.raw["site_id"]
