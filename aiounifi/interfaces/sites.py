"""UniFi sites of network infrastructure."""

from collections.abc import Sequence

from ..models.site import Site, SiteListRequest
from .api_handlers import APIHandler


class Sites(APIHandler[Site]):
    """Represent UniFi sites."""

    obj_id_key = "_id"
    item_cls = Site
    api_request = SiteListRequest.create()

    def resolve_site_uuid(
        self,
        site: str,
        sites: Sequence[Site] | None = None,
    ) -> str | None:
        """Resolve Network API site UUID from primary site data."""
        site_token = site.strip()

        for primary_site in sites or self.values():
            if site_token not in (
                primary_site.hidden_id,
                primary_site.name,
                primary_site.site_id,
            ):
                continue

            external_id = primary_site.raw.get("external_id")
            if isinstance(external_id, str) and external_id:
                return external_id

        return None
