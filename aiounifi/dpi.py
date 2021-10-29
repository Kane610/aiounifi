"""DPI Restrictions as part of a UniFi network."""

from typing import Awaitable, Callable, Final, List

from .api import APIItem, APIItems

GROUP_URL: Final = "/rest/dpigroup"  # List DPI Group configuration
APP_URL: Final = "/rest/dpiapp"  # List DPI App configuration


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

    def __init__(
        self,
        raw: List[dict],
        request: Callable[..., Awaitable[List[dict]]],
    ) -> None:
        """Initialize DPI restriction apps manager."""
        super().__init__(raw, request, APP_URL, DPIRestrictionApp)

    async def async_enable(self, app_id: str) -> List[dict]:
        """Enable DPI Restriction Group Apps."""
        app_url = f"{APP_URL}/{app_id}"
        data = {"enabled": True}
        return await self._request("put", app_url, json=data)

    async def async_disable(self, app_id: str) -> List[dict]:
        """Disable DPI Restriction Group Apps."""
        app_url = f"{APP_URL}/{app_id}"
        data = {"enabled": False}
        return await self._request("put", app_url, json=data)


class DPIRestrictionGroup(APIItem):
    """Represents a DPI Group configuration."""

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


class DPIRestrictionGroups(APIItems):
    """Represents DPI Group configurations."""

    KEY = "_id"

    def __init__(
        self,
        raw: list,
        request: Callable[..., Awaitable[List[dict]]],
    ) -> None:
        """Initialize DPI restriction group manager."""
        super().__init__(raw, request, GROUP_URL, DPIRestrictionGroup)
