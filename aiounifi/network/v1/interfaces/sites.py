"""Site information interface for UniFi Network Integration API v1."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from ..models.site import Site, SiteData, SitesRequest

if TYPE_CHECKING:
    from ..api_client import ApiClient

SiteList = list[Site]


class Sites:
    """Read site information from the Integration API."""

    def __init__(self, api_client: ApiClient) -> None:
        """Initialize sites interface."""
        self.api_client = api_client

    async def list(self, filter_value: str | None = None) -> SiteList:
        """List local sites using the default first-page request."""
        return await self.list_page(filter_value=filter_value)

    async def list_page(
        self,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> SiteList:
        """List one page of local sites."""
        request = SitesRequest.create(offset, limit, filter_value)
        data = await self.api_client.request(request)
        return [Site(cast("SiteData", item)) for item in data.get("data", [])]

    def resolve_site_uuid(
        self,
        site: str,
        sites: Sequence[Site] | None = None,
    ) -> str | None:
        """Resolve Integration API site UUID from site token, name, or id."""
        resolved_sites = list(sites) if sites is not None else []
        site_token = site.strip()

        for network_site in resolved_sites:
            if network_site.internal_reference == site_token:
                return network_site.site_id

        for network_site in resolved_sites:
            if site_token in (network_site.name, network_site.site_id):
                return network_site.site_id

        return None
