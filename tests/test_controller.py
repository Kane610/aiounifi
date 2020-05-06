"""Test controller.

pytest --cov-report term-missing --cov=aiounifi.controller tests/test_controller.py
"""

import asyncio
from asynctest import MagicMock, Mock, patch
from collections import deque
import pytest

from aiounifi.api import SOURCE_DATA, SOURCE_EVENT
from aiounifi.controller import (
    ATTR_MESSAGE,
    ATTR_META,
    Controller,
    DATA_CLIENT,
    DATA_CLIENT_REMOVED,
    DATA_DEVICE,
    DATA_EVENT,
    MESSAGE_CLIENT,
    MESSAGE_DEVICE,
)
from aiounifi.clients import (
    URL as client_url,
    URL_ALL as all_client_url,
)
from aiounifi.devices import URL as device_url
from aiounifi.events import SWITCH_CONNECTED, WIRELESS_CLIENT_CONNECTED
from aiounifi.websocket import SIGNAL_CONNECTION_STATE, SIGNAL_DATA
from aiounifi.wlan import URL as wlan_url

from fixtures import (
    EVENT_SWITCH_16_CONNECTED,
    EVENT_WIRELESS_CLIENT_CONNECTED,
    MESSAGE_WIRELESS_CLIENT_REMOVED,
    SWITCH_16_PORT_POE,
    WIRELESS_CLIENT,
    WLANS,
)

HOST = "127.0.0.1"
PORT = "80"
USERNAME = "user"
PASSWORD = "password"


@pytest.fixture
def controller() -> Controller:
    """Returns the session object."""
    session = MagicMock()
    callback = Mock()
    return Controller(
        HOST, session, username=USERNAME, password=PASSWORD, callback=callback
    )


def mock_request_response(
    controller, json={}, status=200, content_type="application/json", headers=None,
):
    mock_response = Mock()
    mock_response.json.return_value = asyncio.Future()
    mock_response.json.return_value.set_result(json)
    mock_response.status = status
    mock_response.content_type = content_type
    mock_response.headers = headers

    controller.session.request.return_value.__aenter__.side_effect = Mock(
        return_value=mock_response
    )


async def mock_initialize(
    controller,
    *,
    clients_response=None,
    devices_response=None,
    clients_all_response=None,
    wlans_response=None,
):

    mock_client_responses = deque()
    if clients_response:
        mock_client_responses.append(clients_response)

    mock_device_responses = deque()
    if devices_response:
        mock_device_responses.append(devices_response)

    mock_client_all_responses = deque()
    if clients_all_response:
        mock_client_all_responses.append(clients_all_response)

    mock_wlans_responses = deque()
    if wlans_response:
        mock_wlans_responses.append(wlans_response)

    controller.mock_requests = mock_requests = []

    async def mock_request(self, method, path, json=None):
        mock_requests.append({"method": method, "path": path, "json": json})

        if path == "/stat/sta" and mock_client_responses:
            return mock_client_responses.popleft()
        if path == "/stat/device" and mock_device_responses:
            return mock_device_responses.popleft()
        if path == "/rest/user" and mock_client_all_responses:
            return mock_client_all_responses.popleft()
        if path == "/rest/wlanconf" and mock_wlans_responses:
            return mock_wlans_responses.popleft()
        return {}

    with patch("aiounifi.Controller.request", new=mock_request):
        await controller.initialize()
    controller.start_websocket()


