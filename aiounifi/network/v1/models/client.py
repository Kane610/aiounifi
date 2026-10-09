"""Connected clients."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import logging
from typing import NotRequired, TypedDict, TypeIs

from ....models.api import ApiItem
from .api import DEFAULT_PAGE_LIMIT, DEFAULT_PAGE_OFFSET, ApiRequest, page_params

LOGGER = logging.getLogger(__name__)


class ClientAccessType(StrEnum):
    """How a client was admitted to the network."""

    DEFAULT = "DEFAULT"
    GUEST = "GUEST"

    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> ClientAccessType:
        """Set default enum member if an unknown value is provided."""
        LOGGER.warning("Unsupported client access type %s, using UNKNOWN", value)
        return cls.UNKNOWN


class ClientType(StrEnum):
    """How a client is connected."""

    WIRED = "WIRED"
    WIRELESS = "WIRELESS"
    VPN = "VPN"
    TELEPORT = "TELEPORT"

    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> ClientType:
        """Set default enum member if an unknown value is provided."""
        LOGGER.warning("Unsupported client type %s, using UNKNOWN", value)
        return cls.UNKNOWN


class ClientAccess(TypedDict):
    """Access block of a client. `type` is a `ClientAccessType`."""

    type: str


class ClientActionResponse(TypedDict):
    """Response to a client action."""

    action: str
    grantedAuthorization: NotRequired[ClientGuestAuthorization]
    revokedAuthorization: NotRequired[ClientGuestAuthorization]


class ClientData(TypedDict):
    """One client, as returned by both the list and the detail endpoint.

    `type` is a `ClientType`. `macAddress` and `uplinkDeviceId` exist for
    `WIRED` and `WIRELESS` clients only; `VPN` and `TELEPORT` clients have
    neither.
    """

    access: ClientAccess
    connectedAt: NotRequired[str]
    id: str
    ipAddress: NotRequired[str]
    macAddress: NotRequired[str]
    name: str
    type: str
    uplinkDeviceId: NotRequired[str]


class ClientGuestAuthorization(TypedDict):
    """Details of a guest authorization."""

    authorizationMethod: str
    authorizedAt: str
    dataUsageLimitMBytes: NotRequired[int]
    expiresAt: NotRequired[str]
    rxRateLimitKbps: NotRequired[int]
    txRateLimitKbps: NotRequired[int]
    usage: NotRequired[dict[str, int]]


def is_client_action_response(decoded: object) -> TypeIs[ClientActionResponse]:
    """Whether a decoded body is the response to a client action."""
    return isinstance(decoded, dict) and isinstance(decoded.get("action"), str)


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
    def type(self) -> ClientType:
        """How the client is connected."""
        return ClientType(self.raw["type"])

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
    def access_type(self) -> ClientAccessType:
        """How the client was admitted to the network."""
        return ClientAccessType(self.raw["access"]["type"])

    @property
    def uplink_device_id(self) -> str | None:
        """UUID of the device the client is connected through."""
        return self.raw.get("uplinkDeviceId")
