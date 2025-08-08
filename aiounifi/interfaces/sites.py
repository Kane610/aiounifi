"""UniFi sites of network infrastructure."""

from ..models.site import Site, SiteListRequest
from .api_handlers import create_api_handler

# Using the new factory approach instead of subclassing
Sites = create_api_handler(
    obj_id_key="_id",
    item_cls=Site,
    api_request=SiteListRequest.create(),
)
