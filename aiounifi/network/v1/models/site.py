"""Site models for UniFi Network API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .api import ApiRequest


@dataclass
class SitesRequest(ApiRequest):
    """Request for listing local sites from the network API."""

    @classmethod
    def create(
        cls,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> SitesRequest:
        """Construct a request for one sites page."""
        params: dict[str, str | int] = {
            "offset": max(offset, 0),
            "limit": max(limit, 1),
        }
        if filter_value:
            params["filter"] = filter_value
        return cls(method="get", path="/v1/sites", params=params)


class Site:
    """Represent one site from network API data."""

    def __init__(self, raw: dict[str, Any]) -> None:
        """Initialize site model."""
        self.raw = raw

    @property
    def site_id(self) -> str:
        """Site identifier used for further API calls."""
        return str(self.raw.get("id", ""))

    @property
    def internal_reference(self) -> str:
        """Internal site reference returned by API."""
        return str(self.raw.get("internalReference", ""))

    @property
    def name(self) -> str:
        """Display name of the site."""
        return str(self.raw.get("name", ""))