async def test_controller(controller):
    """Test controller communicating with a non UniFiOS UniFi controller."""

    assert controller.session.request.call_count == 0

    mock_request_response(
        controller, content_type="application/octet-stream", status=302
    )
    await controller.check_unifi_os()
    assert not controller.is_unifi_os
    assert controller.session.request.call_count == 1
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443",
        allow_redirects=False,
        headers=None,
        json=None,
        ssl=None,
    )

    mock_request_response(controller)
    await controller.login()
    assert controller.session.request.call_count == 2
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "post",
        "https://127.0.0.1:8443/api/login",
        headers=None,
        json={"username": "user", "password": "password", "remember": True},
        ssl=None,
    )

    # controller.initialize

    mock_request_response(controller, json=EMPTY_RESPONSE)
    await controller.request("get", client_url)
    assert controller.session.request.call_count == 3
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/api/s/default/stat/sta",
        headers=None,
        json=None,
        ssl=None,
    )

    mock_request_response(controller, json=EMPTY_RESPONSE)
    await controller.request("get", device_url)
    assert controller.session.request.call_count == 4
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/api/s/default/stat/device",
        headers=None,
        json=None,
        ssl=None,
    )

    mock_request_response(controller, json=EMPTY_RESPONSE)
    await controller.request("get", all_client_url)
    assert controller.session.request.call_count == 5
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/api/s/default/rest/user",
        headers=None,
        json=None,
        ssl=None,
    )

    mock_request_response(controller, json=WLAN_UNIFIOS_RESPONSE)
    await controller.request("get", wlan_url)
    assert controller.session.request.call_count == 6
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/api/s/default/rest/wlanconf",
        headers=None,
        json=None,
        ssl=None,
    )

    mock_request_response(controller, json=SITE_UNIFIOS_RESPONSE)
    await controller.sites()
    assert controller.session.request.call_count == 7
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/api/self/sites",
        headers=None,
        json=None,
        ssl=None,
    )

    controller.start_websocket()
    assert controller.websocket.url == "wss://127.0.0.1:8443/wss/s/default/events"


async def test_unifios_controller(controller):
    """Test controller communicating with a UniFi OS controller."""

    assert controller.session.request.call_count == 0

    mock_request_response(
        controller, content_type="text/html", headers={"x-csrf-token": 123}
    )
    await controller.check_unifi_os()
    assert controller.is_unifi_os
    assert controller.session.request.call_count == 1
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443",
        allow_redirects=False,
        headers=None,
        json=None,
        ssl=None,
    )

    mock_request_response(controller, json=LOGIN_UNIFIOS_JSON_RESPONSE)
    await controller.login()
    assert controller.session.request.call_count == 2
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "post",
        "https://127.0.0.1:8443/api/auth/login",
        headers={"x-csrf-token": 123},
        json={"username": "user", "password": "password", "remember": True},
        ssl=None,
    )

    # controller.initialize

    mock_request_response(controller, json=EMPTY_RESPONSE)
    await controller.request("get", client_url)
    assert controller.session.request.call_count == 3
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/proxy/network/api/s/default/stat/sta",
        headers={"x-csrf-token": 123},
        json=None,
        ssl=None,
    )

    mock_request_response(controller, json=EMPTY_RESPONSE)
    await controller.request("get", device_url)
    assert controller.session.request.call_count == 4
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/proxy/network/api/s/default/stat/device",
        headers={"x-csrf-token": 123},
        json=None,
        ssl=None,
    )

    mock_request_response(controller, json=EMPTY_RESPONSE)
    await controller.request("get", all_client_url)
    assert controller.session.request.call_count == 5
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/proxy/network/api/s/default/rest/user",
        headers={"x-csrf-token": 123},
        json=None,
        ssl=None,
    )

    mock_request_response(controller, json=WLAN_UNIFIOS_RESPONSE)
    await controller.request("get", wlan_url)
    assert controller.session.request.call_count == 6
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/proxy/network/api/s/default/rest/wlanconf",
        headers={"x-csrf-token": 123},
        json=None,
        ssl=None,
    )

    mock_request_response(controller, json=SITE_UNIFIOS_RESPONSE)
    await controller.sites()
    assert controller.session.request.call_count == 7
    assert controller.session.request.called
    controller.session.request.assert_called_with(
        "get",
        "https://127.0.0.1:8443/proxy/network/api/self/sites",
        headers={"x-csrf-token": 123},
        json=None,
        ssl=None,
    )

    controller.start_websocket()
    assert (
        controller.websocket.url
        == "wss://127.0.0.1:8443/proxy/network/wss/s/default/events"
    )


async def test_no_data(controller, caplog):
    """Test controller initialize."""
    assert not controller.session_handler(SIGNAL_DATA)
    assert not controller.session_handler(SIGNAL_CONNECTION_STATE)

    await mock_initialize(controller)

    assert len(controller.clients._items) == 0
    assert len(controller.clients_all._items) == 0
    assert len(controller.devices._items) == 0
    assert len(controller.wlans._items) == 0

    assert not controller.clients[1]
    assert "Couldn't find key: 1" in caplog.text

    message = {ATTR_META: {ATTR_MESSAGE: "blabla"}}
    assert controller.message_handler(message) == {}

    assert not controller.stop_websocket()


