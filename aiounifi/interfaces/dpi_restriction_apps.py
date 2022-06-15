"""DPI Restrictions as part of a UniFi network."""

from typing import Final

from ..models.dpi_restriction_app import DPIRestrictionApp
from ..models.event import MessageKey
from .api import APIItems

APP_URL: Final = "/rest/dpiapp"


class DPIRestrictionApps(APIItems):
    """Represents DPI App configurations."""

    obj_id_key = "_id"
    path = APP_URL
    item_cls = DPIRestrictionApp
    process_messages = (MessageKey.DPI_APP_ADDED, MessageKey.DPI_APP_UPDATED)
    remove_messages = (MessageKey.DPI_APP_REMOVED,)

    async def enable(self, app_id: str) -> list[dict]:
        """Enable DPI Restriction Group Apps."""
        app_url = f"{APP_URL}/{app_id}"
        data = {"enabled": True}
        return await self.controller.request("put", app_url, json=data)

    async def disable(self, app_id: str) -> list[dict]:
        """Disable DPI Restriction Group Apps."""
        app_url = f"{APP_URL}/{app_id}"
        data = {"enabled": False}
        return await self.controller.request("put", app_url, json=data)
