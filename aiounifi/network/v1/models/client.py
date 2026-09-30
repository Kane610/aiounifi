"""Connected clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired, TypedDict

from ....models.api import ApiItem
from .api import DEFAULT_PAGE_LIMIT, DEFAULT_PAGE_OFFSET, ApiRequest, page_params


def normalize_mac(mac_address: str) -> str:
    """Return a MAC address as lower case, colon separated.

    Accepts `aa:bb:cc:dd:ee:ff`, `aa-bb-cc-dd-ee-ff` and `aabbccddeeff`.
    """
    cleaned = mac_address.strip().lower().replace("-", "").replace(":", "")
    if len(cleaned) != 12:
        raise ValueError(f"Invalid MAC address {mac_address!r}")
    try:
        bytes.fromhex(cleaned)
    except ValueError as err:
        raise ValueError(f"Invalid MAC address {mac_address!r}") from err
    return ":".join(cleaned[idx : idx + 2] for idx in range(0, 12, 2))


class ClientAccess(TypedDict):
    """How the client was admitted to the network."""

    type: str


class GuestAuthorization(TypedDict):
    """Details of a guest authorization."""

    authorizedAt: str
    authorizationMethod: str
    expiresAt: NotRequired[str]
    dataUsageLimitMBytes: NotRequired[int]
    rxRateLimitKbps: NotRequired[int]
    txRateLimitKbps: NotRequired[int]
    usage: NotRequired[dict[str, int]]


class ClientData(TypedDict):
    """One client, as returned by both the list and the detail endpoint.

    `macAddress` and `uplinkDeviceId` exist for `WIRED` and `WIRELESS`
    clients only; `VPN` and `TELEPORT` clients have neither.
    """

    type: str
    id: str
    name: str
    macAddress: NotRequired[str]
    connectedAt: NotRequired[str]
    ipAddress: NotRequired[str]
    access: ClientAccess
    uplinkDeviceId: NotRequired[str]


class ClientActionResponse(TypedDict):
    """Response to a client action."""

    action: str
    grantedAuthorization: NotRequired[GuestAuthorization]
    revokedAuthorization: NotRequired[GuestAuthorization]


@dataclass
class ListClientsRequest(ApiRequest):
    """List the clients connected to a site."""

    @classmethod
    def create(
        cls,
        site_id: str,
        offset: int = DEFAULT_PAGE_OFFSET,
        limit: int = DEFAULT_PAGE_LIMIT,
        filter_value: str | None = None,
    ) -> ListClientsRequest:
        """Create a request for one page of clients."""
        return cls(
            method="get",
            path=f"/v1/sites/{site_id}/clients",
            params=page_params(offset, limit, filter_value),
        )


@dataclass
class GetClientRequest(ApiRequest):
    """Get one client."""

    @classmethod
    def create(cls, site_id: str, client_id: str) -> GetClientRequest:
        """Create the request."""
        return cls(method="get", path=f"/v1/sites/{site_id}/clients/{client_id}")


@dataclass
class ClientActionRequest(ApiRequest):
    """Run an action on a client."""

    @classmethod
    def create_authorize_guest_access(
        cls,
        site_id: str,
        client_id: str,
        time_limit_minutes: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> ClientActionRequest:
        """Authorize a guest client, with optional limits."""
        data: dict[str, int | str] = {"action": "AUTHORIZE_GUEST_ACCESS"}
        if time_limit_minutes is not None:
            data["timeLimitMinutes"] = time_limit_minutes
        if data_usage_limit_mbytes is not None:
            data["dataUsageLimitMBytes"] = data_usage_limit_mbytes
        if rx_rate_limit_kbps is not None:
            data["rxRateLimitKbps"] = rx_rate_limit_kbps
        if tx_rate_limit_kbps is not None:
            data["txRateLimitKbps"] = tx_rate_limit_kbps
        return cls(
            method="post",
            path=f"/v1/sites/{site_id}/clients/{client_id}/actions",
            data=data,
        )

    @classmethod
    def create_unauthorize_guest_access(
        cls, site_id: str, client_id: str
    ) -> ClientActionRequest:
        """Revoke a guest client's authorization."""
        return cls(
            method="post",
            path=f"/v1/sites/{site_id}/clients/{client_id}/actions",
            data={"action": "UNAUTHORIZE_GUEST_ACCESS"},
        )


class Client(ApiItem):
    """A connected client."""

    raw: ClientData

    @property
    def client_id(self) -> str:
        """UUID used in client-scoped paths."""
        return self.raw["id"]

    @property
    def name(self) -> str:
        """Display name."""
        return self.raw["name"]

    @property
    def type(self) -> str:
        """`WIRED`, `WIRELESS`, `VPN` or `TELEPORT`."""
        return self.raw["type"]

    @property
    def mac_address(self) -> str | None:
        """MAC address; `None` for VPN and Teleport clients."""
        return self.raw.get("macAddress")

    @property
    def ip_address(self) -> str | None:
        """IP address, when the console knows one."""
        return self.raw.get("ipAddress")

    @property
    def connected_at(self) -> str | None:
        """When the client connected, ISO 8601."""
        return self.raw.get("connectedAt")

    @property
    def access_type(self) -> str:
        """`DEFAULT` or `GUEST`."""
        return self.raw["access"]["type"]

    @property
    def uplink_device_id(self) -> str | None:
        """UUID of the device the client is connected through."""
        return self.raw.get("uplinkDeviceId")
