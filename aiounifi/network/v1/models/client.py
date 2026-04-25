"""Client models for UniFi Network API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired, TypedDict

from ....models.api import ApiItem
from .api import ApiRequest


class Usage(TypedDict):
    """Usage information for guest authorization."""


class GuestAuthorizationDetails(TypedDict):
    """Guest authorization details type definition."""

    authorizedAt: str
    authorizationMethod: str
    expiresAt: str
    dataUsageLimitMBytes: int
    rxRateLimitKbps: int
    txRateLimitKbps: int
    usage: Usage


class Access(TypedDict):
    """Access information for a client."""

    type: str


class ClientDetailData(TypedDict):
    """Typed payload for a client returned by single-item detail endpoint."""

    type: str
    id: str
    name: str
    connectedAt: NotRequired[str]
    ipAddress: NotRequired[str]
    access: Access
    macAddress: str
    uplinkDeviceId: str


class ClientSummaryData(TypedDict):
    """Typed payload for a client entry in the list-all response."""

    type: str
    id: str
    name: str
    connectedAt: NotRequired[str]
    ipAddress: NotRequired[str]
    access: Access
    macAddress: str
    uplinkDeviceId: str


class ExecuteClientActionResponse(TypedDict):
    """Response for execute client action request."""

    action: str
    revokedAuthorization: NotRequired[GuestAuthorizationDetails]
    grantedAuthorization: GuestAuthorizationDetails


@dataclass
class ListClientsRequest(ApiRequest):
    """Request for listing connected clients from the network API."""

    @classmethod
    def create(
        cls,
        site_id: str,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> ListClientsRequest:
        """Construct a request for one clients page.

        Args:
            site_id: The site ID to list clients for
            offset: Pagination offset (default: 0)
            limit: Number of results per page, 0-200 (default: 25)
            filter_value: Optional filter expression

        Returns:
            ListClientsRequest configured with the provided parameters

        """
        params: dict[str, str | int] = {
            "offset": max(offset, 0),
            "limit": max(min(limit, 200), 1),
        }
        if filter_value:
            params["filter"] = filter_value
        return cls(method="get", path=f"/v1/sites/{site_id}/clients", params=params)


@dataclass
class GetClientDetailsRequest(ApiRequest):
    """Request for getting detailed information about a specific client."""

    @classmethod
    def create(
        cls,
        site_id: str,
        client_id: str,
    ) -> GetClientDetailsRequest:
        """Construct a request for client details.

        Args:
            site_id: The site ID
            client_id: The client ID (UUID)

        Returns:
            GetClientDetailsRequest configured with the provided parameters

        """
        return cls(
            method="get",
            path=f"/v1/sites/{site_id}/clients/{client_id}",
        )


@dataclass
class ExecuteClientActionRequest(ApiRequest):
    """Request for executing an action on a client."""

    @classmethod
    def create_authorize_guest_access(
        cls,
        site_id: str,
        client_id: str,
        time_limit_minutes: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> ExecuteClientActionRequest:
        """Construct a request to authorize guest access for a client.

        Args:
            site_id: The site ID
            client_id: The client ID (UUID)
            time_limit_minutes: Guest access time limit in minutes (1-1000000).
                If not specified, default site setting is used.
            data_usage_limit_mbytes: Data usage limit in megabytes (1-1048576).
                Optional, if not specified no limit is applied.
            rx_rate_limit_kbps: Download rate limit in kilobits per second (2-100000).
                Optional, if not specified no limit is applied.
            tx_rate_limit_kbps: Upload rate limit in kilobits per second (2-100000).
                Optional, if not specified no limit is applied.

        Returns:
            ExecuteClientActionRequest configured to authorize guest access

        """
        request_data: dict[str, int | str] = {"action": "AUTHORIZE_GUEST_ACCESS"}

        if time_limit_minutes is not None:
            request_data["timeLimitMinutes"] = time_limit_minutes

        if data_usage_limit_mbytes is not None:
            request_data["dataUsageLimitMBytes"] = data_usage_limit_mbytes

        if rx_rate_limit_kbps is not None:
            request_data["rxRateLimitKbps"] = rx_rate_limit_kbps

        if tx_rate_limit_kbps is not None:
            request_data["txRateLimitKbps"] = tx_rate_limit_kbps

        return cls(
            method="post",
            path=f"/v1/sites/{site_id}/clients/{client_id}/actions",
            data=request_data,
        )


class Client(ApiItem):
    """Represent one client from network API data."""

    raw: ClientDetailData

    @property
    def client_id(self) -> str:
        """Client identifier used for further API calls."""
        return self.raw["id"]

    @property
    def name(self) -> str:
        """Display name of the client."""
        return self.raw["name"]

    @property
    def type(self) -> str:
        """Client type (e.g., WIRED, WIRELESS, VPN)."""
        return self.raw["type"]

    @property
    def mac_address(self) -> str:
        """MAC address of the client."""
        return self.raw["macAddress"]

    @property
    def ip_address(self) -> str | None:
        """IP address of the client, if available."""
        return self.raw.get("ipAddress")

    @property
    def connected_at(self) -> str | None:
        """ISO 8601 timestamp when client connected."""
        return self.raw.get("connectedAt")

    @property
    def access(self) -> Access:
        """Access type and authorization status."""
        return self.raw["access"]

    @property
    def access_type(self) -> str:
        """Access type (GUEST or DEFAULT)."""
        return self.raw["access"]["type"]

    @property
    def uplink_device_id(self) -> str:
        """ID of the device through which this client connects."""
        return self.raw["uplinkDeviceId"]
