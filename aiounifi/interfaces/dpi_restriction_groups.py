"""DPI Restrictions as part of a UniFi network."""

from typing import Final

from ..models.dpi_restriction_group import DPIRestrictionGroup
from .api import APIItems

GROUP_URL: Final = "/rest/dpigroup"  # List DPI Group configuration


class DPIRestrictionGroups(APIItems):
    """Represents DPI Group configurations."""

    KEY = "_id"
    path = GROUP_URL
    item_cls = DPIRestrictionGroup
