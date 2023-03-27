"""Test wlan configuration API.

pytest --cov-report term-missing --cov=aiounifi.wlan tests/test_wlans.py
"""

import pytest

from aiounifi.models.wlan import (
    WlanChangePasswordRequest,
    WlanEnableRequest,
    wlan_qr_code,
)

from .fixtures import WLANS


async def test_wlan_password_change(
    mock_aioresponse, unifi_controller, unifi_called_with
):
    """Test changing Wlan password."""
    mock_aioresponse.put(
        "https://host:8443/api/s/default/rest/wlanconf/123", payload={}
    )

    await unifi_controller.request(WlanChangePasswordRequest.create("123", "456"))

    assert unifi_called_with(
        "put",
        "/api/s/default/rest/wlanconf/123",
        json={"x_passphrase": "456"},
    )


@pytest.mark.parametrize("enable", [True, False])
async def test_wlan_enable(
    mock_aioresponse, unifi_controller, unifi_called_with, enable
):
    """Test that wlan can be enabled and disabled."""
    mock_aioresponse.put(
        "https://host:8443/api/s/default/rest/wlanconf/123", payload={}
    )

    await unifi_controller.request(WlanEnableRequest.create("123", enable))

    assert unifi_called_with(
        "put",
        "/api/s/default/rest/wlanconf/123",
        json={"enabled": enable},
    )


def test_wlan_qr_code():
    """Test that wlan can be enabled and disabled."""
    assert (
        wlan_qr_code("ssid", "passphrase")
        == b'<?xml version="1.0" encoding="utf-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="132" height="132" class="segno"><path transform="scale(4)" class="qrline" stroke="#000" d="M4 4.5h7m2 0h2m5 0h1m1 0h7m-25 1h1m5 0h1m3 0h1m2 0h1m4 0h1m5 0h1m-25 1h1m1 0h3m1 0h1m2 0h4m1 0h3m1 0h1m1 0h3m1 0h1m-25 1h1m1 0h3m1 0h1m1 0h3m5 0h1m1 0h1m1 0h3m1 0h1m-25 1h1m1 0h3m1 0h1m1 0h1m1 0h2m2 0h1m1 0h1m1 0h1m1 0h3m1 0h1m-25 1h1m5 0h1m2 0h1m6 0h1m1 0h1m5 0h1m-25 1h7m1 0h1m1 0h1m1 0h1m1 0h1m1 0h1m1 0h7m-15 1h1m1 0h1m-13 1h2m3 0h3m4 0h2m6 0h2m-22 1h3m4 0h1m1 0h1m1 0h1m1 0h1m1 0h1m2 0h5m1 0h1m-19 1h1m1 0h1m3 0h2m1 0h2m1 0h1m2 0h4m-24 1h5m1 0h1m2 0h3m2 0h1m1 0h2m2 0h1m1 0h2m-25 1h1m2 0h2m1 0h2m1 0h3m3 0h1m1 0h2m1 0h4m-24 1h3m2 0h1m5 0h1m2 0h4m1 0h1m2 0h1m1 0h1m-25 1h1m2 0h2m1 0h1m1 0h1m1 0h1m1 0h1m2 0h2m2 0h2m2 0h2m-25 1h1m1 0h1m4 0h1m4 0h1m1 0h4m1 0h2m1 0h2m-24 1h1m1 0h5m3 0h11m1 0h3m-17 1h1m1 0h2m3 0h2m3 0h1m1 0h3m-25 1h7m1 0h2m1 0h4m1 0h1m1 0h1m1 0h2m2 0h1m-25 1h1m5 0h1m1 0h1m1 0h1m1 0h1m1 0h3m3 0h2m2 0h1m-25 1h1m1 0h3m1 0h1m2 0h2m2 0h8m3 0h1m-25 1h1m1 0h3m1 0h1m2 0h1m1 0h1m5 0h6m-23 1h1m1 0h3m1 0h1m2 0h2m2 0h1m1 0h5m1 0h1m2 0h1m-25 1h1m5 0h1m1 0h2m1 0h2m1 0h3m1 0h1m1 0h1m3 0h1m-25 1h7m1 0h1m1 0h2m3 0h2m2 0h1m4 0h1"/></svg>\n'
    )


