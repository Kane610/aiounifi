"""Test the clients interface against captured console responses."""

from datetime import UTC, datetime

from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.network.v1.api_client import ApiClient

from .conftest import BASE_URL, SITE_ID, envelope, requests_to, url_pattern

HA_CLIENT = {
    "type": "WIRED",
    "id": "f9edef13-b667-369f-9556-bc36978095af",
    "name": "ha",
    "connectedAt": "2026-09-24T17:40:52Z",
    "ipAddress": "10.8.0.20",
    "macAddress": "20:f8:3b:03:ec:9c",
    "uplinkDeviceId": "72cf3194-b496-3ada-877c-6764792adc4a",
    "access": {"type": "DEFAULT"},
}
VPN_CLIENT = {
    "type": "VPN",
    "id": "0d1e2f3a-0000-4000-8000-000000000003",
    "name": "laptop-wireguard",
    "connectedAt": "2026-09-24T18:00:00Z",
    "ipAddress": "10.8.99.2",
    "access": {"type": "DEFAULT"},
}
GUEST_CLIENT = {
    "type": "WIRELESS",
    "id": "e704bf9d-7359-3026-89fd-5d5e224e963d",
    "name": "phone",
    "macAddress": "72:af:09:a5:03:bc",
    "access": {"type": "GUEST"},
}


