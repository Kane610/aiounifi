"""Sites."""

from __future__ import annotations

from ..api_handlers import APIHandler
from ..models.site import ListSitesRequest, Site


class Sites(APIHandler[Site]):
    """The sites the API key can see."""

    item_cls = Site
    obj_id_key = "id"

    def list_request(self, offset: int, limit: int) -> ListSitesRequest:
        """Return the list request for one page."""
        return ListSitesRequest.create(offset, limit)

    async def list_page(
        self,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> list[Site]:
        """Return one page of sites without touching the cache."""
        response = await self.api_client.request(
            ListSitesRequest.create(offset, limit, filter_value)
        )
        return [Site(raw) for raw in response["data"]]
