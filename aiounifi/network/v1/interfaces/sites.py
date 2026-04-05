"""Site information interface for UniFi Network API."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..models.site import Site, SiteData, SitesRequest

if TYPE_CHECKING:
    from ..client import Client

SiteList = list[Site]


class Sites:
    """Read site information from the Network API."""

    def __init__(self, client: Client) -> None:
        """Initialize sites interface."""
        self.client = client

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
        data = await self.client.request(request)
        return [Site(cast(SiteData, item)) for item in data.get("data", [])]
