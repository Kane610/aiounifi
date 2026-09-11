"""UniFi Network Integration API client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .connectivity import Connectivity
from .interfaces.sites import Sites
from .models.info import ApplicationInfo, InfoRequest

if TYPE_CHECKING:
    from ...controller import Controller
    from .models.api import ApiRequest, ApiResponse


class ApiClient:
    """Client for the official UniFi Network Integration API."""

    def __init__(self, controller: Controller) -> None:
        """Initialize Integration API client interfaces."""
        self.controller = controller
        self.connectivity = Connectivity(controller.connectivity.config)
        self.sites = Sites(self)

    async def get_info(self) -> ApplicationInfo:
        """Return Integration API application info."""
        response = await self.request(InfoRequest.create())
        return ApplicationInfo.from_response(response)

    async def request(self, api_request: ApiRequest) -> ApiResponse:
        """Perform a typed Integration API request."""
        return await self.connectivity.request(api_request)