async def test_client(controller):
    """Test controller adding client on initialize."""
    await mock_initialize(controller, clients_response=[WIRELESS_CLIENT])
    assert len(controller.clients._items) == 1


async def test_clients(controller):
    """Test controller managing clients."""
    await mock_initialize(controller)
    assert len(controller.clients._items) == 0

    # Add client from websocket
    controller.websocket._data = {
        "meta": {"message": MESSAGE_CLIENT},
        "data": [WIRELESS_CLIENT],
    }
    controller.session_handler(SIGNAL_DATA)
    assert len(controller.clients._items) == 1

    # Verify expected callback signalling
    client = controller.clients[WIRELESS_CLIENT["mac"]]
    controller.callback.assert_called_with(SIGNAL_DATA, {DATA_CLIENT: {client.mac}})

    # Verify APIItems.__getitem__
    client_mac = next(iter(controller.clients))
    assert client_mac == client.mac

    assert client.update() is None

    # Register callback
    mock_callback = MagicMock()
    client.register_callback(mock_callback)
    assert len(client._callbacks) == 1

    # Retrieve websocket data
    controller.websocket._data = {
        "meta": {"message": MESSAGE_CLIENT},
        "data": [WIRELESS_CLIENT],
    }
    controller.session_handler(SIGNAL_DATA)

    controller.callback.assert_called_with(SIGNAL_DATA, {DATA_CLIENT: set()})
    assert client.last_updated == SOURCE_DATA
    assert mock_callback.call_count == 1

    # Retrieve websocket event
    controller.websocket._data = EVENT_WIRELESS_CLIENT_CONNECTED
    controller.session_handler(SIGNAL_DATA)

    controller.callback.assert_called_with(SIGNAL_DATA, {DATA_EVENT: {client.event}})
    assert client.event.event == WIRELESS_CLIENT_CONNECTED
    assert client.last_updated == SOURCE_EVENT
    assert mock_callback.call_count == 2

    # Remove callback
    client.remove_callback(mock_callback)
    assert len(client._callbacks) == 0


async def test_message_client_removed(controller):
    """Test controller communicating client has been removed."""
    await mock_initialize(controller, clients_response=[WIRELESS_CLIENT])
    assert len(controller.clients._items) == 1

    controller.websocket._data = MESSAGE_WIRELESS_CLIENT_REMOVED
    controller.session_handler(SIGNAL_DATA)
    controller.callback.assert_called_with(
        SIGNAL_DATA, {DATA_CLIENT_REMOVED: {WIRELESS_CLIENT["mac"]}}
    )

    assert len(controller.clients._items) == 0


async def test_device(controller):
    """Test controller adding device on initialize."""
    await mock_initialize(controller, devices_response=[SWITCH_16_PORT_POE])
    assert len(controller.devices._items) == 1


async def test_devices(controller):
    """Test controller managing devices."""
    await mock_initialize(controller)
    assert len(controller.devices._items) == 0

    # Add client from websocket
    controller.websocket._data = {
        "meta": {"message": MESSAGE_DEVICE},
        "data": [SWITCH_16_PORT_POE],
    }
    controller.session_handler(SIGNAL_DATA)
    assert len(controller.devices._items) == 1

    # Verify expected callback signalling
    device = controller.devices[SWITCH_16_PORT_POE["mac"]]
    controller.callback.assert_called_with(SIGNAL_DATA, {DATA_DEVICE: {device.mac}})

    # Verify APIItems.__getitem__
    device_mac = next(iter(controller.devices))
    assert device_mac == device.mac

    # Verify Device.Port.__iter__
    port_1 = next(iter(device.ports))
    assert port_1 == 1

    assert device.update() is None

    # Register callback
    mock_callback = MagicMock()
    device.register_callback(mock_callback)
    assert len(device._callbacks) == 1

    # Retrieve websocket data
    controller.websocket._data = {
        "meta": {"message": MESSAGE_DEVICE},
        "data": [SWITCH_16_PORT_POE],
    }
    controller.session_handler(SIGNAL_DATA)

    controller.callback.assert_called_with(SIGNAL_DATA, {DATA_DEVICE: set()})
    assert device.last_updated == SOURCE_DATA
    assert mock_callback.call_count == 1

    # Retrieve websocket event
    controller.websocket._data = EVENT_SWITCH_16_CONNECTED
    controller.session_handler(SIGNAL_DATA)

    controller.callback.assert_called_with(SIGNAL_DATA, {DATA_EVENT: {device.event}})
    assert device.event.event == SWITCH_CONNECTED
    assert device.last_updated == SOURCE_EVENT
    assert mock_callback.call_count == 2

    # Remove callback
    device.remove_callback(mock_callback)
    assert len(device._callbacks) == 0


