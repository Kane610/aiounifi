"""Entry point of the Network API v1."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ...errors import RequestError
from .connectivity import Connectivity
from .interfaces.clients import Clients
from .interfaces.devices import Devices
from .interfaces.sites import Sites
from .models.info import InfoData, InfoRequest

if TYPE_CHECKING:
    from ...models.configuration import Configuration
    from .models.api import ApiRequest, ApiResponse


class ApiClient:
    """Client of the Network API v1.

    Needs `Configuration.api_key` and nothing else from the legacy login.
    Site-scoped interfaces need `assign_site` to have run once, because the
    v1 API addresses sites by UUID while the legacy API, and callers used
    to it, use the short site name.
    """

    def __init__(self, config: Configuration) -> None:
        """Initialize."""
        self.config = config
        self.connectivity = Connectivity(config)
        self._site_id: str | None = None
        self.sites = Sites(self)
        self.devices = Devices(self)
        self.clients = Clients(self)

    @property
    def site_id(self) -> str:
        """UUID of the active site."""
        if self._site_id is None:
            raise RequestError("No site assigned, call assign_site first")
        return self._site_id

    async def request(self, api_request: ApiRequest) -> ApiResponse:
        """Send a request."""
        return await self.connectivity.request(api_request)

    async def get_info(self) -> InfoData:
        """Return the Network application version.

        Also the cheapest way to check an API key.
        """
        response = await self.request(InfoRequest.create())
        return cast("InfoData", response["data"][0])

    async def assign_site(self, site: str | None = None) -> str:
        """Resolve a site token to its UUID and make that the active site.

        The token may be the UUID itself, the short name (`default`) or the
        display name. Defaults to `Configuration.site`.
        """
        token = (site if site is not None else self.config.site).strip()
        await self.sites.update()
        for candidate in self.sites.values():
            if token in (candidate.site_id, candidate.internal_reference):
                self._site_id = candidate.site_id
                return self._site_id
        for candidate in self.sites.values():
            if token == candidate.name:
                self._site_id = candidate.site_id
                return self._site_id
        raise RequestError(f"No Network API site matches {token!r}")
