"""Test wlan configuration API.

pytest --cov-report term-missing --cov=aiounifi.wlan tests/test_wlans.py
"""
from copy import deepcopy

from .fixtures import WLANS


async def test_no_ports(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test that no ports also work."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )

    wlans = unifi_controller.wlans
    await wlans.update()

    assert unifi_called_with("get", "/api/s/default/rest/wlanconf")
    assert len(wlans.values()) == 0


async def test_ports(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test that different types of ports work."""
    wlans = unifi_controller.wlans
    wlans.process_raw(deepcopy(WLANS))

    assert len(wlans.values()) == 2

    wlan = wlans["SSID 1"]
    assert wlan.id == "012345678910111213141516"
    assert wlan.bc_filter_enabled == False
    assert wlan.bc_filter_list == []
    assert wlan.dtim_mode == "default"
    assert wlan.dtim_na == 1
    assert wlan.dtim_ng == 1
    assert wlan.enabled is True
    assert wlan.group_rekey == 3600
    assert wlan.is_guest is False
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
    assert wlan.minrate_ng_cck_rates_enabled is False
    assert wlan.minrate_ng_data_rate_kbps == 1000
    assert wlan.minrate_ng_enabled is False
    assert wlan.minrate_ng_mgmt_rate_kbps == 1000
    assert wlan.name == "SSID 1"
    assert wlan.name_combine_enabled is True
    assert wlan.name_combine_suffix == ""
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
