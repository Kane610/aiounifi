"""Sites."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from ....models.api import ApiItem
from .api import DEFAULT_PAGE_LIMIT, DEFAULT_PAGE_OFFSET, ApiRequest, page_params


class SiteData(TypedDict):
    """One site as returned by GET /v1/sites."""

    id: str
    internalReference: str
    name: str


@dataclass
class ListSitesRequest(ApiRequest):
    """List the sites the API key can see."""

    @classmethod
    def create(
        cls,
        offset: int = DEFAULT_PAGE_OFFSET,
        limit: int = DEFAULT_PAGE_LIMIT,
        filter_value: str | None = None,
    ) -> ListSitesRequest:
        """Create a request for one page of sites."""
        return cls(
            method="get",
            path="/v1/sites",
            params=page_params(offset, limit, filter_value),
        )


class Site(ApiItem):
    """A site."""

    raw: SiteData

    @property
    def site_id(self) -> str:
        """UUID used in every site-scoped path."""
        return self.raw["id"]

    @property
    def internal_reference(self) -> str:
        """Short name of the site, `default` for the first one.

        This is the same value the legacy API calls the site name, so a
        legacy site token resolves to a v1 site through this field.
        """
        return self.raw["internalReference"]

    @property
    def name(self) -> str:
        """Display name of the site."""
        return self.raw["name"]