EMPTY_RESPONSE = {"meta": {"rc": "ok"}, "data": []}

LOGIN_UNIFIOS_JSON_RESPONSE = {
    "unique_id": "868d288b-a642-4209-a768-8425498fa928",
    "username": "Testing1",
    "first_name": "Testing",
    "last_name": "Testing",
    "full_name": "Testing Testing",
    "email": "",
    "email_status": "UNVERIFIED",
    "phone": "",
    "avatar": "",
    "avatar_relative_path": "",
    "status": "ACTIVE",
    "sso_account": "",
    "sso_uuid": "",
    "sso_username": "",
    "create_time": 1585163886,
    "local_account_exist": True,
    "uid_sso_id": "",
    "uid_sso_account": "",
    "password_revision": 1585163886,
    "extras": None,
    "nfc_token": "",
    "nfc_display_id": "",
    "update_time": 1585167486,
    "groups": [],
    "roles": [
        {
            "unique_id": "ddf31242-c4f1-4dbc-b362-d0b220cae124",
            "name": "Super Administrator",
            "system_role": True,
            "system_key": "super_administrator",
            "level": 2,
        }
    ],
    "permissions": {
        "access.management": ["admin"],
        "led.management": ["admin"],
        "network.management": ["admin"],
        "protect.management": ["admin"],
        "system.management.location": ["admin"],
        "system.management.user": ["admin"],
        "talk.management": ["admin"],
    },
    "scopes": [
        "view:user_timezone",
        "view:user",
        "view:systemlog",
        "view:settings",
        "view:role",
        "view:permission:viewer",
        "view:permission:admin",
        "view:notification",
        "view:location_policy",
        "view:location_device",
        "view:location_activity",
        "view:location",
        "view:holiday_timezone",
        "view:holiday",
        "view:group",
        "view:door_group",
        "view:controller:talk",
        "view:controller:protect",
        "view:controller:network",
        "view:controller:led",
        "view:controller:access",
        "view:cloud_access",
        "view:app:users",
        "view:app:settings",
        "view:app:locations",
        "view:access.visitor",
        "view:access.systemlog",
        "view:access.schedule",
        "view:access.policy",
        "view:access.nfc_card",
        "view:access.device",
        "view:access.dashboard",
        "update:access.device",
        "systemlog:user",
        "systemlog:system",
        "systemlog:location",
        "systemlog:access",
        "notify:user",
        "notify:location",
        "notify:access",
        "manage:controller:talk",
        "manage:controller:protect",
        "manage:controller:network",
        "manage:controller:led",
        "manage:controller:access",
        "edit:user_timezone",
        "edit:user",
        "edit:systemlog",
        "edit:settings",
        "edit:role",
        "edit:permission:viewer",
        "edit:permission:admin",
        "edit:notification",
        "edit:location_policy",
        "edit:location_device",
        "edit:location_activity",
        "edit:location",
        "edit:holiday_timezone",
        "edit:holiday",
        "edit:group",
        "edit:feedback",
        "edit:door_group",
        "edit:access.visitor",
        "edit:access.schedule",
        "edit:access.policy",
        "edit:access.nfc_card",
        "edit:access.device",
        "delete:access.device",
        "assign:role",
        "adopt:access.device",
    ],
    "cloud_access_granted": False,
    "id": "868d288b-a642-4209-a768-8425498fa928",
    "isOwner": False,
    "isSuperAdmin": True,
}

WLAN_UNIFIOS_RESPONSE = {"meta": {"rc": "ok"}, "data": WLANS}

SITE_UNIFIOS_RESPONSE = {
    "meta": {"rc": "ok"},
    "data": [
        {
            "_id": "5e231c10931eb902acf25112",
            "name": "default",
            "desc": "Default",
            "attr_hidden_id": "default",
            "attr_no_delete": True,
            "role": "admin",
        }
    ],
}