async def test_update_and_properties(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Clients are cached by MAC and expose their fields."""
    mock_aioresponse.get(
        url_pattern(f"/v1/sites/{SITE_ID}/clients"),
        payload=envelope([HA_CLIENT, GUEST_CLIENT, VPN_CLIENT]),
    )
    clients = network_client_with_site.clients

    await clients.update()

    assert len(clients.items()) == 2, "VPN clients have no MAC and are not cached"

    ha = clients["20:F8:3B:03:EC:9C"]
    assert ha.client_id == "f9edef13-b667-369f-9556-bc36978095af"
    assert ha.name == "ha"
    assert ha.type == "WIRED"
    assert ha.mac_address == "20:f8:3b:03:ec:9c"
    assert ha.ip_address == "10.8.0.20"
    assert ha.connected_at == "2026-09-24T17:40:52Z"
    assert ha.access_type == "DEFAULT"
    assert ha.uplink_device_id == "72cf3194-b496-3ada-877c-6764792adc4a"

    guest = clients["72:af:09:a5:03:bc"]
    assert guest.ip_address is None
    assert guest.connected_at is None
    assert guest.uplink_device_id is None
    assert guest.access_type == "GUEST"


async def test_list_page_returns_clients_without_mac(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """A VPN client is a client, just not one with a MAC address."""
    mock_aioresponse.get(
        url_pattern(f"/v1/sites/{SITE_ID}/clients"), payload=envelope([VPN_CLIENT])
    )

    (client,) = await network_client_with_site.clients.list_page()

    assert client.type == "VPN"
    assert client.mac_address is None
    assert client.uplink_device_id is None
    assert client.ip_address == "10.8.99.2"


async def test_unauthorize_guest_access(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Revoking posts the matching action."""
    mock_aioresponse.post(
        f"{BASE_URL}/v1/sites/{SITE_ID}/clients/{GUEST_CLIENT['id']}/actions",
        payload={"action": "UNAUTHORIZE_GUEST_ACCESS"},
    )

    response = await network_client_with_site.clients.unauthorize_guest_access(
        GUEST_CLIENT["id"]
    )

    assert response["action"] == "UNAUTHORIZE_GUEST_ACCESS"
    (call,) = requests_to(mock_aioresponse, "post", "/actions")
    assert call.kwargs["data"] == b'{"action":"UNAUTHORIZE_GUEST_ACCESS"}'


async def test_get_details(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """The detail endpoint returns a bare object."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/sites/{SITE_ID}/clients/{HA_CLIENT['id']}", payload=HA_CLIENT
    )

    client = await network_client_with_site.clients.get_details(HA_CLIENT["id"])

    assert client.name == "ha"


async def test_get_by_mac(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Lookup by MAC filters on the console and returns one client or None."""
    mock_aioresponse.get(
        url_pattern(f"/v1/sites/{SITE_ID}/clients"), payload=envelope([HA_CLIENT])
    )
    mock_aioresponse.get(
        url_pattern(f"/v1/sites/{SITE_ID}/clients"), payload=envelope([])
    )
    clients = network_client_with_site.clients

    found = await clients.get_by_mac("20-F8-3B-03-EC-9C")
    missing = await clients.get_by_mac("00:00:00:00:00:00")

    assert found is not None
    assert found.client_id == HA_CLIENT["id"]
    assert missing is None
    calls = requests_to(mock_aioresponse, "get", "/clients")
    assert calls[0].kwargs["params"] == {
        "offset": 0,
        "limit": 1,
        "filter": "macAddress.eq('20:f8:3b:03:ec:9c')",
    }


async def test_authorize_guest_access(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Guest authorization posts the action with only the limits given."""
    mock_aioresponse.post(
        f"{BASE_URL}/v1/sites/{SITE_ID}/clients/{GUEST_CLIENT['id']}/actions",
        payload={
            "action": "AUTHORIZE_GUEST_ACCESS",
            "grantedAuthorization": {
                "authorizedAt": "2026-09-24T20:00:00Z",
                "authorizationMethod": "API",
                "expiresAt": "2026-09-24T21:00:00Z",
            },
        },
    )

    response = await network_client_with_site.clients.authorize_guest_access(
        GUEST_CLIENT["id"], time_limit_minutes=60, rx_rate_limit_kbps=5000
    )

    assert response["grantedAuthorization"]["expiresAt"] == "2026-09-24T21:00:00Z"
    (call,) = requests_to(mock_aioresponse, "post", "/actions")
    assert (
        call.kwargs["data"]
        == b'{"action":"AUTHORIZE_GUEST_ACCESS","timeLimitMinutes":60,"rxRateLimitKbps":5000}'
    )


async def test_authorize_guest_access_all_limits(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Every limit has its own field."""
    mock_aioresponse.post(
        f"{BASE_URL}/v1/sites/{SITE_ID}/clients/{GUEST_CLIENT['id']}/actions",
        payload={"action": "AUTHORIZE_GUEST_ACCESS"},
    )

    await network_client_with_site.clients.authorize_guest_access(
        GUEST_CLIENT["id"],
        time_limit_minutes=1,
        data_usage_limit_mbytes=2,
        rx_rate_limit_kbps=3,
        tx_rate_limit_kbps=4,
    )

    (call,) = requests_to(mock_aioresponse, "post", "/actions")
    assert (
        call.kwargs["data"]
        == b'{"action":"AUTHORIZE_GUEST_ACCESS","timeLimitMinutes":1,"dataUsageLimitMBytes":2,"rxRateLimitKbps":3,"txRateLimitKbps":4}'
    )


async def test_client_that_leaves_is_kept(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """A client missing from the list stays cached and reads as disconnected."""
    path = url_pattern(f"/v1/sites/{SITE_ID}/clients")
    mock_aioresponse.get(path, payload=envelope([HA_CLIENT, GUEST_CLIENT]))
    mock_aioresponse.get(path, payload=envelope([HA_CLIENT]))
    mock_aioresponse.get(path, payload=envelope([HA_CLIENT]))
    mock_aioresponse.get(path, payload=envelope([HA_CLIENT, GUEST_CLIENT]))
    clients = network_client_with_site.clients
    events: list[tuple[ItemEvent, str, bool]] = []
    guest_mac = GUEST_CLIENT["macAddress"]

    await clients.update()
    first_seen = clients.last_seen(guest_mac)
    assert clients.is_connected(guest_mac)
    assert first_seen is not None

    # Each event records what `is_connected` said inside the callback
    clients.subscribe(
        lambda event, obj_id: (
            events.append((event, obj_id, clients.is_connected(obj_id)))
            if obj_id == guest_mac
            else None
        )
    )
    await clients.update()
    await clients.update()

    assert guest_mac in clients
    assert clients[guest_mac].name == "phone"
    assert not clients.is_connected(guest_mac)
    assert clients.last_seen(guest_mac) == first_seen
    assert events == [(ItemEvent.CHANGED, guest_mac, False)], (
        "signalled once, as it left, and already disconnected then"
    )

    await clients.update()

    assert clients.is_connected(guest_mac)
    assert clients.last_seen(guest_mac) > first_seen
    assert events[-1] == (ItemEvent.CHANGED, guest_mac, True)


async def test_forget(mock_aioresponse, network_client_with_site: ApiClient) -> None:
    """Forgetting a client drops it and signals DELETED."""
    mock_aioresponse.get(
        url_pattern(f"/v1/sites/{SITE_ID}/clients"), payload=envelope([HA_CLIENT])
    )
    clients = network_client_with_site.clients
    await clients.update()
    events: list[tuple[ItemEvent, str]] = []
    clients.subscribe(lambda event, obj_id: events.append((event, obj_id)))

    clients.forget("20-F8-3B-03-EC-9C")
    clients.forget("20:f8:3b:03:ec:9c")

    assert "20:f8:3b:03:ec:9c" not in clients
    assert not clients.is_connected("20:f8:3b:03:ec:9c")
    assert clients.last_seen("20:f8:3b:03:ec:9c") is None
    assert events == [(ItemEvent.DELETED, "20:f8:3b:03:ec:9c")]


async def test_restore(mock_aioresponse, network_client_with_site: ApiClient) -> None:
    """A restored client is cached and disconnected until an update lists it."""
    mock_aioresponse.get(
        url_pattern(f"/v1/sites/{SITE_ID}/clients"), payload=envelope([GUEST_CLIENT])
    )
    clients = network_client_with_site.clients
    events: list[tuple[ItemEvent, str]] = []
    clients.subscribe(lambda event, obj_id: events.append((event, obj_id)))
    seen = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)

    assert clients.restore(HA_CLIENT, seen) == "20:f8:3b:03:ec:9c"
    assert clients.restore(VPN_CLIENT) is None, "no MAC, nothing to key on"

    assert clients["20:f8:3b:03:ec:9c"].name == "ha"
    assert not clients.is_connected("20:f8:3b:03:ec:9c")
    assert clients.last_seen("20:f8:3b:03:ec:9c") == seen
    assert events == [(ItemEvent.ADDED, "20:f8:3b:03:ec:9c")]

    await clients.update()

    assert "20:f8:3b:03:ec:9c" in clients, "not listed, still kept"
    assert not clients.is_connected("20:f8:3b:03:ec:9c")
    assert clients.last_seen("20:f8:3b:03:ec:9c") == seen
    assert clients.is_connected(GUEST_CLIENT["macAddress"])
    assert (ItemEvent.DELETED, "20:f8:3b:03:ec:9c") not in events
