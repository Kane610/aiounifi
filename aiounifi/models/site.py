"""Site is a specific grouping in a UniFi network."""

from __future__ import annotations

from dataclasses import dataclass

from .request_object import RequestObject


@dataclass
class SiteListRequest(RequestObject):
    """Request object for site list."""

    @classmethod
    def create(cls) -> "SiteListRequest":
        """Create site list request."""
        return cls(
            method="get",
            path="",
            data=None,
        )

    def generate_url(self, url: str, site: str, is_unifi_os: bool) -> str:
        """Url to list sites is global for controller."""
        if is_unifi_os:
            url = f"{url}/proxy/network"
        return f"{url}/api/self/sites"


@dataclass
class SiteDescriptionRequest(RequestObject):
    """Request object for site description."""

    @classmethod
    def create(cls) -> "SiteDescriptionRequest":
        """Create site list request."""
        return cls(
            method="get",
            path="/self",
            data=None,
        )