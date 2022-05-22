"""DPI Restrictions as part of a UniFi network."""

from collections.abc import Awaitable, Callable
from typing import Final

from .api import APIItems
from .models.dpi_restriction_app import DPIRestrictionApp
from .models.dpi_restriction_group import DPIRestrictionGroup

GROUP_URL: Final = "/rest/dpigroup"  # List DPI Group configuration
APP_URL: Final = "/rest/dpiapp"  # List DPI App configuration


class DPIRestrictionApps(APIItems):
    """Represents DPI App configurations."""

    KEY = "_id"

    def __init__(
        self,
        raw: list[dict],
        request: Callable[..., Awaitable[list[dict]]],
    ) -> None:
        """Initialize DPI restriction apps manager."""
        super().__init__(raw, request, APP_URL, DPIRestrictionApp)

    async def enable(self, app_id: str) -> list[dict]:
        """Enable DPI Restriction Group Apps."""
        app_url = f"{APP_URL}/{app_id}"
        data = {"enabled": True}
        return await self._request("put", app_url, json=data)

    async def disable(self, app_id: str) -> list[dict]:
        """Disable DPI Restriction Group Apps."""
        app_url = f"{APP_URL}/{app_id}"
        data = {"enabled": False}
        return await self._request("put", app_url, json=data)


class DPIRestrictionGroups(APIItems):
    """Represents DPI Group configurations."""

    KEY = "_id"

    def __init__(
        self,
        raw: list,
        request: Callable[..., Awaitable[list[dict]]],
    ) -> None:
        """Initialize DPI restriction group manager."""
        super().__init__(raw, request, GROUP_URL, DPIRestrictionGroup)
