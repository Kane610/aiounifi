"""DPI Restrictions as part of a UniFi network."""

from collections.abc import Awaitable, Callable
from typing import Final

from ..models.dpi_restriction_group import DPIRestrictionGroup
from .api import APIItems

GROUP_URL: Final = "/rest/dpigroup"  # List DPI Group configuration


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
