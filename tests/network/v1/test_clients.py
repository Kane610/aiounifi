"""Test Network API clients endpoint."""

import re

import pytest

from aiounifi.errors import RequestError, Unauthorized
from aiounifi.network.v1.models.client import normalize_mac

from .helpers import assert_request_called_with


def _client_payload(**overrides):
    """Build a default client payload for endpoint tests."""
    payload = {
        "type": "WIRED",
        "id": "client-uuid",
        "name": "Device",
        "access": {"type": "DEFAULT"},
        "macAddress": "aa:bb:cc:dd:ee:ff",
        "uplinkDeviceId": "device-uuid-1",
    }
    payload.update(overrides)
    return payload


def test_network_normalize_mac_colon_lowercase() -> None:
    """Verify normalize_mac keeps canonical lowercase colon format."""
    assert normalize_mac("aa:bb:cc:dd:ee:ff") == "aa:bb:cc:dd:ee:ff"


def test_network_normalize_mac_uppercase() -> None:
    """Verify normalize_mac lowercases uppercase colon format."""
    assert normalize_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"


def test_network_normalize_mac_dash_delimited() -> None:
    """Verify normalize_mac accepts dash-delimited input."""
    assert normalize_mac("AA-BB-CC-DD-EE-FF") == "aa:bb:cc:dd:ee:ff"


def test_network_normalize_mac_compact() -> None:
    """Verify normalize_mac accepts compact 12-hex input."""
    assert normalize_mac("AABBCCDDEEFF") == "aa:bb:cc:dd:ee:ff"


@pytest.mark.parametrize(
    "mac", ["", "aa:bb:cc:dd:ee", "zz:bb:cc:dd:ee:ff", "aabbccddeef"]
)
def test_network_normalize_mac_invalid(mac: str) -> None:
    """Verify normalize_mac rejects malformed MAC addresses."""
    with pytest.raises(ValueError, match="Invalid MAC address"):
        normalize_mac(mac)


async def test_network_clients_list_success(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify network clients list returns parsed client models."""
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 2,
            "count": 2,
            "totalCount": 10,
            "data": [
                {
                    "type": "WIRED",
                    "id": "client-1",
                    "name": "Desktop",
                    "connectedAt": "2024-01-15T10:30:00Z",
                    "ipAddress": "192.168.1.100",
                    "access": {"type": "DEFAULT"},
                    "macAddress": "aa:bb:cc:dd:ee:01",
                    "uplinkDeviceId": "device-uuid-1",
                },
                {
                    "type": "WIRELESS",
                    "id": "client-2",
                    "name": "Laptop",
                    "connectedAt": "2024-01-15T11:45:00Z",
                    "ipAddress": "192.168.1.101",
                    "access": {"type": "GUEST"},
                    "macAddress": "aa:bb:cc:dd:ee:02",
                    "uplinkDeviceId": "device-uuid-2",
                },
            ],
        },
    )

    clients = await network_client_with_site.clients.list_page(offset=0, limit=2)

    assert len(clients) == 2
    assert clients[0].client_id == "client-1"
    assert clients[0].name == "Desktop"
    assert clients[0].type == "WIRED"
    assert clients[0].mac_address == "aa:bb:cc:dd:ee:01"
    assert clients[0].ip_address == "192.168.1.100"
    assert clients[0].access_type == "DEFAULT"

    assert clients[1].client_id == "client-2"
    assert clients[1].name == "Laptop"
    assert clients[1].type == "WIRELESS"
    assert clients[1].access_type == "GUEST"
    assert_request_called_with(
        mock_aioresponse,
        "get",
        "/proxy/network/integration/v1/sites/site-uuid/clients",
        params={"offset": 0, "limit": 2},
    )


async def test_network_clients_list_default_pagination(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify clients list uses default pagination parameters."""
    site_id = "site-uuid"
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 25,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "type": "WIRED",
                    "id": "client-1",
                    "name": "Device",
                    "access": {"type": "DEFAULT"},
                    "macAddress": "aa:bb:cc:dd:ee:01",
                    "uplinkDeviceId": "device-uuid-1",
                }
            ],
        },
    )

    clients = await network_client_with_site.clients.list()

    assert len(clients) == 1
    assert_request_called_with(
        mock_aioresponse,
        "get",
        f"/proxy/network/integration/v1/sites/{site_id}/clients",
        params={"offset": 0, "limit": 25},
    )


