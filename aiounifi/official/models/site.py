"""Site models for official UniFi API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .api import OfficialApiRequest, OfficialApiResponse


@dataclass
class OfficialSitesRequest(OfficialApiRequest):
    """Request for listing local sites from the official API."""

    @classmethod
    def create(
        cls,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> OfficialSitesRequest:
        """Construct a request for one sites page."""
        params: dict[str, str | int] = {
            "offset": max(offset, 0),
            "limit": max(limit, 1),
        }
        if filter_value:
            params["filter"] = filter_value
        return cls(method="get", path="/v1/sites", params=params)


class OfficialSite:
    """Represent one site from official API data."""

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


class OfficialSiteOverviewPage:
    """Represent one sites page with metadata and parsed site objects."""

    def __init__(self, raw: OfficialApiResponse) -> None:
        """Initialize page wrapper."""
        self.raw = raw
        self.sites = [OfficialSite(item) for item in raw.get("data", [])]

    @property
    def offset(self) -> int:
        """Offset of this page."""
        return int(self.raw.get("offset", 0))

    @property
    def limit(self) -> int:
        """Requested page size."""
        return int(self.raw.get("limit", 0))

    @property
    def count(self) -> int:
        """Count of returned rows in this page."""
        return int(self.raw.get("count", len(self.sites)))

    @property
    def total_count(self) -> int:
        """Total rows available on the server side."""
        return int(self.raw.get("totalCount", self.count))
