"""Test controller.

pytest --cov-report term-missing --cov=aiounifi.controller tests/test_controller.py
"""

import asyncio
from asynctest import MagicMock, Mock
import pytest

from aiounifi.controller import Controller
from aiounifi.clients import (
    Clients,
    URL as client_url,
    ClientsAll,
    URL_ALL as all_client_url,
)
from aiounifi.devices import Devices, URL as device_url
from aiounifi.wlan import Wlans, URL as wlan_url

HOST = "127.0.0.1"
PORT = "80"
USERNAME = "user"
PASSWORD = "password"


@pytest.fixture
def controller() -> Controller:
    """Returns the session object."""
    session = MagicMock()
    return Controller(HOST, session, username=USERNAME, password=PASSWORD)


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


async def test_controller(controller, loop):
    """Test controller communicating with a UniFi controller"""

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
        "https://127.0.0.1:8443/",
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


async def test_unifios_controller(controller, loop):
    """Test controller communicating with a UniFi OS controller"""

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
        "https://127.0.0.1:8443/",
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

WLAN_UNIFIOS_RESPONSE = {
    "meta": {"rc": "ok"},
    "data": [
        {
            "_id": "5e231d8e931eb902acf25117",
            "enabled": True,
            "name": "Wi-Fi Network",
            "security": "wpapsk",
            "wpa_enc": "ccmp",
            "wpa_mode": "wpa2",
            "x_passphrase": "password",
            "wlangroup_id": "5e231c14931eb902acf25113",
            "name_combine_enabled": False,
            "name_combine_suffix": "_2G",
            "site_id": "5e231c10931eb902acf25112",
            "x_iapp_key": "2a71691714511b8e496c0062565d111a",
            "no2ghz_oui": False,
            "minrate_ng_enabled": True,
            "minrate_ng_beacon_rate_kbps": 6000,
            "minrate_ng_data_rate_kbps": 6000,
            "wep_idx": 1,
            "usergroup_id": "5e231c14931eb902acf25112",
            "dtim_mode": "default",
            "dtim_ng": 1,
            "dtim_na": 1,
            "minrate_ng_advertising_rates": False,
            "minrate_ng_cck_rates_enabled": True,
            "minrate_na_enabled": False,
            "minrate_na_advertising_rates": False,
            "minrate_na_data_rate_kbps": 6000,
            "mac_filter_enabled": False,
            "mac_filter_policy": "allow",
            "mac_filter_list": [],
            "bc_filter_enabled": False,
            "bc_filter_list": [],
            "group_rekey": 3600,
            "radius_das_enabled": False,
            "schedule": [],
            "minrate_ng_mgmt_rate_kbps": 6000,
            "minrate_na_mgmt_rate_kbps": 6000,
            "minrate_na_beacon_rate_kbps": 6000,
        }
    ],
}

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
