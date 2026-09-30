"""Test the devices interface against captured console responses."""

import pytest

from aiounifi.network.v1.api_client import ApiClient

from .conftest import BASE_URL, SITE_ID, envelope, requests_to, url_pattern

SWITCH_ID = "90edff53-2df1-3c0a-be00-516fb6e88bdc"
AP_ID = "74c2ac6a-e9ae-38b0-8ef9-bcc96eb336fa"

# As listed by a UCG Industrial on Network 10.6.106.
SWITCH_SUMMARY = {
    "id": SWITCH_ID,
    "macAddress": "70:a7:41:65:c0:ce",
    "ipAddress": "10.8.0.188",
    "name": "USW Enterprise 8 PoE",
    "model": "USW Enterprise 8 PoE",
    "state": "ONLINE",
    "supported": True,
    "firmwareVersion": "7.5.15",
    "firmwareUpdatable": False,
    "features": ["switching"],
    "interfaces": ["ports"],
}
AP_SUMMARY = {
    "id": AP_ID,
    "macAddress": "78:45:58:e5:1a:d9",
    "ipAddress": "10.8.0.254",
    "name": "AP - Main house",
    "model": "U6 Pro",
    "state": "ONLINE",
    "supported": True,
    "firmwareVersion": "6.8.2",
    "firmwareUpdatable": False,
    "features": ["accessPoint"],
    "interfaces": ["radios"],
}
MODEM_SUMMARY = {
    "id": "bdd9bc11-2f6e-3f37-8344-e6aa15e3fae7",
    "macAddress": "8c:30:66:d2:08:94",
    "name": "Modem - Backup",
    "model": "U5G Max Outdoor",
    "state": "ONLINE",
    "supported": True,
}
SWITCH_DETAIL = {
    **SWITCH_SUMMARY,
    "adoptedAt": "2026-09-23T12:33:38Z",
    "provisionedAt": "2026-09-24T17:51:07Z",
    "configurationId": "c2bd6ccb7c5fb126",
    "uplink": {"deviceId": "72cf3194-b496-3ada-877c-6764792adc4a"},
    "features": {"switching": {"lags": []}},
    "interfaces": {
        "ports": [
            {
                "idx": 1,
                "state": "DOWN",
                "connector": "RJ45",
                "maxSpeedMbps": 2500,
                "poe": {
                    "standard": "802.3at",
                    "type": 2,
                    "enabled": True,
                    "state": "DOWN",
                },
            },
            {
                "idx": 3,
                "state": "UP",
                "connector": "RJ45",
                "maxSpeedMbps": 2500,
                "speedMbps": 100,
                "poe": {
                    "standard": "802.3at",
                    "type": 2,
                    "enabled": True,
                    "state": "UP",
                },
            },
            {"idx": 9, "state": "DOWN", "connector": "SFPPLUS", "maxSpeedMbps": 10000},
        ]
    },
}
AP_DETAIL = {
    **AP_SUMMARY,
    "adoptedAt": "2026-09-23T12:29:53Z",
    "uplink": {"deviceId": SWITCH_ID},
    "features": {"accessPoint": {}},
    "interfaces": {
        "radios": [
            {
                "wlanStandard": "802.11ax",
                "frequencyGHz": 2.4,
                "channelWidthMHz": 20,
                "channel": 11,
            },
            {
                "wlanStandard": "802.11ax",
                "frequencyGHz": 5,
                "channelWidthMHz": 80,
                "channel": 128,
            },
            {"wlanStandard": "802.11be", "frequencyGHz": 6, "channelWidthMHz": 160},
        ]
    },
}
AP_STATISTICS = {
    "uptimeSec": 8508,
    "lastHeartbeatAt": "2026-09-24T20:04:22Z",
    "nextHeartbeatAt": "2026-09-24T20:04:44Z",
    "loadAverage1Min": 0.24,
    "loadAverage5Min": 0.13,
    "loadAverage15Min": 0.1,
    "cpuUtilizationPct": 8.0,
    "memoryUtilizationPct": 58.7,
    "uplink": {"txRateBps": 531296, "rxRateBps": 45032},
    "interfaces": {
        "radios": [
            {"frequencyGHz": 2.4, "txRetriesPct": 0.0},
            {"frequencyGHz": 5, "txRetriesPct": 1.5},
        ]
    },
}


