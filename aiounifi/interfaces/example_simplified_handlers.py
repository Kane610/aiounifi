"""Example of using the simplified API handler.

This file demonstrates how the new APIHandler improvements reduce boilerplate
and provide better error handling and configuration options.
"""

from typing import TYPE_CHECKING

from ..models.message import MessageKey
from ..models.site import Site, SiteListRequest
from .api_handlers import APIHandler, APIHandlerConfig, create_api_handler

if TYPE_CHECKING:
    from ..controller import Controller


# OLD WAY: Traditional subclassing (still supported)
class SitesOldWay(APIHandler[Site]):
    """Traditional way - lots of boilerplate."""

    obj_id_key = "_id"
    item_cls = Site
    api_request = SiteListRequest.create()


# NEW WAY 1: Using configuration object
class SitesWithConfig(APIHandler[Site]):
    """Using configuration object for cleaner initialization."""

    def __init__(self, controller: Controller) -> None:
        """Initialize with configuration object."""
        config = APIHandlerConfig(
            obj_id_key="_id",
            item_cls=Site,
            api_request=SiteListRequest.create(),
        )
        super().__init__(controller, config)


# NEW WAY 2: Using factory function (most concise)
Sites = create_api_handler(
    obj_id_key="_id",
    item_cls=Site,
    api_request=SiteListRequest.create(),
)

# NEW WAY 3: For handlers with message processing
DevicesHandler = create_api_handler(
    obj_id_key="mac",
    item_cls=Site,  # Would normally be Device
    api_request=SiteListRequest.create(),  # Would normally be DeviceListRequest
    process_messages=(MessageKey.DEVICE,),
)
