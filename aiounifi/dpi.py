"""DPI Restrictions as part of a UniFi network."""
import asyncio
from typing import List, Optional, Union

from .api import APIItem, APIItems

GROUP_URL = "/rest/dpigroup"  # List DPI Group configuration
APP_URL = "/rest/dpiapp"  # List DPI App configuration


class DPIRestrictionApp(APIItem):
    """Represents a DPI App configuration."""

    @property
    def id(self) -> str:
        """DPI app ID."""
        return self.raw["_id"]

    @property
    def apps(self) -> list:
        """List of apps."""
        return self.raw["apps"]

    @property
    def blocked(self) -> bool:
        """Is blocked."""
        return self.raw["blocked"]

    @property
    def cats(self) -> list:
        """Categories."""
        return self.raw["cats"]

    @property
    def enabled(self) -> bool:
        """Is enabled."""
        return self.raw["enabled"]

    @property
    def log(self) -> bool:
        """Is logging enabled."""
        return self.raw["log"]

    @property
    def site_id(self) -> str:
        """Site ID."""
        return self.raw["site_id"]


class DPIRestrictionApps(APIItems):
    """Represents DPI App configurations."""

    KEY = "_id"

    def __init__(self, raw: list, request) -> None:
        """Initialize DPI restriction apps manager."""
        super().__init__(raw, request, APP_URL, DPIRestrictionApp)

    async def async_enable(self, app_id: str) -> None:
        """Enable DPI Restriction Group Apps."""
        app_url = f"{APP_URL}/{app_id}"
        data = {"enabled": True}
        await self._request("put", app_url, json=data)

    async def async_disable(self, app_id: str) -> None:
        """Disable DPI Restriction Group Apps."""
        app_url = f"{APP_URL}/{app_id}"
        data = {"enabled": False}
        await self._request("put", app_url, json=data)


class DPIRestrictionGroup(APIItem):
    """Represents a DPI Group configuration."""

    def __init__(self, raw: dict, request) -> None:
        """Initialize DPI Group."""
        super().__init__(raw, request)
        self.apps: Optional[DPIRestrictionApps] = None

    @property
    def id(self) -> str:
        """DPI group ID."""
        return self.raw["_id"]

    @property
    def attr_no_delete(self) -> bool:
        """Can be deleted."""
        return self.raw.get("attr_no_delete", False)

    @property
    def attr_hidden_id(self) -> str:
        """Attr hidden ID."""
        return self.raw.get("attr_hidden_id", "")

    @property
    def name(self) -> str:
        """DPI group name."""
        return self.raw["name"]

    @property
    def site_id(self) -> str:
        """Site ID."""
        return self.raw["site_id"]

    @property
    def dpiapp_ids(self) -> List[str]:
        """DPI app IDs belonging to group."""
        return self.raw.get("dpiapp_ids", [])

    @property
    def enabled(self) -> Union[DPIRestrictionApps, None, bool]:
        """Are all apps in group enabled."""
        return self.apps and all(
            [self.apps[id].enabled for id in self.apps if id in self.dpiapp_ids]  # type: ignore
        )


class DPIRestrictionGroups(APIItems):
    """Represents DPI Group configurations."""

    KEY = "_id"

    def __init__(self, raw: list, request, apps: DPIRestrictionApps) -> None:
        """Initialize DPI restriction group manager."""
        self._apps = apps
        super().__init__(raw, request, GROUP_URL, DPIRestrictionGroup)

    async def async_enable(self, dpi: DPIRestrictionGroup) -> None:
        """Enable DPI Restriction Group Apps."""
        await asyncio.gather(
            *[self._apps.async_enable(app_id) for app_id in dpi.dpiapp_ids]
        )

    async def async_disable(self, dpi: DPIRestrictionGroup) -> None:
        """Disable DPI Restriction Group Apps."""
        await asyncio.gather(
            *[self._apps.async_disable(app_id) for app_id in dpi.dpiapp_ids]
        )

    def process_raw(self, raw: list) -> set:
        """Set enabled attribute based on app data."""
        new_items = super().process_raw(raw)

        for item_key in new_items:
            item = self._items[item_key]
            item.apps = self._apps

        return new_items
