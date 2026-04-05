"""Site information interface for official UniFi API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.site import OfficialSiteOverviewPage, OfficialSitesRequest

if TYPE_CHECKING:
    from ..client import OfficialClient


class Sites:
    """Read site information from the official API."""

    def __init__(self, client: OfficialClient) -> None:
        """Initialize sites interface."""
        self.client = client

    async def list(
        self,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> OfficialSiteOverviewPage:
        """List one page of local sites."""
        request = OfficialSitesRequest.create(offset, limit, filter_value)
        data = await self.client.request(request)
        return OfficialSiteOverviewPage(data)
