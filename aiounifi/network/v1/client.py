"""UniFi Network API client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...models.configuration import Configuration
from .connectivity import Connectivity
from .interfaces.clients import Clients
from .interfaces.sites import Sites

if TYPE_CHECKING:
    from .models.api import ApiRequest, ApiResponse


class Client:
    """Client for the UniFi Network API."""

    def __init__(self, config: Configuration) -> None:
        """Initialize Network API client interfaces."""
        self.connectivity = Connectivity(config)
        self.clients = Clients(self)
        self.sites = Sites(self)

    async def request(self, api_request: ApiRequest) -> ApiResponse:
        """Perform a typed Network API request."""
        return await self.connectivity.request(api_request)
