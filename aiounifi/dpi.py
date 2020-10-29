"""DPI Restrictions as part of a UniFi network."""
import asyncio
from typing import List, Optional

from .api import APIItem, APIItems

GROUP_URL = "/rest/dpigroup"  # List DPI Group configuration
APP_URL = "/rest/dpiapp"  # List DPI App configuration


class DPIItems(APIItems):
    """Custom process method for DPI."""

    def process_raw(self, raw: list) -> set:
        """Set enabled attribute based on app data."""
        new_items = set()

        for raw_item in raw:
            key = raw_item[self.KEY]
            obj = self._items.get(key)

            if obj is not None:
                obj.update(raw=raw_item)
            else:
                new_item = self._item_cls(raw_item, self._request)
                if self._item_cls == DPIRestrictionGroup:
                    new_item.apps = self._apps
                self._items[key] = new_item

            new_items.add(key)

        return new_items


class DPIRestrictionApp(APIItem):
    """Represents a DPI App configuration."""

    @property
    def id(self) -> str:
        return self.raw["_id"]

    @property
    def apps(self) -> list:
        return self.raw["apps"]

    @property
    def blocked(self) -> bool:
        return self.raw["blocked"]

    @property
    def cats(self) -> list:
        return self.raw["cats"]

    @property
    def enabled(self) -> bool:
        return self.raw["enabled"]

    @property
    def log(self) -> bool:
        return self.raw["log"]

    @property
    def site_id(self) -> str:
        return self.raw["site_id"]


class DPIRestrictionApps(DPIItems):
    """Represents DPI App configurations."""

    KEY = "_id"

    def __init__(self, raw: list, request) -> None:
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

    def __init__(
        self, raw: dict, request, apps: Optional[DPIRestrictionApps] = None
    ) -> None:
        """Initialize DPI Group."""
        super().__init__(raw, request)
        self.apps = apps

    @property
    def id(self) -> str:
        return self.raw["_id"]

    @property
    def attr_no_delete(self) -> bool:
        return self.raw.get("attr_no_delete", False)

    @property
    def attr_hidden_id(self) -> str:
        return self.raw.get("attr_hidden_id", "")

    @property
    def name(self) -> str:
        return self.raw["name"]

    @property
    def site_id(self) -> str:
        return self.raw["site_id"]

    @property
    def dpiapp_ids(self) -> List[str]:
        return self.raw.get("dpiapp_ids", [])

    @property
    def enabled(self) -> bool:
        return self.apps and all(
            [self.apps[id].enabled for id in self.apps if id in self.dpiapp_ids]
        )


class DPIRestrictionGroups(DPIItems):
    """Represents DPI Group configurations."""

    KEY = "_id"

    def __init__(self, raw: list, request, apps: DPIRestrictionApps) -> None:
        self._apps = apps
        super().__init__(raw, request, GROUP_URL, DPIRestrictionGroup)

    async def async_enable(self, dpi: DPIRestrictionGroup) -> None:
        """Enable DPI Restriction Group Apps."""
        calls = []
        for app_id in dpi.dpiapp_ids:
            calls.append(self._apps.async_enable(app_id))
        await asyncio.gather(*calls)

    async def async_disable(self, dpi: DPIRestrictionGroup) -> None:
        """Disable DPI Restriction Group Apps."""
        calls = []
        for app_id in dpi.dpiapp_ids:
            calls.append(self._apps.async_disable(app_id))
        await asyncio.gather(*calls)
