"""Client information interface for UniFi Network API."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..models.client import (
    Client,
    ClientData,
    ExecuteClientActionRequest,
    ExecuteClientActionResponse,
    GetClientDetailsRequest,
    ListClientsRequest,
)

if TYPE_CHECKING:
    from ..client import Client as ApiClient

ClientList = list[Client]


class Clients:
    """Read and manage client information from the Network API."""

    def __init__(self, client: ApiClient) -> None:
        """Initialize clients interface."""
        self.client = client

    async def list(
        self,
        site_id: str,
        filter_value: str | None = None,
    ) -> ClientList:
        """List connected clients on a site using the default first-page request.

        Args:
            site_id: The site ID to list clients for
            filter_value: Optional filter expression (e.g., "access.type.eq('GUEST')")

        Returns:
            List of connected clients

        """
        return await self.list_page(site_id, filter_value=filter_value)

    async def list_page(
        self,
        site_id: str,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> ClientList:
        """List one page of connected clients.

        Args:
            site_id: The site ID to list clients for
            offset: Pagination offset (default: 0)
            limit: Number of results per page, 0-200 (default: 25)
            filter_value: Optional filter expression

        Returns:
            List of clients for the requested page

        """
        request = ListClientsRequest.create(site_id, offset, limit, filter_value)
        data = await self.client.request(request)
        return [Client(cast(ClientData, item)) for item in data.get("data", [])]

    async def get_details(
        self,
        site_id: str,
        client_id: str,
    ) -> Client:
        """Get detailed information about a specific connected client.

        Args:
            site_id: The site ID
            client_id: The client ID (UUID)

        Returns:
            Client with full details

        """
        request = GetClientDetailsRequest.create(site_id, client_id)
        data = await self.client.request(request)
        client_data = cast(ClientData, data.get("data", [{}])[0])
        return Client(client_data)

    async def authorize_guest_access(
        self,
        site_id: str,
        client_id: str,
        time_limit_minutes: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> ExecuteClientActionResponse:
        """Authorize guest access for a client.

        Args:
            site_id: The site ID
            client_id: The client ID (UUID)
            time_limit_minutes: Guest access time limit in minutes (1-1000000).
                If not specified, the default limit from site settings is used.
            data_usage_limit_mbytes: Data usage limit in megabytes (1-1048576).
                Optional.
            rx_rate_limit_kbps: Download rate limit in kilobits per second (2-100000).
                Optional.
            tx_rate_limit_kbps: Upload rate limit in kilobits per second (2-100000).
                Optional.

        Returns:
            Response containing granted authorization details and any revoked
            authorization details if the guest was already authorized

        """
        request = ExecuteClientActionRequest.create_authorize_guest_access(
            site_id,
            client_id,
            time_limit_minutes,
            data_usage_limit_mbytes,
            rx_rate_limit_kbps,
            tx_rate_limit_kbps,
        )
        data = await self.client.request(request)
        # For action endpoints, the response structure is different
        # We need to extract the response from the endpoint directly
        response = data.get("data", [{}])[0]
        return cast(ExecuteClientActionResponse, response)
