"""Site is a specific grouping in a UniFi network."""

from dataclasses import dataclass

from .api import ApiRequest


@dataclass
class SiteListRequest(ApiRequest):
    """Request object for site list."""

    @classmethod
    def create(cls) -> "SiteListRequest":
        """Create site list request."""
        return cls(method="get", path="", data=None)

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        """Url to list sites is global for controller."""
        if is_unifi_os:
            return "/proxy/network/api/self/sites"
        return "/api/self/sites"


@dataclass
class SiteDescriptionRequest(ApiRequest):
    """Request object for site description."""

    @classmethod
    def create(cls) -> "SiteDescriptionRequest":
        """Create site list request."""
        return cls(method="get", path="/self", data=None)
