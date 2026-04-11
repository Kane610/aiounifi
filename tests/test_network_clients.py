"""Test Network API clients endpoint."""

from collections.abc import AsyncGenerator
import re

import aiohttp
import pytest
from yarl import URL

from aiounifi import ApiClient
from aiounifi.errors import Unauthorized
from aiounifi.models.configuration import Configuration


@pytest.fixture(name="network_client")
async def network_client_fixture() -> AsyncGenerator[ApiClient]:
    """Build network client for tests."""
    session = aiohttp.ClientSession()
    config = Configuration(
        session,
        "host",
        username="user",
        password="pass",
        api_key="secret-key",
    )
    client = ApiClient(config)
    yield client
    await session.close()


async def test_network_clients_list_success(mock_aioresponse, network_client) -> None:
    """Verify network clients list returns parsed client models."""
    site_id = "site-uuid"
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

    clients = await network_client.clients.list_page(site_id, offset=0, limit=2)

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


async def test_network_clients_list_default_pagination(
    mock_aioresponse, network_client
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

    clients = await network_client.clients.list(site_id)

    assert len(clients) == 1
    request = next(iter(mock_aioresponse.requests))
    assert request[0] == "get"
    assert isinstance(request[1], URL)
    assert request[1].path == f"/proxy/network/integration/v1/sites/{site_id}/clients"


async def test_network_clients_list_filter(mock_aioresponse, network_client) -> None:
    """Verify filter parameter is accepted for clients list."""
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
                    "id": "guest-1",
                    "name": "Guest Device",
                    "access": {"type": "GUEST"},
                    "macAddress": "aa:bb:cc:dd:ee:ff",
                    "uplinkDeviceId": "device-uuid-1",
                }
            ],
        },
    )

    clients = await network_client.clients.list(
        site_id, filter_value="access.type.eq('GUEST')"
    )

    assert len(clients) == 1
    assert clients[0].access_type == "GUEST"


async def test_network_clients_get_details_success(
    mock_aioresponse, network_client
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

    client = await network_client.clients.get_details(site_id, client_id)

    assert client.client_id == "client-uuid"
    assert client.name == "Smartphone"
    assert client.type == "WIRELESS"
    assert client.mac_address == "bb:cc:dd:ee:ff:00"
    assert client.ip_address == "192.168.1.150"
    assert client.connected_at == "2024-01-15T14:20:00Z"
    assert client.uplink_device_id == "ap-uuid-1"


async def test_network_clients_authorize_guest_access_minimal(
    mock_aioresponse, network_client
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

    response = await network_client.clients.authorize_guest_access(site_id, client_id)

    assert response["action"] == "AUTHORIZE_GUEST_ACCESS"
    assert response["grantedAuthorization"]["authorizedAt"] == "2024-01-15T15:00:00Z"
    assert response["grantedAuthorization"]["dataUsageLimitMBytes"] == 1024


async def test_network_clients_authorize_guest_access_full_params(
    mock_aioresponse, network_client
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

    response = await network_client.clients.authorize_guest_access(
        site_id,
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


async def test_network_clients_unauthorized(mock_aioresponse, network_client) -> None:
    """Verify unauthorized response is mapped to Unauthorized."""
    site_id = "site-uuid"
    mock_aioresponse.get(
        re.compile(
            r"^https://host:8443/proxy/network/integration/v1/sites/site-uuid/clients(?:\?.*)?$"
        ),
        status=401,
    )

    with pytest.raises(Unauthorized):
        await network_client.clients.list(site_id)


async def test_network_clients_get_details_unauthorized(
    mock_aioresponse, network_client
) -> None:
    """Verify unauthorized response on get_details."""
    site_id = "site-uuid"
    client_id = "client-uuid"
    mock_aioresponse.get(
        f"https://host:8443/proxy/network/integration/v1/sites/{site_id}/clients/{client_id}",
        status=401,
    )

    with pytest.raises(Unauthorized):
        await network_client.clients.get_details(site_id, client_id)


async def test_network_clients_authorize_guest_structured_error(
    mock_aioresponse, network_client
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
        await network_client.clients.authorize_guest_access(site_id, client_id)

    assert getattr(err.value, "status_code") == 401
    assert getattr(err.value, "status_name") == "UNAUTHORIZED"
    assert getattr(err.value, "code") == "api.authentication.missing-credentials"
    assert getattr(err.value, "detail") == "Missing credentials"


async def test_network_clients_list_client_properties(
    mock_aioresponse, network_client
) -> None:
    """Verify all client properties are correctly extracted from response."""
    site_id = "site-uuid"
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

    clients = await network_client.clients.list(site_id)

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
    mock_aioresponse, network_client
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
                    "type": "VPN",
                    "id": "client-minimal",
                    "name": "VPN Client",
                    "access": {"type": "DEFAULT"},
                    "macAddress": "bb:cc:dd:ee:ff:00",
                    "uplinkDeviceId": "device-uuid",
                }
            ],
        },
    )

    client = await network_client.clients.get_details(site_id, client_id)

    assert client.client_id == "client-minimal"
    assert client.ip_address is None
    assert client.connected_at is None
    assert client.name == "VPN Client"


async def test_network_clients_authorize_guest_partial_params(
    mock_aioresponse, network_client
) -> None:
    """Verify authorize_guest_access with selective optional parameters."""
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
                        "expiresAt": "2024-01-15T17:00:00Z",
                        "dataUsageLimitMBytes": 1024,
                        "rxRateLimitKbps": 1000,
                        "txRateLimitKbps": 1000,
                        "usage": {},
                    },
                }
            ],
        },
    )

    # Only time limit and rx rate
    response = await network_client.clients.authorize_guest_access(
        site_id,
        client_id,
        time_limit_minutes=120,
        rx_rate_limit_kbps=1000,
    )

    assert response["action"] == "AUTHORIZE_GUEST_ACCESS"
    assert response["grantedAuthorization"]["expiresAt"] == "2024-01-15T17:00:00Z"
