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
        == b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x84\x00\x00\x00"
        + b"\x84\x01\x00\x00\x00\x00y?\xbe\n\x00\x00\x00\xc4IDATx\xda\xedV\xcb"
        + b"\r\xc3P\x0cB]\xc0\xfbo\xc9\x06\x14\xfcri\x0fUUz\x8c\xf3\xd1\x93\xa5"
        + b" \x8c\xb1\x15\xe8-\x88;\xf3\x9a\x010\x1cir\x10\x1fx\x8fo2\xc6\t\x84"
        + b"\x86\xd7\xa1\xc0\xc1\x0c\x91\xb7\xef\x12\x07\xe1\xf2\x07\x9c\x81\xa6"
        + b"\xc6\xd1\xaac\xa0N\x9f\xb4i\xa3\xec\xd7F\xc8\x1c'\xfc\xce\xe7\xb8H"
        + b"\xe7)p\\LB\xe8t>U\x81\xeb\xa2\x02\x87\x80\xb9\x0c\x99\xbb\xe9;\x07V"
        + b"\xc8 \x8bZ\xe8c\xf7D\x1djJ>\t\xee\xd5\xe0\xf8\xe3\xdd\x1a.L\xd5|\xb9M{"
        + b"\x9e\xda\xcff\xe2\x9a:\x9c%\xc2k\xe8\xcby\xdf\xa5!\xf4\xfb\xd0^\x8eL5"
        + b"\x0e\xd7\xd7\xa3\x9e\xcf\x8eG\xabO\xbcc\x8d\xfa}\x98\xbe\xb3\xdb\xab"
        + b"\xf7_\xc1\x87\xcc\x13u:\xfe\x00\xeaq\xcby\x00\x00\x00\x00IEND\xaeB`\x82"
    )


async def test_no_wlans(unifi_controller, _mock_endpoints, unifi_called_with):
    """Test that no ports also work."""
    wlans = unifi_controller.wlans
    await wlans.update()

    assert unifi_called_with("get", "/api/s/default/rest/wlanconf")
    assert len(wlans.values()) == 0


@pytest.mark.parametrize("wlan_payload", [WLANS])
async def test_wlans(
    mock_aioresponse, unifi_controller, _mock_endpoints, unifi_called_with
):
    """Test that different types of ports work."""
    wlans = unifi_controller.wlans
    await wlans.update()
    assert len(wlans.values()) == 2

    wlan = wlans["012345678910111213141516"]
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
    assert wlan.name_combine_suffix is None
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
        == b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x94\x00\x00\x00"
        + b"\x94\x01\x00\x00\x00\x00]G=y\x00\x00\x00\xf6IDATx\xda\xed\x96A\x0eBA"
        + b"\x08C\x89\x17\xe0\xfe\xb7\xec\r\xb0\x0f\xbf+7\xeat\xf9\tF2\x8b\xa6C"
        + b"\x99\xf2k>Bu\x9f\xfdrVU-\xd7\xad\xa6\x1c=\xea3\xbe=3^;\xcbX.(\xcf\xf1"
        + b"\xaa\xdb<\x0bD\x97\x11\xbc\x92\xda\x19\xc3\x1b2\xc5\xcf\tL\x87\xfa\x87"
        + b"\xa8WD\xf4}\x85\xd9\xbdg\xe8\x98_oj\xac\x8a\xce\xf1\x04\xd2\x12\xe4\xc6"
        + b"\x13\xb8\xaf\x87YL\x0c\x1c\x13\xfc\x9c\xfe\r\x03\xa8\x80\x1e\xed\x16"
        + b"\xc2\xcf#my\xcf\xf9\xb9i\x0c\x1f\x0c\x13\xfd\x83\x95\x83\xfei\x02\xfc"
        + b"\x06\x98\xebq$\xf4h\xac\xa5\xf1\xc0\xa6\x87\xe7\xf3\x8c\x11\xec\x8d"
        + b"\x97j\x84_\xa31\x033\x11=\x10Y\xafG\x9c\xf0+1~\x06\\{\x89\xf8\x0b@"
        + b"\x97\xadf\xfc\x0f)\x84(\x13\xf1\xe7\x15\x99?e\xf6\xc7\x1a\x0cL'\xb5"
        + b"\xdfj\xfd9\xc6\x8f\xb7\xe1\x0eVMp\xbf\xad#\x84\xf6\x1b\xec\x06\xdf"
        + b"\x0f\xed\xb7\xfb;\xf1\xaf\xb3'\x1b6\x8f;\x0f\x90\xd4i\x00\x00\x00"
        + b"\x00IEND\xaeB`\x82"
    )
