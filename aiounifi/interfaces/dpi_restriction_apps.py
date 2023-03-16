"""DPI Restrictions as part of a UniFi network."""

from typing import Any

from ..models.dpi_restriction_app import (
    DPIRestrictionApp,
    DPIRestrictionAppEnableRequest,
)
from ..models.message import MessageKey
from .api_handlers import APIHandler


class DPIRestrictionApps(APIHandler[DPIRestrictionApp]):
    """Represents DPI App configurations."""

    obj_id_key = "_id"
    path = "/rest/dpiapp"
    item_cls = DPIRestrictionApp
    process_messages = (MessageKey.DPI_APP_ADDED, MessageKey.DPI_APP_UPDATED)
    remove_messages = (MessageKey.DPI_APP_REMOVED,)

    async def enable(self, app_id: str) -> list[dict[str, Any]]:
        """Enable DPI Restriction Group Apps."""
        return await self.controller.request(
            DPIRestrictionAppEnableRequest.create(app_id, enable=True)
        )

    async def disable(self, app_id: str) -> list[dict[str, Any]]:
        """Disable DPI Restriction Group Apps."""
        return await self.controller.request(
            DPIRestrictionAppEnableRequest.create(app_id, enable=False)
        )
