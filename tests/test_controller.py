"""Test controller.

pytest --cov-report term-missing --cov=aiounifi.controller tests/test_controller.py
"""

import asyncio
from asynctest import MagicMock, Mock, patch
from collections import deque
import pytest

from aiounifi.controller import Controller, DATA_CLIENT_REMOVED, DATA_EVENT, SIGNAL_DATA
from aiounifi.clients import (
    URL as client_url,
    URL_ALL as all_client_url,
)
from aiounifi.devices import URL as device_url
from aiounifi.events import (
    WIRED_CLIENT_CONNECTED,
    WIRED_CLIENT_DISCONNECTED,
    WIRELESS_CLIENT_CONNECTED,
    WIRELESS_CLIENT_DISCONNECTED,
)
from aiounifi.wlan import URL as wlan_url

from fixtures import WIRELESS_CLIENT, WLANS

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


async def test_client(controller):
    """Test controller communicating client class."""
    await mock_initialize(controller, clients_response=[WIRELESS_CLIENT])
    assert len(controller.clients._items) == 1


async def test_message_client_events(controller):
    """Test controller communicating different client events."""
    await mock_initialize(controller, clients_response=[WIRELESS_CLIENT])
    assert len(controller.clients._items) == 1

    controller.websocket._data = EVENT_CLIENT_1_WIRELESS_CONNECTED
    controller.session_handler(SIGNAL_DATA)
    controller.callback.assert_called_with(
        SIGNAL_DATA, {DATA_EVENT: {controller.clients[WIRELESS_CLIENT["mac"]].event}}
    )

    assert (
        controller.clients[WIRELESS_CLIENT["mac"]].event.event
        == WIRELESS_CLIENT_CONNECTED
    )


async def test_message_client_removed(controller):
    """Test controller communicating client has been removed."""
    await mock_initialize(controller, clients_response=[WIRELESS_CLIENT])
    assert len(controller.clients._items) == 1

    controller.websocket._data = MESSAGE_CLIENT_1_REMOVED
    controller.session_handler(SIGNAL_DATA)
    controller.callback.assert_called_with(
        SIGNAL_DATA, {DATA_CLIENT_REMOVED: {WIRELESS_CLIENT["mac"]}}
    )

    assert len(controller.clients._items) == 0


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


MESSAGE_CLIENT_1_REMOVED = {
    "meta": {"rc": "ok", "message": "user:delete"},
    "data": [
        {
            "_id": "5cdb099be4b01dd218123456",
            "mac": WIRELESS_CLIENT["mac"],
            "site_id": WIRELESS_CLIENT["essid"],
            "oui": "NortelNe",
            "is_guest": False,
            "first_seen": 1557858715,
            "last_seen": WIRELESS_CLIENT["last_seen"] + 10,
            "is_wired": WIRELESS_CLIENT["is_wired"],
        }
    ],
}


