"""Official UniFi API client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.configuration import Configuration
from .connectivity import OfficialConnectivity
from .interfaces.sites import Sites

if TYPE_CHECKING:
    from .models.api import OfficialApiRequest, OfficialApiResponse


class OfficialClient:
    """Client for the official UniFi API."""

    def __init__(self, config: Configuration) -> None:
        """Initialize official API client interfaces."""
        self.connectivity = OfficialConnectivity(config)
        self.sites = Sites(self)

    async def request(self, api_request: OfficialApiRequest) -> OfficialApiResponse:
        """Perform a typed official API request."""
        return await self.connectivity.request(api_request)