async def test_network_clients_list_filter(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify filter parameter is accepted for clients list."""
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 25,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "type": "WIRED",
                    "id": "guest-1",
                    "name": "Guest Device",
                    "access": {"type": "GUEST"},
                    "macAddress": "aa:bb:cc:dd:ee:ff",
                    "uplinkDeviceId": "device-uuid-1",
                }
            ],
        },
    )

    clients = await network_client_with_site.clients.list(
        filter_value="access.type.eq('GUEST')"
    )

    assert len(clients) == 1
    assert clients[0].access_type == "GUEST"
    assert_request_called_with(
        mock_aioresponse,
        "get",
        "/proxy/network/integration/v1/sites/site-uuid/clients",
        params={"offset": 0, "limit": 25, "filter": "access.type.eq('GUEST')"},
    )


async def test_network_clients_get_details_success(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify get_details returns a single client with all information."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.get(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}",
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "type": "WIRELESS",
                    "id": "client-uuid",
                    "name": "Smartphone",
                    "connectedAt": "2024-01-15T14:20:00Z",
                    "ipAddress": "192.168.1.150",
                    "access": {"type": "DEFAULT"},
                    "macAddress": "bb:cc:dd:ee:ff:00",
                    "uplinkDeviceId": "ap-uuid-1",
                }
            ],
        },
    )

    client = await network_client_with_site.clients.get_details(client_id)

    assert client.client_id == "client-uuid"
    assert client.name == "Smartphone"
    assert client.type == "WIRELESS"
    assert client.mac_address == "bb:cc:dd:ee:ff:00"
    assert client.ip_address == "192.168.1.150"
    assert client.connected_at == "2024-01-15T14:20:00Z"
    assert client.uplink_device_id == "ap-uuid-1"


async def test_network_clients_authorize_guest_access_minimal(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify authorize_guest_access with minimal parameters."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.post(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}/actions",
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "action": "AUTHORIZE_GUEST_ACCESS",
                    "grantedAuthorization": {
                        "authorizedAt": "2024-01-15T15:00:00Z",
                        "authorizationMethod": "MANUAL",
                        "expiresAt": "2024-01-15T16:00:00Z",
                        "dataUsageLimitMBytes": 1024,
                        "rxRateLimitKbps": 1000,
                        "txRateLimitKbps": 1000,
                        "usage": {},
                    },
                }
            ],
        },
    )

    response = await network_client_with_site.clients.authorize_guest_access(client_id)

    assert response["action"] == "AUTHORIZE_GUEST_ACCESS"
    assert response["grantedAuthorization"]["authorizedAt"] == "2024-01-15T15:00:00Z"
    assert response["grantedAuthorization"]["dataUsageLimitMBytes"] == 1024
    assert_request_called_with(
        mock_aioresponse,
        "post",
        f"/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}/actions",
        json_body={"action": "AUTHORIZE_GUEST_ACCESS"},
    )


async def test_network_clients_authorize_guest_access_full_params(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify authorize_guest_access with all optional parameters."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.post(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}/actions",
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "action": "AUTHORIZE_GUEST_ACCESS",
                    "revokedAuthorization": {
                        "authorizedAt": "2024-01-15T14:00:00Z",
                        "authorizationMethod": "VOUCHER",
                        "expiresAt": "2024-01-15T15:00:00Z",
                        "dataUsageLimitMBytes": 512,
                        "rxRateLimitKbps": 500,
                        "txRateLimitKbps": 500,
                        "usage": {"dataUsageMBytes": 100},
                    },
                    "grantedAuthorization": {
                        "authorizedAt": "2024-01-15T15:05:00Z",
                        "authorizationMethod": "MANUAL",
                        "expiresAt": "2024-01-15T17:05:00Z",
                        "dataUsageLimitMBytes": 2048,
                        "rxRateLimitKbps": 5000,
                        "txRateLimitKbps": 5000,
                        "usage": {},
                    },
                }
            ],
        },
    )

    response = await network_client_with_site.clients.authorize_guest_access(
        client_id,
        time_limit_minutes=120,
        data_usage_limit_mbytes=2048,
        rx_rate_limit_kbps=5000,
        tx_rate_limit_kbps=5000,
    )

    assert response["action"] == "AUTHORIZE_GUEST_ACCESS"
    assert "revokedAuthorization" in response
    assert response["revokedAuthorization"]["dataUsageLimitMBytes"] == 512
    assert response["grantedAuthorization"]["dataUsageLimitMBytes"] == 2048
    assert response["grantedAuthorization"]["rxRateLimitKbps"] == 5000
    assert_request_called_with(
        mock_aioresponse,
        "post",
        f"/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}/actions",
        json_body={
            "action": "AUTHORIZE_GUEST_ACCESS",
            "timeLimitMinutes": 120,
            "dataUsageLimitMBytes": 2048,
            "rxRateLimitKbps": 5000,
            "txRateLimitKbps": 5000,
        },
    )


async def test_network_clients_unauthorized(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify unauthorized response is mapped to Unauthorized."""
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        status=401,
    )

    with pytest.raises(Unauthorized):
        await network_client_with_site.clients.list()


