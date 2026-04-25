"""Site models for UniFi Network API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from ....models.api import ApiItem
from .api import DEFAULT_PAGE_LIMIT, DEFAULT_PAGE_OFFSET, ApiRequest


class SiteData(TypedDict):
    """Typed payload for one site returned by the network API."""

    id: str
    internalReference: str
    name: str


@dataclass
class SitesRequest(ApiRequest):
    """Request for listing local sites from the network API."""

    @classmethod
    def create(
        cls,
        offset: int = DEFAULT_PAGE_OFFSET,
        limit: int = DEFAULT_PAGE_LIMIT,
        filter_value: str | None = None,
    ) -> SitesRequest:
        """Construct a request for one sites page."""
        params: dict[str, str | int] = {
            "offset": max(offset, DEFAULT_PAGE_OFFSET),
            "limit": max(limit, 1),
        }
        if filter_value:
            params["filter"] = filter_value
        return cls(method="get", path="/v1/sites", params=params)


class Site(ApiItem):
    """Represent one site from network API data."""

    raw: SiteData

    @property
    def site_id(self) -> str:
        """Site identifier used for further API calls."""
        return self.raw["id"]

    @property
    def internal_reference(self) -> str:
        """Internal site reference returned by API."""
        return self.raw["internalReference"]

    @property
    def name(self) -> str:
        """Display name of the site."""
        return self.raw["name"]