async def test_update_keys_devices_by_mac(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Devices are cached by MAC, in any spelling."""
    mock_aioresponse.get(
        url_pattern(f"/v1/sites/{SITE_ID}/devices"),
        payload=envelope([SWITCH_SUMMARY, AP_SUMMARY, MODEM_SUMMARY]),
    )
    devices = network_client_with_site.devices

    await devices.update()

    assert len(devices.items()) == 3
    switch = devices["70-A7-41-65-C0-CE"]
    assert "70a7416 5c0ce".replace(" ", "") in devices
    assert switch.device_id == SWITCH_ID
    assert switch.mac_address == "70:a7:41:65:c0:ce"
    assert switch.name == "USW Enterprise 8 PoE"
    assert switch.model == "USW Enterprise 8 PoE"
    assert switch.state == "ONLINE"
    assert switch.supported is True
    assert switch.ip_address == "10.8.0.188"
    assert switch.firmware_version == "7.5.15"
    assert switch.firmware_updatable is False
    assert switch.features == ["switching"]
    assert switch.ports == []
    assert switch.radios == []
    assert switch.uplink_device_id is None
    assert switch.adopted_at is None

    modem = devices["8c:30:66:d2:08:94"]
    assert modem.ip_address is None
    assert modem.firmware_version is None
    assert modem.firmware_updatable is False
    assert modem.features == []


async def test_get_details_fills_ports_and_updates_cache(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """The detail endpoint returns a bare object with ports and uplink."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/sites/{SITE_ID}/devices/{SWITCH_ID}", payload=SWITCH_DETAIL
    )
    devices = network_client_with_site.devices

    switch = await devices.get_details(SWITCH_ID)

    assert switch.features == ["switching"]
    assert switch.uplink_device_id == "72cf3194-b496-3ada-877c-6764792adc4a"
    assert switch.adopted_at == "2026-09-23T12:33:38Z"
    assert [port["idx"] for port in switch.ports] == [1, 3, 9]
    assert switch.ports[1]["speedMbps"] == 100
    assert switch.ports[1]["poe"]["state"] == "UP"
    assert "poe" not in switch.ports[2]
    assert switch.radios == []
    assert devices["70:a7:41:65:c0:ce"].ports == switch.ports


async def test_get_details_radios(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Access points carry radios instead of ports."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/sites/{SITE_ID}/devices/{AP_ID}", payload=AP_DETAIL
    )

    access_point = await network_client_with_site.devices.get_details(AP_ID)

    assert [radio.get("channel") for radio in access_point.radios] == [11, 128, None]
    assert access_point.ports == []
    assert access_point.features == ["accessPoint"]


async def test_get_statistics(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Statistics come back as a bare object."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/sites/{SITE_ID}/devices/{AP_ID}/statistics/latest",
        payload=AP_STATISTICS,
    )

    statistics = await network_client_with_site.devices.get_statistics(AP_ID)

    assert statistics.uptime_sec == 8508
    assert statistics.last_heartbeat_at == "2026-09-24T20:04:22Z"
    assert statistics.cpu_utilization_pct == 8.0
    assert statistics.memory_utilization_pct == 58.7
    assert statistics.load_average_1min == 0.24
    assert statistics.uplink_tx_rate_bps == 531296
    assert statistics.uplink_rx_rate_bps == 45032
    assert statistics.radios[1]["txRetriesPct"] == 1.5


async def test_statistics_without_optional_blocks(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """A device that reports only the heartbeat."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/sites/{SITE_ID}/devices/{AP_ID}/statistics/latest",
        payload={
            "uptimeSec": 1,
            "lastHeartbeatAt": "2026-09-24T20:04:22Z",
            "nextHeartbeatAt": "2026-09-24T20:04:44Z",
        },
    )

    statistics = await network_client_with_site.devices.get_statistics(AP_ID)

    assert statistics.cpu_utilization_pct is None
    assert statistics.memory_utilization_pct is None
    assert statistics.load_average_1min is None
    assert statistics.uplink_tx_rate_bps is None
    assert statistics.uplink_rx_rate_bps is None
    assert statistics.radios == []


async def test_list_page_with_filter(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Server-side filtering by MAC."""
    mock_aioresponse.get(
        url_pattern(f"/v1/sites/{SITE_ID}/devices"), payload=envelope([SWITCH_SUMMARY])
    )

    devices = await network_client_with_site.devices.list_page(
        filter_value="macAddress.eq('70:a7:41:65:c0:ce')"
    )

    assert [device.device_id for device in devices] == [SWITCH_ID]
    (call,) = requests_to(mock_aioresponse, "get", "/devices")
    assert call.kwargs["params"]["filter"] == "macAddress.eq('70:a7:41:65:c0:ce')"


async def test_restart(mock_aioresponse, network_client_with_site: ApiClient) -> None:
    """Restart posts the only action the console accepts for devices."""
    mock_aioresponse.post(
        f"{BASE_URL}/v1/sites/{SITE_ID}/devices/{SWITCH_ID}/actions", body=b""
    )

    await network_client_with_site.devices.restart(SWITCH_ID)

    (call,) = requests_to(mock_aioresponse, "post", "/actions")
    assert call.kwargs["data"] == b'{"action":"RESTART"}'


async def test_power_cycle_port(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Power cycle posts the only action the console accepts for ports."""
    mock_aioresponse.post(
        f"{BASE_URL}/v1/sites/{SITE_ID}/devices/{SWITCH_ID}/interfaces/ports/3/actions",
        body=b"",
    )

    await network_client_with_site.devices.power_cycle_port(SWITCH_ID, 3)

    (call,) = requests_to(mock_aioresponse, "post", "/ports/3/actions")
    assert call.kwargs["data"] == b'{"action":"POWER_CYCLE"}'


@pytest.mark.parametrize("mac", ["70:a7:41:65:c0", "zz:zz:zz:zz:zz:zz"])
def test_invalid_mac_lookup(network_client: ApiClient, mac: str) -> None:
    """A malformed MAC is a ValueError, not a silent miss."""
    with pytest.raises(ValueError, match="Invalid MAC address"):
        _ = mac in network_client.devices