EVENT_CLIENT_1_WIRELESS_DISCONNECTED = {
    "meta": {"rc": "ok", "message": "events"},
    "data": [
        {
            "user": WIRELESS_CLIENT["mac"],
            "ssid": "ssid",
            "hostname": WIRELESS_CLIENT["hostname"],
            "ap": "80:2a:a8:00:00:01",
            "duration": 467,
            "bytes": 459039,
            "key": "EVT_WU_Disconnected",
            "subsystem": "wlan",
            "site_id": WIRELESS_CLIENT["essid"],
            "time": 1587752927000,
            "datetime": "2020-04-24T18:28:47Z",
            "msg": f'User{[WIRELESS_CLIENT["mac"]]} disconnected from "{"ssid"}" (7m 47s connected, 448.28K bytes, last AP["80:2a:a8:00:00:01"])',
            "_id": "5ea32ff730c49e00f90dca1a",
        }
    ],
}
EVENT_CLIENT_1_WIRED_CONNECTED = {
    "meta": {"rc": "ok", "message": "events"},
    "data": [
        {
            "user": WIRELESS_CLIENT["mac"],
            "network": "LAN",
            "key": "EVT_LU_Connected",
            "subsystem": "lan",
            "site_id": WIRELESS_CLIENT["essid"],
            "time": 1587753022473,
            "datetime": "2020-04-24T18:30:22Z",
            "msg": f'User{[WIRELESS_CLIENT["mac"]]} has connected to LAN',
            "_id": "5ea3304330c49e00f90dcc35",
        }
    ],
}
EVENT_CLIENT_1_WIRED_DISCONNECTED = {
    "meta": {"rc": "ok", "message": "events"},
    "data": [
        {
            "user": WIRELESS_CLIENT["mac"],
            "hostname": WIRELESS_CLIENT["hostname"],
            "network": "LAN",
            "duration": 5,
            "bytes": 0,
            "key": "EVT_LU_Disconnected",
            "subsystem": "lan",
            "site_id": WIRELESS_CLIENT["essid"],
            "time": 1587753027000,
            "datetime": "2020-04-24T18:30:27Z",
            "msg": f'User{[WIRELESS_CLIENT["mac"]]} disconnected from "LAN" (5s connected, 0.00 bytes)',
            "_id": "5ea3318a30c49e00f90dd8c4",
        }
    ],
}
EVENT_CLIENT_1_WIRELESS_CONNECTED = {
    "meta": {"rc": "ok", "message": "events"},
    "data": [
        {
            "user": WIRELESS_CLIENT["mac"],
            "ssid": "ssid",
            "ap": "80:2a:a8:00:00:01",
            "radio": "na",
            "channel": "44",
            "hostname": WIRELESS_CLIENT["hostname"],
            "key": "EVT_WU_Connected",
            "subsystem": "wlan",
            "site_id": WIRELESS_CLIENT["essid"],
            "time": 1587753456179,
            "datetime": "2020-04-24T18:37:36Z",
            "msg": f'User{[WIRELESS_CLIENT["mac"]]} has connected to AP["80:2a:a8:00:00:01"] with "ssid" "{"ssid"}" on "channel 44(na)"',
            "_id": "5ea331fa30c49e00f90ddc1a",
        }
    ],
}


EVENT_DEVICE_CONNECTED = {
    "meta": {"rc": "ok", "message": "events"},
    "data": [
        {
            "_id": "5eae82572ab79c00f9d39b38",
            "datetime": "2020-05-03T08:35:35Z",
            "key": "EVT_SW_Connected",
            "msg": "Switch[fc:ec:da:11:22:33] was connected",
            "site_id": "5a32aa4ee4b0412345678910",
            "subsystem": "lan",
            "sw": "fc:ec:da:11:22:33",
            "sw_name": "Switch 16",
            "time": 1588494935241,
        }
    ],
}


EVENT_DEVICE_RESTARTED_UNKOWN = {
    "meta": {"rc": "ok", "message": "events"},
    "data": [
        {
            "sw": "fc:ec:da:11:22:33",
            "sw_name": "Switch 16",
            "key": "EVT_SW_RestartedUnknown",
            "subsystem": "lan",
            "site_id": "5a32aa4ee4b0412345678910",
            "time": 1588192044198,
            "datetime": "2020-04-29T20:27:24Z",
            "msg": "Switch[fc:ec:da:11:22:33] was restarted",
            "_id": "5ea9e37030c49e010363ee0b",
        }
    ],
}
EVENT_DEVICE_LOST_CONTACT = {
    "meta": {"rc": "ok", "message": "events"},
    "data": [
        {
            "_id": "5eae7fe02ab79c00f9d38960",
            "datetime": "2020-05-03T08:25:04Z",
            "key": "EVT_SW_Lost_Contact",
            "msg": "Switch[fc:ec:da:11:22:33] was disconnected",
            "site_id": "5a32aa4ee4b0412345678910",
            "subsystem": "lan",
            "sw": "fc:ec:da:11:22:33",
            "sw_name": "Switch 16",
            "time": 1588494304030,
        }
    ],
}
