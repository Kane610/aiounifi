"""DPI Restrictions as part of a UniFi network."""

from __future__ import annotations

from dataclasses import dataclass

from .api import APIItem
from .request_object import RequestObject


@dataclass
class DPIRestrictionAppEnableRequest(RequestObject):
    """Request object for enabling DPI Restriction App."""

    @classmethod
    def create(cls, app_id: str, enable: bool) -> "DPIRestrictionAppEnableRequest":
        """Create enabling DPI Restriction App request."""
        return cls(
            method="put",
            path=f"/rest/dpiapp/{app_id}",
            data={"enabled": enable},
        )


class DPIRestrictionApp(APIItem):
    """Represents a DPI App configuration."""

    @property
    def id(self) -> str:
        """DPI app ID."""
        return self.raw["_id"]

    @property
    def apps(self) -> list:
        """List of apps."""
        return self.raw["apps"]

    @property
    def blocked(self) -> bool:
        """Is blocked."""
        return self.raw["blocked"]

    @property
    def cats(self) -> list:
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