async def test_no_wlans(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test that no ports also work."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )

    wlans = unifi_controller.wlans
    await wlans.update()

    assert unifi_called_with("get", "/api/s/default/rest/wlanconf")
    assert len(wlans.values()) == 0


async def test_wlans(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test that different types of ports work."""
    wlans = unifi_controller.wlans
    wlans.process_raw(WLANS)

    assert len(wlans.values()) == 2

    wlan = wlans["SSID 1"]
    assert wlan.id == "012345678910111213141516"
    assert wlan.bc_filter_enabled is False
    assert wlan.bc_filter_list == []
    assert wlan.dtim_mode == "default"
    assert wlan.dtim_na == 1
    assert wlan.dtim_ng == 1
    assert wlan.enabled is True
    assert wlan.group_rekey == 3600
    assert wlan.is_guest is None
    assert wlan.mac_filter_enabled is False
    assert wlan.mac_filter_list == []
    assert wlan.mac_filter_policy == "allow"
    assert wlan.minrate_na_advertising_rates is False
    assert wlan.minrate_na_beacon_rate_kbps == 6000
    assert wlan.minrate_na_data_rate_kbps == 6000
    assert wlan.minrate_na_enabled is False
    assert wlan.minrate_na_mgmt_rate_kbps == 6000
    assert wlan.minrate_ng_advertising_rates is False
    assert wlan.minrate_ng_beacon_rate_kbps == 1000
    assert wlan.minrate_ng_cck_rates_enabled is None
    assert wlan.minrate_ng_data_rate_kbps == 1000
    assert wlan.minrate_ng_enabled is False
    assert wlan.minrate_ng_mgmt_rate_kbps == 1000
    assert wlan.name == "SSID 1"
    assert wlan.name_combine_enabled is None
    assert wlan.name_combine_suffix == None
    assert wlan.no2ghz_oui is False
    assert wlan.schedule == []
    assert wlan.security == "wpapsk"
    assert wlan.site_id == "5a32aa4ee4b0412345678910"
    assert wlan.usergroup_id == "012345678910111213141518"
    assert wlan.wep_idx == 1
    assert wlan.wlangroup_id == "012345678910111213141519"
    assert wlan.wpa_enc == "ccmp"
    assert wlan.wpa_mode == "wpa2"
    assert wlan.x_iapp_key == "01234567891011121314151617181920"
    assert wlan.x_passphrase == "password in clear text"

    mock_aioresponse.put(
        "https://host:8443/api/s/default/rest/wlanconf/012345678910111213141516",
        payload={},
        repeat=True,
    )

    await wlans.enable(wlan)
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/wlanconf/012345678910111213141516",
        json={"enabled": True},
    )

    await wlans.disable(wlan)
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/wlanconf/012345678910111213141516",
        json={"enabled": False},
    )

    assert (
        wlans.generate_wlan_qr_code(wlan)
        == b'<?xml version="1.0" encoding="utf-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="148" height="148" class="segno"><path transform="scale(4)" class="qrline" stroke="#000" d="M4 4.5h7m2 0h1m6 0h1m2 0h2m1 0h7m-29 1h1m5 0h1m1 0h2m1 0h2m1 0h2m2 0h1m3 0h1m5 0h1m-29 1h1m1 0h3m1 0h1m2 0h3m2 0h3m1 0h2m2 0h1m1 0h3m1 0h1m-29 1h1m1 0h3m1 0h1m1 0h2m1 0h1m1 0h2m2 0h1m1 0h2m1 0h1m1 0h3m1 0h1m-29 1h1m1 0h3m1 0h1m3 0h1m1 0h1m3 0h1m1 0h2m2 0h1m1 0h3m1 0h1m-29 1h1m5 0h1m1 0h1m1 0h1m4 0h2m1 0h1m3 0h1m5 0h1m-29 1h7m1 0h1m1 0h1m1 0h1m1 0h1m1 0h1m1 0h1m1 0h1m1 0h7m-17 1h1m1 0h1m-15 1h5m1 0h5m1 0h4m1 0h1m2 0h2m1 0h1m1 0h1m1 0h1m-27 1h3m1 0h1m2 0h2m4 0h1m1 0h1m3 0h1m1 0h1m1 0h1m1 0h2m-23 1h2m1 0h2m1 0h3m1 0h1m1 0h2m1 0h4m1 0h1m-25 1h3m3 0h5m3 0h1m3 0h1m1 0h2m1 0h1m2 0h2m-27 1h1m3 0h4m1 0h3m1 0h1m1 0h1m1 0h2m2 0h4m-26 1h2m1 0h2m3 0h2m1 0h1m6 0h1m3 0h2m1 0h2m-28 1h1m2 0h4m1 0h1m1 0h1m1 0h1m2 0h1m1 0h2m1 0h2m1 0h1m2 0h1m-25 1h2m1 0h1m2 0h1m1 0h1m1 0h1m3 0h1m5 0h1m2 0h1m-26 1h1m3 0h3m1 0h3m1 0h3m2 0h1m2 0h1m2 0h1m1 0h1m1 0h2m-29 1h3m1 0h2m2 0h1m1 0h1m1 0h1m1 0h1m1 0h1m2 0h1m4 0h2m1 0h1m-28 1h1m3 0h3m1 0h1m1 0h1m3 0h4m3 0h1m1 0h2m-25 1h1m2 0h3m5 0h2m2 0h1m6 0h1m1 0h1m3 0h1m-29 1h1m4 0h3m1 0h3m1 0h2m2 0h1m2 0h7m-19 1h5m3 0h3m1 0h1m3 0h1m1 0h1m-27 1h7m1 0h1m5 0h2m1 0h1m1 0h2m1 0h1m1 0h1m1 0h1m-27 1h1m5 0h1m3 0h3m1 0h2m4 0h1m3 0h2m1 0h2m-29 1h1m1 0h3m1 0h1m1 0h1m1 0h2m1 0h3m1 0h1m2 0h6m2 0h1m-29 1h1m1 0h3m1 0h1m1 0h2m1 0h4m9 0h2m1 0h2m-29 1h1m1 0h3m1 0h1m1 0h1m3 0h1m2 0h1m1 0h3m1 0h1m1 0h5m-28 1h1m5 0h1m1 0h1m1 0h1m4 0h2m1 0h1m2 0h2m1 0h2m1 0h1m-28 1h7m1 0h1m1 0h1m2 0h3m1 0h1m1 0h1m4 0h2"/></svg>\n'
    )
