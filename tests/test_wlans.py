"""Test wlan configuration API.

pytest --cov-report term-missing --cov=aiounifi.wlan tests/test_wlans.py
"""

import pytest
from asynctest import Mock

from aiounifi.wlan import Wlans


def test_ports():
    """Test that different types of ports work."""
    wlans = Wlans(fixture_wlans, Mock())
    print(wlans)
    assert False
    assert len(wlans.values()) == 2

    key = "SSID 1"
    assert wlans[key].id == '012345678910111213141516'
    assert wlans[key].bc_filter_enabled == False
    assert wlans[key].bc_filter_list == []
    assert wlans[key].dtim_mode == 'default'
    assert wlans[key].dtim_na == 1
    assert wlans[key].dtim_ng == 1
    assert wlans[key].enabled == True
    assert wlans[key].group_rekey == 3600
    assert wlans[key].is_guest is False
    assert wlans[key].mac_filter_enabled == False
    assert wlans[key].mac_filter_list == []
    assert wlans[key].mac_filter_policy == 'allow'
    assert wlans[key].minrate_na_advertising_rates == False
    assert wlans[key].minrate_na_beacon_rate_kbps == 6000
    assert wlans[key].minrate_na_data_rate_kbps == 6000
    assert wlans[key].minrate_na_enabled == False
    assert wlans[key].minrate_na_mgmt_rate_kbps == 6000
    assert wlans[key].minrate_ng_advertising_rates == False
    assert wlans[key].minrate_ng_beacon_rate_kbps == 1000
    assert wlans[key].minrate_ng_cck_rates_enabled is False
    assert wlans[key].minrate_ng_data_rate_kbps == 1000
    assert wlans[key].minrate_ng_enabled == False
    assert wlans[key].minrate_ng_mgmt_rate_kbps == 1000
    assert wlans[key].name == 'SSID 1'
    assert wlans[key].no2ghz_oui == False
    assert wlans[key].schedule == []
    assert wlans[key].security == 'wpapsk'
    assert wlans[key].site_id == '012345678910111213141517'
    assert wlans[key].usergroup_id == '012345678910111213141518'
    assert wlans[key].wep_idx == 1
    assert wlans[key].wlangroup_id == '012345678910111213141519'
    assert wlans[key].wpa_enc == 'ccmp'
    assert wlans[key].wpa_mode == 'wpa2'
    assert wlans[key].x_iapp_key == '01234567891011121314151617181920'
    assert wlans[key].x_passphrase == 'password in clear text'


def test_no_ports():
    """Test that no ports also work."""
    mock_request = Mock()
    mock_request.return_value = ''
    wlans = Wlans("", mock_request)
    wlans.update()

    mock_request.assert_called_once

    assert len(wlans.values()) == 0



fixture_wlans = [
    {
        '_id': '012345678910111213141516',
        'bc_filter_enabled': False,
        'bc_filter_list': [],
        'dtim_mode': 'default',
        'dtim_na': 1,
        'dtim_ng': 1,
        'enabled': True,
        'group_rekey': 3600,
        'mac_filter_enabled': False,
        'mac_filter_list': [],
        'mac_filter_policy': 'allow',
        'minrate_na_advertising_rates': False,
        'minrate_na_beacon_rate_kbps': 6000,
        'minrate_na_data_rate_kbps': 6000,
        'minrate_na_enabled': False,
        'minrate_na_mgmt_rate_kbps': 6000,
        'minrate_ng_advertising_rates': False,
        'minrate_ng_beacon_rate_kbps': 1000,
        'minrate_ng_data_rate_kbps': 1000,
        'minrate_ng_enabled': False,
        'minrate_ng_mgmt_rate_kbps': 1000,
        'name': 'SSID 1',
        'no2ghz_oui': False,
        'schedule': [],
        'security': 'wpapsk',
        'site_id': '012345678910111213141517',
        'usergroup_id': '012345678910111213141518',
        'wep_idx': 1,
        'wlangroup_id': '012345678910111213141519',
        'wpa_enc': 'ccmp',
        'wpa_mode': 'wpa2',
        'x_iapp_key': '01234567891011121314151617181920',
        'x_passphrase': 'password in clear text'
    },
    {
        '_id': '123456789101112161415160',
        'bc_filter_enabled': True,
        'bc_filter_list': [],
        'dtim_mode': 'default',
        'dtim_na': 1,
        'dtim_ng': 1,
        'enabled': False,
        'group_rekey': 3600,
        'is_guest': True,
        'mac_filter_enabled': False,
        'mac_filter_list': [],
        'mac_filter_policy': 'allow',
        'minrate_na_advertising_rates': False,
        'minrate_na_beacon_rate_kbps': 6000,
        'minrate_na_data_rate_kbps': 6000,
        'minrate_na_enabled': False,
        'minrate_na_mgmt_rate_kbps': 6000,
        'minrate_ng_advertising_rates': False,
        'minrate_ng_beacon_rate_kbps': 1000,
        'minrate_ng_cck_rates_enabled': True,
        'minrate_ng_data_rate_kbps': 1000,
        'minrate_ng_enabled': False,
        'minrate_ng_mgmt_rate_kbps': 1000,
        'name': 'SSID 2',
        'schedule': [],
        'security': 'wpapsk',
        'site_id': '123456789101112161415161',
        'usergroup_id': '123456789101112161415162',
        'wep_idx': 1,
        'wlangroup_id': '123456789101112161415163',
        'wpa_enc': 'ccmp',
        'wpa_mode': 'wpa2',
        'x_iapp_key': '12345678910111216141516171819204',
        'x_passphrase': 'password in clear text'
    }
]
