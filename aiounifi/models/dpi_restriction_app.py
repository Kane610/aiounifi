"""DPI Restrictions as part of a UniFi network."""

from .api import APIItem


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
