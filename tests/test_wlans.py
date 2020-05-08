"""Test wlan configuration API.

pytest --cov-report term-missing --cov=aiounifi.wlan tests/test_wlans.py
"""

from asyncio import Future
from asynctest import MagicMock

from aiounifi.wlan import Wlans

from fixtures import WLANS


async def test_no_ports():
    """Test that no ports also work."""
    mock_requests = MagicMock(return_value=Future())
    mock_requests.return_value.set_result("")
    wlans = Wlans([], mock_requests)
    await wlans.update()

    mock_requests.assert_called_once
    assert len(wlans.values()) == 0


async def test_ports():
    """Test that different types of ports work."""
    mock_requests = MagicMock(return_value=Future())
    mock_requests.return_value.set_result("")
    wlans = Wlans(WLANS, mock_requests)

    assert len(wlans.values()) == 2

    wlan = wlans["SSID 1"]
    assert wlan.id == "wlan_id_1"
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
    assert wlan.x_iapp_key == "wlan_id_117181920"
    assert wlan.x_passphrase == "password in clear text"

    await wlans.async_enable(wlan)
    mock_requests.assert_called_with(
        "put", "/rest/wlanconf/wlan_id_1", json={"enabled": True}
    )

    await wlans.async_disable(wlan)
    mock_requests.assert_called_with(
        "put", "/rest/wlanconf/wlan_id_1", json={"enabled": False}
    )
