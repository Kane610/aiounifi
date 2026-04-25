"""UniFi Network API client."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ...errors import RequestError
from .connectivity import Connectivity
from .interfaces.clients import Clients
from .interfaces.sites import Sites

if TYPE_CHECKING:
    from ...controller import Controller
    from .models.api import ApiRequest, ApiResponse


class ApiClient:
    """Client for the UniFi Network API."""

    def __init__(self, controller: Controller) -> None:
        """Initialize Network API client interfaces."""
        config = controller.connectivity.config
        self.connectivity = Connectivity(config)
        self.controller = controller
        configured_site_id = config.site_uuid
        self._site_id: str | None = configured_site_id or None
        self._site_task: asyncio.Task[str] | None = None
        self.clients = Clients(self)
        self.sites = Sites(self)

    @property
    def site_id(self) -> str:
        """Return active Network API site UUID."""
        if self._site_id is None:
            raise RequestError(
                "ApiClient.site_id is not set. Resolve and assign a site UUID first."
            )
        return self._site_id

    async def assign_site(self, site: str) -> str:
        """Resolve and assign active Network API site UUID from a site token.

        Concurrent calls are safe without a lock: asyncio's single-threaded
        cooperative model ensures the ``_site_task`` check and ``create_task``
        assignment are atomic between awaits, so all concurrent callers share
        a single in-flight resolution and avoid duplicate network fetches.

        Resolution order:
        1. Already-resolved ``_site_id`` (fast path).
        2. In-flight resolution task (piggyback).
        3. Configured network-site UUID.
        4. Legacy/primary site resolver.
        5. Already-fetched v1 sites cache.
        6. Fresh v1 sites fetch.
        """
        if self._site_id is not None:
            return self._site_id

        if self._site_task is not None:
            await self._site_task
            return self._site_id  # type: ignore[return-value]

        self._site_task = asyncio.get_event_loop().create_task(self._resolve_site(site))
        await self._site_task
        return self._site_id  # type: ignore[return-value]

    async def _resolve_site(self, site: str) -> str:
        """Perform the four-step site UUID resolution and store the result."""
        if configured_site_id := self.controller.connectivity.config.site_uuid:
            self._site_id = configured_site_id
            return configured_site_id

        if site_uuid := self.controller.sites.resolve_site_uuid(site):
            self._site_id = site_uuid
            return site_uuid

        if site_uuid := self.sites.resolve_site_uuid(site):
            self._site_id = site_uuid
            return site_uuid

        network_sites = await self.sites.list()
        if site_uuid := self.sites.resolve_site_uuid(site, network_sites):
            self._site_id = site_uuid
            return site_uuid

        raise RequestError(f"Could not resolve Network API site UUID for site={site!r}")

    async def request(self, api_request: ApiRequest) -> ApiResponse:
        """Perform a typed Network API request."""
        return await self.connectivity.request(api_request)
