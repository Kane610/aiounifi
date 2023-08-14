"""UniFi sites of network infrastructure."""

from ..models.site import Site, SiteListRequest
from .api_handlers import APIHandler


class Sites(APIHandler[Site]):
    """Represent UniFi sites."""

    obj_id_key = "_id"
    path = "/self/sites"
    item_cls = Site
    api_request = SiteListRequest.create()
