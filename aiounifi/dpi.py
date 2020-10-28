"""DPI Restrictions as part of a UniFi network."""
from typing import List

from .api import APIItem, APIItems

GROUP_URL = "/rest/dpigroup"  # List DPI Group configuration
APP_URL = "/rest/dpiapp"  # List DPI App configuration


class DPIRestrictionGroup(APIItem):
    """Represents a DPI App configuration."""

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
        return self.raw["enabled"]


class DPIRestrictionGroups(APIItems):
    """Represents DPI Group configurations."""

    KEY = "name"

    def __init__(self, raw: dict, request) -> None:
        super().__init__(raw, request, GROUP_URL, DPIRestrictionGroup)

    async def update(self) -> None:
        raw_apps = await self._request("get", APP_URL)
        raw_groups = await self._request("get", GROUP_URL)
        for item in raw_groups:
            item["enabled"] = all(
                [
                    app["enabled"]
                    for app in raw_apps
                    if app["_id"] in item.get("dpiapp_ids", [])
                ]
            )

        self.process_raw(raw_groups)

    async def async_enable(self, dpi: DPIRestrictionGroup) -> None:
        """Enable DPI Restriction Group Apps."""
        for app_id in dpi.dpiapp_ids:
            app_url = f"{APP_URL}/{app_id}"
            data = {"enabled": True}
            await self._request("put", app_url, json=data)

    async def async_disable(self, dpi: DPIRestrictionGroup) -> None:
        """Disable DPI Restriction Group Apps."""
        for app_id in dpi.dpiapp_ids:
            app_url = f"{APP_URL}/{app_id}"
            data = {"enabled": False}
            await self._request("put", app_url, json=data)