async def test_network_clients_get_details_unauthorized(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify unauthorized response on get_details."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.get(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}",
        status=401,
    )

    with pytest.raises(Unauthorized):
        await network_client_with_site.clients.get_details(client_id)


async def test_network_clients_authorize_guest_structured_error(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify structured API error fields are included in raised exceptions."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.post(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}/actions",
        status=401,
        payload={
            "statusCode": 401,
            "statusName": "UNAUTHORIZED",
            "code": "api.authentication.missing-credentials",
            "message": "Missing credentials",
            "timestamp": "2024-11-27T08:13:46.966Z",
            "requestPath": f"/v1/sites/{site_id}/clients/{client_id}/actions",
            "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
    )

    with pytest.raises(
        Unauthorized, match="api.authentication.missing-credentials"
    ) as err:
        await network_client_with_site.clients.authorize_guest_access(client_id)

    assert getattr(err.value, "status_code") == 401
    assert getattr(err.value, "status_name") == "UNAUTHORIZED"
    assert getattr(err.value, "code") == "api.authentication.missing-credentials"
    assert getattr(err.value, "detail") == "Missing credentials"


async def test_network_clients_list_client_properties(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify all client properties are correctly extracted from response."""
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "type": "WIRED",
                    "id": "client-full",
                    "name": "Full Client",
                    "connectedAt": "2024-01-15T10:30:00Z",
                    "ipAddress": "192.168.1.100",
                    "access": {"type": "DEFAULT"},
                    "macAddress": "aa:bb:cc:dd:ee:ff",
                    "uplinkDeviceId": "device-full-uuid",
                }
            ],
        },
    )

    clients = await network_client_with_site.clients.list()

    client = clients[0]
    assert client.client_id == "client-full"
    assert client.name == "Full Client"
    assert client.type == "WIRED"
    assert client.mac_address == "aa:bb:cc:dd:ee:ff"
    assert client.ip_address == "192.168.1.100"
    assert client.connected_at == "2024-01-15T10:30:00Z"
    assert client.access == {"type": "DEFAULT"}
    assert client.access_type == "DEFAULT"
    assert client.uplink_device_id == "device-full-uuid"


async def test_network_clients_optional_fields(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify optional fields (connectedAt, ipAddress) can be missing."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.get(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}",
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "type": "WIRED",
                    "id": client_id,
                    "name": "Minimal Client",
                    "access": {"type": "DEFAULT"},
                    "macAddress": "aa:bb:cc:dd:ee:ff",
                    "uplinkDeviceId": "device-minimal-uuid",
                }
            ],
        },
    )

    client = await network_client_with_site.clients.get_details(client_id)

    assert client.client_id == client_id
    assert client.connected_at is None
    assert client.ip_address is None


async def test_network_clients_authorize_guest_partial_params(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify authorize_guest_access with only some optional parameters."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.post(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}/actions",
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "action": "AUTHORIZE_GUEST_ACCESS",
                    "grantedAuthorization": {
                        "authorizedAt": "2024-01-15T15:00:00Z",
                        "authorizationMethod": "MANUAL",
                        "expiresAt": "2024-01-15T15:30:00Z",
                        "dataUsageLimitMBytes": 500,
                        "rxRateLimitKbps": 1000,
                        "txRateLimitKbps": 1000,
                        "usage": {},
                    },
                }
            ],
        },
    )

    response = await network_client_with_site.clients.authorize_guest_access(
        client_id,
        time_limit_minutes=30,
        data_usage_limit_mbytes=500,
    )

    assert response["action"] == "AUTHORIZE_GUEST_ACCESS"
    assert response["grantedAuthorization"]["dataUsageLimitMBytes"] == 500
    assert_request_called_with(
        mock_aioresponse,
        "post",
        f"/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}/actions",
        json_body={
            "action": "AUTHORIZE_GUEST_ACCESS",
            "timeLimitMinutes": 30,
            "dataUsageLimitMBytes": 500,
        },
    )


async def test_network_clients_update_indexes_by_mac(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify APIHandler storage for v1 clients is keyed by MAC address."""
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 25,
            "count": 1,
            "totalCount": 1,
            "data": [_client_payload()],
        },
    )

    await network_client_with_site.clients.update()

    assert "aa:bb:cc:dd:ee:ff" in network_client_with_site.clients
    assert (
        network_client_with_site.clients["aa:bb:cc:dd:ee:ff"].client_id == "client-uuid"
    )


