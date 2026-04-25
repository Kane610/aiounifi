"""Client information interface for UniFi Network API."""

from __future__ import annotations

from typing import cast

from ....errors import RequestError
from ..api_handlers import APIHandler
from ..models.client import (
    Client,
    ClientDetailData,
    ExecuteClientActionRequest,
    ExecuteClientActionResponse,
    GetClientDetailsRequest,
    ListClientsRequest,
    normalize_mac,
)

ClientList = list[Client]


class Clients(APIHandler[Client]):
    """Read and manage client information from the Network API."""

    item_cls = Client
    obj_id_key = "macAddress"

    @property
    def api_request(self) -> ListClientsRequest:
        """Return the default clients list request for the configured site."""
        return ListClientsRequest.create(self.api_client.site_id)

    async def list(
        self,
        filter_value: str | None = None,
    ) -> ClientList:
        """List connected clients on a site using the default first-page request.

        Args:
            filter_value: Optional filter expression (e.g., "access.type.eq('GUEST')")

        Returns:
            List of connected clients

        """
        return await self.list_page(filter_value=filter_value)

    async def list_page(
        self,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> ClientList:
        """List one page of connected clients.

        Args:
            offset: Pagination offset (default: 0)
            limit: Number of results per page, 0-200 (default: 25)
            filter_value: Optional filter expression

        Returns:
            List of clients for the requested page

        """
        request = ListClientsRequest.create(
            self.api_client.site_id, offset, limit, filter_value
        )
        data = await self.api_client.request(request)
        return [Client(cast(ClientDetailData, item)) for item in data.get("data", [])]

    async def get_details(
        self,
        client_id: str,
    ) -> Client:
        """Get detailed information about a specific connected client.

        Args:
            client_id: The client ID (UUID)

        Returns:
            Client with full details

        """
        request = GetClientDetailsRequest.create(self.api_client.site_id, client_id)
        data = await self.api_client.request(request)
        client_data = cast(ClientDetailData, data.get("data", [{}])[0])
        return Client(client_data)

    async def authorize_guest_access(
        self,
        client_id: str,
        time_limit_minutes: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> ExecuteClientActionResponse:
        """Authorize guest access for a client.

        Args:
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
            self.api_client.site_id,
            client_id,
            time_limit_minutes,
            data_usage_limit_mbytes,
            rx_rate_limit_kbps,
            tx_rate_limit_kbps,
        )
        data = await self.api_client.request(request)
        # For action endpoints, the response structure is different
        # We need to extract the response from the endpoint directly
        response = data.get("data", [{}])[0]
        return cast(ExecuteClientActionResponse, response)

    async def get_by_mac(self, mac_address: str) -> Client | None:
        """Get a client by MAC address using server-side filtering."""
        normalized_mac = normalize_mac(mac_address)
        filter_value = f"macAddress.eq('{normalized_mac}')"
        clients = await self.list_page(limit=1, filter_value=filter_value)
        return clients[0] if clients else None

    async def require_by_mac(self, mac_address: str) -> Client:
        """Get a client by MAC address or raise RequestError if not found."""
        client = await self.get_by_mac(mac_address)
        if client is None:
            raise RequestError(f"Could not find client for mac_address={mac_address!r}")
        return client

    def get_by_mac_cached(self, mac_address: str) -> Client | None:
        """Get a client by MAC from already-loaded handler state without I/O."""
        normalized_mac = normalize_mac(mac_address)
        return self.get(normalized_mac)

    def get_by_uuid(self, client_id: str) -> Client | None:
        """Get a client by UUID from already-loaded handler state without I/O."""
        return next(
            (client for client in self.values() if client.client_id == client_id), None
        )

    def require_by_uuid(self, client_id: str) -> Client:
        """Get a client by UUID from handler state or raise RequestError."""
        client = self.get_by_uuid(client_id)
        if client is None:
            raise RequestError(f"Could not find client for client_id={client_id!r}")
        return client

    async def get_details_by_mac(self, mac_address: str) -> Client:
        """Get detailed client information by MAC address."""
        client = await self.require_by_mac(mac_address)
        return await self.get_details(client.client_id)

    async def authorize_guest_access_by_mac(
        self,
        mac_address: str,
        time_limit_minutes: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> ExecuteClientActionResponse:
        """Authorize guest access for a client resolved by MAC address."""
        client = await self.require_by_mac(mac_address)
        return await self.authorize_guest_access(
            client.client_id,
            time_limit_minutes,
            data_usage_limit_mbytes,
            rx_rate_limit_kbps,
            tx_rate_limit_kbps,
        )
