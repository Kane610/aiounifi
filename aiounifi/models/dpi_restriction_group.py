"""DPI Restrictions as part of a UniFi network."""

from .api import APIItem


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
    def dpiapp_ids(self) -> list[str]:
        """DPI app IDs belonging to group."""
        return self.raw.get("dpiapp_ids", [])
