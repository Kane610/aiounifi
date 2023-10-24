"""DPI Restrictions as part of a UniFi network."""

from ..models.api import TypedApiResponse
from ..models.dpi_restriction_app import (
    DPIRestrictionApp,
    DPIRestrictionAppEnableRequest,
    DpiRestrictionAppListRequest,
)
from ..models.message import MessageKey
from .api_handlers import APIHandler


class DPIRestrictionApps(APIHandler[DPIRestrictionApp]):
    """Represents DPI App configurations."""

    obj_id_key = "_id"
    item_cls = DPIRestrictionApp
    process_messages = (MessageKey.DPI_APP_ADDED, MessageKey.DPI_APP_UPDATED)
    remove_messages = (MessageKey.DPI_APP_REMOVED,)
    api_request = DpiRestrictionAppListRequest.create()

    async def enable(self, app_id: str) -> TypedApiResponse:
        """Enable DPI Restriction Group Apps."""
        return await self.controller.request(
            DPIRestrictionAppEnableRequest.create(app_id, enable=True)
        )

    async def disable(self, app_id: str) -> TypedApiResponse:
        """Disable DPI Restriction Group Apps."""
        return await self.controller.request(
            DPIRestrictionAppEnableRequest.create(app_id, enable=False)
        )