async def test_network_clients_update_normalizes_mac_keys(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify cached client keys are canonical even for uppercase payload MACs."""
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 25,
            "count": 1,
            "totalCount": 1,
            "data": [_client_payload(macAddress="AA:BB:CC:DD:EE:FF")],
        },
    )

    await network_client_with_site.clients.update()

    assert "aa:bb:cc:dd:ee:ff" in network_client_with_site.clients
    assert "AA:BB:CC:DD:EE:FF" in network_client_with_site.clients
    assert (
        network_client_with_site.clients["AA:BB:CC:DD:EE:FF"].client_id == "client-uuid"
    )


def test_network_clients_get_by_mac_cached_normalizes_input(
    network_client_with_site,
) -> None:
    """Verify cached MAC lookups normalize user input before lookup."""
    network_client_with_site.clients._items = {
        "aa:bb:cc:dd:ee:ff": network_client_with_site.clients.item_cls(
            _client_payload()
        )
    }

    client = network_client_with_site.clients.get_by_mac_cached("AA-BB-CC-DD-EE-FF")

    assert client is not None
    assert client.client_id == "client-uuid"


async def test_network_clients_get_by_mac_success(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify get_by_mac resolves via server-side filter with normalized MAC."""
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [_client_payload()],
        },
    )

    client = await network_client_with_site.clients.get_by_mac("AA-BB-CC-DD-EE-FF")

    assert client is not None
    assert client.client_id == "client-uuid"
    assert_request_called_with(
        mock_aioresponse,
        "get",
        "/proxy/network/integration/v1/sites/site-uuid/clients",
        params={
            "offset": 0,
            "limit": 1,
            "filter": "macAddress.eq('aa:bb:cc:dd:ee:ff')",
        },
    )


async def test_network_clients_get_by_mac_not_found(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify get_by_mac returns None when no match is found."""
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 1,
            "count": 0,
            "totalCount": 0,
            "data": [],
        },
    )

    assert (
        await network_client_with_site.clients.get_by_mac("aa:bb:cc:dd:ee:ff") is None
    )


async def test_network_clients_require_by_mac_not_found(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify require_by_mac raises RequestError when no match exists."""
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 1,
            "count": 0,
            "totalCount": 0,
            "data": [],
        },
    )

    with pytest.raises(RequestError, match="mac_address"):
        await network_client_with_site.clients.require_by_mac("aa:bb:cc:dd:ee:ff")


def test_network_clients_get_by_uuid_from_cache(network_client_with_site) -> None:
    """Verify get_by_uuid resolves from cached handler state."""
    network_client_with_site.clients._items = {
        "aa:bb:cc:dd:ee:ff": network_client_with_site.clients.item_cls(
            _client_payload()
        )
    }

    client = network_client_with_site.clients.get_by_uuid("client-uuid")
    assert client is not None
    assert client.mac_address == "aa:bb:cc:dd:ee:ff"


def test_network_clients_require_by_uuid_missing(network_client_with_site) -> None:
    """Verify require_by_uuid raises RequestError when cache has no match."""
    with pytest.raises(RequestError, match="client_id"):
        network_client_with_site.clients.require_by_uuid("missing")


async def test_network_clients_get_details_by_mac(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify get_details_by_mac resolves UUID via MAC filter then fetches details."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [_client_payload(type="WIRELESS", id=client_id, name="Client")],
        },
    )
    mock_aioresponse.get(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}",
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [_client_payload(type="WIRELESS", id=client_id, name="Client")],
        },
    )

    client = await network_client_with_site.clients.get_details_by_mac(
        "aa:bb:cc:dd:ee:ff"
    )
    assert client.client_id == client_id


async def test_network_clients_authorize_guest_access_by_mac(
    mock_aioresponse, network_client_with_site
) -> None:
    """Verify authorize_guest_access_by_mac resolves UUID and sends action request."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "type": "WIRELESS",
                    "id": client_id,
                    "name": "Client",
                    "access": {"type": "DEFAULT"},
                    "macAddress": "aa:bb:cc:dd:ee:ff",
                    "uplinkDeviceId": "device-uuid-1",
                }
            ],
        },
    )
    mock_aioresponse.post(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}/actions",
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "action": "AUTHORIZE_GUEST_ACCESS",
                    "grantedAuthorization": {
                        "authorizedAt": "2024-01-15T15:00:00Z",
                        "authorizationMethod": "MANUAL",
                        "expiresAt": "2024-01-15T16:00:00Z",
                        "dataUsageLimitMBytes": 1024,
                        "rxRateLimitKbps": 1000,
                        "txRateLimitKbps": 1000,
                        "usage": {},
                    },
                }
            ],
        },
    )

    response = await network_client_with_site.clients.authorize_guest_access_by_mac(
        "aa:bb:cc:dd:ee:ff", time_limit_minutes=60
    )

    assert response["action"] == "AUTHORIZE_GUEST_ACCESS"
    assert_request_called_with(
        mock_aioresponse,
        "post",
        f"/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}/actions",
        json_body={"action": "AUTHORIZE_GUEST_ACCESS", "timeLimitMinutes": 60},
    )
