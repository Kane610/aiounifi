"""Test client configuration API.

pytest --cov-report term-missing --cov=aiounifi.devices tests/test_devices.py
"""

import pytest

from aiounifi.models.device import (
    DevicePowerCyclePortRequest,
    DeviceRestartRequest,
    DeviceSetOutletCycleEnabledRequest,
    DeviceSetOutletRelayRequest,
    DeviceSetPoePortModeRequest,
    DeviceUpgradeRequest,
)

from .fixtures import (
    ACCESS_POINT_AC_PRO,
    GATEWAY_USG3,
    PDU_PRO,
    PLUG_UP1,
    STRIP_UP6,
    SWITCH_16_PORT_POE,
)

test_data = [
    ([{"mac": "0", "disabled": True}], {"mac": "0", "disabled": True}),
    (
        [ACCESS_POINT_AC_PRO],
        {
            "board_revision": 21,
            "considered_lost_at": 1588175837,
            "disabled": False,
            "id": "235678987654345678",
            "ip": "192.168.0.4",
            "downlink_table": [],
            "fan_level": None,
            "has_fan": False,
            "last_seen": 1588175726,
            "lldp_table": [],
            "mac": "80:2a:a8:00:01:02",
            "model": "U7PG2",
            "name": "ACCESS POINT AC PRO",
            "next_heartbeat_at": 1588175763,
            "overheating": False,
            "port_overrides": [],
            "port_table": ACCESS_POINT_AC_PRO["port_table"],
            "state": 1,
            "sys_stats": {
                "loadavg_1": "0.15",
                "loadavg_15": "0.02",
                "loadavg_5": "0.08",
                "mem_buffer": 0,
                "mem_total": 128622592,
                "mem_used": 63606784,
            },
            "type": "uap",
            "version": "4.0.69.10871",
            "upgradable": True,
            "upgrade_to_firmware": "4.0.80.10875",
            "uplink": ACCESS_POINT_AC_PRO["uplink"],
            "uplink_depth": None,
            "user_num_sta": 12,
            "wlan_overrides": [
                {
                    "name": "My5GHzSSID1",
                    "radio": "na",
                    "radio_name": "wifi1",
                    "wlan_id": "012345678910111213141516",
                },
            ],
        },
    ),
    (
        [GATEWAY_USG3],
        {
            "board_revision": 16,
            "considered_lost_at": 1588175842,
            "disabled": False,
            "id": "235678987654345678",
            "ip": "1.2.3.4",
            "downlink_table": [],
            "fan_level": None,
            "has_fan": False,
            "last_seen": 1588175740,
            "lldp_table": [],
            "mac": "78:8a:20:33:44:55",
            "model": "UGW3",
            "name": "USG",
            "next_heartbeat_at": 1588175774,
            "overheating": False,
            "port_overrides": [],
            "port_table": GATEWAY_USG3["port_table"],
            "state": 1,
            "sys_stats": {
                "loadavg_1": "0.03",
                "loadavg_15": "0.08",
                "loadavg_5": "0.07",
                "mem_buffer": 57561088,
                "mem_total": 507412480,
                "mem_used": 293453824,
            },
            "type": "ugw",
            "version": "4.4.44.5213844",
            "upgradable": True,
            "upgrade_to_firmware": "4.4.50.5272448",
            "uplink": GATEWAY_USG3["uplink"],
            "uplink_depth": None,
            "user_num_sta": 20,
            "wlan_overrides": [],
        },
    ),
    (
        [PLUG_UP1],
        {
            "board_revision": 2,
            "downlink_table": [],
            "id": "600c8356942a6ade50707b56",
            "ip": "192.168.0.189",
            "has_fan": False,
            "last_seen": 1642055273,
            "lldp_table": [],
            "mac": "fc:ec:da:76:4f:5f",
            "model": "UP1",
            "name": "Plug",
            "next_interval": 40,
            "outlet_table": [
                {
                    "index": 1,
                    "has_relay": True,
                    "has_metering": False,
                    "relay_state": False,
                    "name": "Outlet 1",
                }
            ],
            "outlet_overrides": [],
            "port_table": [],
            "state": 1,
            "sys_stats": {"mem_total": 98304, "mem_used": 87736},
            "type": "uap",
            "version": "2.2.1.511",
            "upgradable": False,
            "uplink": PLUG_UP1["uplink"],
        },
    ),
    (
        [STRIP_UP6],
        {
            "board_revision": 5,
            "downlink_table": [],
            "id": "61eb1a75942a6a859b45d2bc",
            "ip": "192.168.0.138",
            "has_fan": False,
            "last_seen": 1642800247,
            "lldp_table": [],
            "mac": "78:45:58:fc:16:7d",
            "model": "UP6",
            "name": "",
            "next_interval": 41,
            "outlet_table": [
                {
                    "index": 1,
                    "has_relay": True,
                    "has_metering": False,
                    "relay_state": False,
                    "cycle_enabled": False,
                    "name": "Outlet 1",
                },
                {
                    "index": 2,
                    "has_relay": True,
                    "has_metering": False,
                    "relay_state": False,
                    "cycle_enabled": False,
                    "name": "Outlet 2",
                },
                {
                    "index": 3,
                    "has_relay": True,
                    "has_metering": False,
                    "relay_state": True,
                    "cycle_enabled": False,
                    "name": "Outlet 3",
                },
                {
                    "index": 4,
                    "has_relay": True,
                    "has_metering": False,
                    "relay_state": True,
                    "cycle_enabled": True,
                    "name": "Outlet 4",
                },
                {
                    "index": 5,
                    "has_relay": True,
                    "has_metering": False,
                    "relay_state": False,
                    "cycle_enabled": False,
                    "name": "Outlet 5",
                },
                {
                    "index": 6,
                    "has_relay": True,
                    "has_metering": False,
                    "relay_state": False,
                    "cycle_enabled": False,
                    "name": "Outlet 6",
                },
                {
                    "index": 7,
                    "has_relay": True,
                    "has_metering": False,
                    "relay_state": False,
                    "cycle_enabled": False,
                    "name": "USB Outlets",
                },
            ],
            "outlet_overrides": [
                {
                    "index": 1,
                    "name": "Outlet 1",
                    "cycle_enabled": False,
                    "relay_state": False,
                },
                {
                    "index": 2,
                    "name": "Outlet 2",
                    "cycle_enabled": False,
                    "relay_state": False,
                },
                {
                    "index": 3,
                    "name": "Outlet 3",
                    "cycle_enabled": False,
                    "relay_state": True,
                },
                {
                    "index": 4,
                    "name": "Outlet 4",
                    "cycle_enabled": True,
                    "relay_state": True,
                },
                {
                    "index": 5,
                    "name": "Outlet 5",
                    "cycle_enabled": False,
                    "relay_state": False,
                },
                {
                    "index": 6,
                    "name": "Outlet 6",
                    "cycle_enabled": False,
                    "relay_state": False,
                },
                {
                    "index": 7,
                    "name": "USB Outlets",
                    "cycle_enabled": False,
                    "relay_state": False,
                },
            ],
            "port_table": [],
            "state": 1,
            "sys_stats": {"mem_total": 98304, "mem_used": 88056},
            "type": "uap",
            "version": "2.2.1.511",
            "upgradable": False,
            "uplink": STRIP_UP6["uplink"],
        },
    ),
    (
        [PDU_PRO],
        {
            "board_revision": 1,
            "downlink_table": [],
            "id": "61e4a1e60bbb2d53aeb430ea",
            "ip": "192.168.1.66",
            "has_fan": False,
            "last_seen": 1643721168,
            "lldp_table": [
                {
                    "chassis_id": "00:00:00:00:00:83",
                    "chassis_id_subtype": "mac",
                    "is_wired": True,
                    "local_port_idx": 1,
                    "local_port_name": "eth0",
                    "port_id": "local Port 1",
                }
            ],
            "mac": "00:00:00:00:00:84",
            "model": "USPPDUP",
            "name": "Main Server Cabinet PDU",
            "next_interval": 56,
            "outlet_ac_power_budget": "1875.000",
            "outlet_ac_power_consumption": "307.741",
            "outlet_table": [
                {
                    "index": 1,
                    "relay_state": True,
                    "cycle_enabled": False,
                    "name": "USB Outlet 1",
                    "outlet_caps": 1,
                },
                {
                    "index": 2,
                    "relay_state": False,
                    "cycle_enabled": False,
                    "name": "USB Outlet 2",
                    "outlet_caps": 1,
                },
                {
                    "index": 3,
                    "relay_state": True,
                    "cycle_enabled": False,
                    "name": "USB Outlet 3",
                    "outlet_caps": 1,
                },
                {
                    "index": 4,
                    "relay_state": False,
                    "cycle_enabled": False,
                    "name": "USB Outlet 4",
                    "outlet_caps": 1,
                },
                {
                    "index": 5,
                    "relay_state": True,
                    "name": "Console",
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.061",
                    "outlet_power": "3.815",
                    "outlet_power_factor": "0.527",
                },
                {
                    "index": 6,
                    "relay_state": True,
                    "name": "UDM Pro",
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.248",
                    "outlet_power": "14.351",
                    "outlet_power_factor": "0.488",
                },
                {
                    "index": 7,
                    "relay_state": True,
                    "name": "Unraid",
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "1.454",
                    "outlet_power": "169.900",
                    "outlet_power_factor": "0.985",
                },
                {
                    "index": 8,
                    "relay_state": True,
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.000",
                    "outlet_power": "0.000",
                    "outlet_power_factor": "0.000",
                    "name": "Outlet 8",
                },
                {
                    "index": 9,
                    "relay_state": True,
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.000",
                    "outlet_power": "0.000",
                    "outlet_power_factor": "0.000",
                    "name": "Outlet 9",
                },
                {
                    "index": 10,
                    "relay_state": True,
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.000",
                    "outlet_power": "0.000",
                    "outlet_power_factor": "0.000",
                    "name": "Outlet 10",
                },
                {
                    "index": 11,
                    "relay_state": False,
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.000",
                    "outlet_power": "0.000",
                    "outlet_power_factor": "0.000",
                    "name": "Outlet 11",
                },
                {
                    "index": 12,
                    "relay_state": True,
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.000",
                    "outlet_power": "0.000",
                    "outlet_power_factor": "0.000",
                    "name": "Outlet 12",
                },
                {
                    "index": 13,
                    "relay_state": True,
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.000",
                    "outlet_power": "0.000",
                    "outlet_power_factor": "0.000",
                    "name": "Outlet 13",
                },
                {
                    "index": 14,
                    "relay_state": True,
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.000",
                    "outlet_power": "0.000",
                    "outlet_power_factor": "0.000",
                    "name": "Outlet 14",
                },
                {
                    "index": 15,
                    "relay_state": True,
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.127",
                    "outlet_power": "9.394",
                    "outlet_power_factor": "0.623",
                    "name": "Outlet 15",
                },
                {
                    "index": 16,
                    "relay_state": True,
                    "name": "UNVR Pro",
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.278",
                    "outlet_power": "31.992",
                    "outlet_power_factor": "0.970",
                },
                {
                    "index": 17,
                    "relay_state": True,
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.000",
                    "outlet_power": "0.000",
                    "outlet_power_factor": "0.000",
                    "name": "Outlet 17",
                },
                {
                    "index": 18,
                    "relay_state": True,
                    "name": "Home Assistant",
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.328",
                    "outlet_power": "21.529",
                    "outlet_power_factor": "0.553",
                },
                {
                    "index": 19,
                    "relay_state": True,
                    "name": "Server Cabinet Switch",
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.495",
                    "outlet_power": "56.760",
                    "outlet_power_factor": "0.967",
                },
                {
                    "index": 20,
                    "relay_state": True,
                    "name": "Rear Cabinet Lights",
                    "outlet_caps": 3,
                    "outlet_voltage": "118.566",
                    "outlet_current": "0.000",
                    "outlet_power": "0.000",
                    "outlet_power_factor": "0.000",
                },
            ],
            "outlet_overrides": [
                {
                    "index": 1,
                    "name": "USB Outlet 1",
                    "cycle_enabled": False,
                    "relay_state": False,
                },
                {
                    "index": 2,
                    "name": "USB Outlet 2",
                    "cycle_enabled": False,
                    "relay_state": False,
                },
                {
                    "index": 3,
                    "name": "USB Outlet 3",
                    "cycle_enabled": False,
                    "relay_state": False,
                },
                {
                    "index": 4,
                    "name": "USB Outlet 4",
                    "cycle_enabled": False,
                    "relay_state": False,
                },
                {"index": 5, "name": "Console", "relay_state": True},
                {"index": 6, "name": "UDM Pro", "relay_state": True},
                {"index": 7, "name": "Unraid", "relay_state": True},
                {"index": 8, "relay_state": True},
                {"index": 9, "relay_state": True},
                {"index": 10, "relay_state": True},
                {"index": 11, "relay_state": True},
                {"index": 12, "relay_state": True},
                {"index": 13, "relay_state": True},
                {"index": 14, "relay_state": True},
                {"index": 15, "relay_state": True},
                {"index": 16, "name": "UNVR Pro", "relay_state": True},
                {"index": 17, "relay_state": True},
                {"index": 18, "name": "Home Assistant", "relay_state": True},
                {"index": 19, "name": "Server Cabinet Switch", "relay_state": True},
                {"index": 20, "name": "Rear Cabinet Lights", "relay_state": True},
            ],
            "port_table": [
                {
                    "port_idx": 1,
                    "media": "FE",
                    "port_poe": False,
                    "poe_caps": 0,
                    "speed_caps": 1048591,
                    "op_mode": "switch",
                    "portconf_id": "5fc7fb23c3da2e039ebeea97",
                    "autoneg": False,
                    "enable": True,
                    "flowctrl_rx": False,
                    "flowctrl_tx": False,
                    "full_duplex": True,
                    "is_uplink": True,
                    "jumbo": False,
                    "mac_table": [],
                    "rx_broadcast": 0,
                    "rx_bytes": 538000102,
                    "rx_dropped": 2,
                    "rx_errors": 0,
                    "rx_multicast": 0,
                    "rx_packets": 3943979,
                    "satisfaction": 90,
                    "satisfaction_reason": 1,
                    "speed": 100,
                    "stp_pathcost": 0,
                    "stp_state": "disabled",
                    "tx_broadcast": 0,
                    "tx_bytes": 114523726,
                    "tx_dropped": 0,
                    "tx_errors": 0,
                    "tx_multicast": 0,
                    "tx_packets": 670312,
                    "up": True,
                    "tx_bytes-r": 82,
                    "rx_bytes-r": 1510,
                    "bytes-r": 1592,
                    "name": "Port 1",
                    "masked": False,
                    "aggregated_by": False,
                }
            ],
            "state": 1,
            "sys_stats": {
                "loadavg_1": "0.08",
                "loadavg_15": "0.01",
                "loadavg_5": "0.02",
                "mem_buffer": 0,
                "mem_total": 61792256,
                "mem_used": 18235392,
            },
            "type": "usw",
            "version": "5.76.7.13442",
            "upgradable": False,
            "uplink": PDU_PRO["uplink"],
        },
    ),
    (
        [SWITCH_16_PORT_POE],
        {
            "board_revision": 9,
            "considered_lost_at": 1588175821,
            "disabled": False,
            "id": "235678987654345678",
            "ip": "192.168.0.57",
            "downlink_table": [],
            "fan_level": 0,
            "has_fan": True,
            "last_seen": 1588175722,
            "lldp_table": [],
            "mac": "fc:ec:da:11:22:33",
            "model": "US16P150",
            "name": "Switch 16",
            "next_interval": 23,
            "next_heartbeat_at": 1588175755,
            "overheating": False,
            "port_overrides": [
                {
                    "poe_mode": "auto",
                    "portconf_id": "5e1b309714bd614afd3d11a7",
                    "port_security_mac_address": [],
                    "autoneg": True,
                    "stp_port_mode": True,
                },
                {
                    "poe_mode": "off",
                    "port_idx": 3,
                    "portconf_id": "5a32aa4ee4babd4452422ddd22222",
                },
                {
                    "poe_mode": "auto",
                    "port_idx": 4,
                    "portconf_id": "5a32aa4ee4babd4452422ddd22222",
                },
                {
                    "poe_mode": "auto",
                    "port_idx": 16,
                    "portconf_id": "5a32aa4ee4babd4452422ddd22222",
                },
            ],
            "port_table": SWITCH_16_PORT_POE["port_table"],
            "state": 1,
            "sys_stats": {
                "loadavg_1": "2.82",
                "loadavg_15": "2.81",
                "loadavg_5": "2.80",
                "mem_buffer": 0,
                "mem_total": 262402048,
                "mem_used": 129331200,
            },
            "type": "usw",
            "version": "4.0.66.10832",
            "upgradable": True,
            "upgrade_to_firmware": "4.0.80.10875",
            "uplink": SWITCH_16_PORT_POE["uplink"],
            "uplink_depth": 2,
            "user_num_sta": 4,
            "wlan_overrides": [],
        },
    ),
]


@pytest.mark.parametrize("device_payload, reference_data", test_data)
async def test_device(unifi_controller, mock_endpoints, reference_data):
    """Test device class."""
    devices = unifi_controller.devices
    await devices.update()
    assert len(devices.items()) == 1

    device = next(iter(devices.values()))
    for key, value in reference_data.items():
        assert getattr(device, key) == value
    assert device.__repr__() == f"<Device {device.name}: {device.mac}>"


@pytest.mark.parametrize(
    "method, mac, command",
    [["upgrade", "0", {"mac": "0", "cmd": "upgrade"}]],
)
async def test_device_commands(
    mock_aioresponse, unifi_controller, unifi_called_with, method, mac, command
):
    """Test device commands."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/devmgr", payload={})
    class_command = getattr(unifi_controller.devices, method)
    await class_command(mac)
    assert unifi_called_with("post", "/api/s/default/cmd/devmgr", json=command)


@pytest.mark.parametrize(
    "api_request, input, command",
    [
        [
            DeviceRestartRequest,
            {"mac": "0", "soft": True},
            {"mac": "0", "cmd": "restart", "reboot_type": "soft"},
        ],
        [
            DeviceRestartRequest,
            {"mac": "0", "soft": False},
            {"mac": "0", "cmd": "restart", "reboot_type": "hard"},
        ],
        [
            DeviceUpgradeRequest,
            {"mac": "0"},
            {"mac": "0", "cmd": "upgrade"},
        ],
        [
            DevicePowerCyclePortRequest,
            {"mac": "0", "port_idx": 1},
            {"mac": "0", "port_idx": 1, "cmd": "power-cycle"},
        ],
    ],
)
async def test_device_requests(
    mock_aioresponse, unifi_controller, unifi_called_with, api_request, input, command
):
    """Test device commands."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/devmgr", payload={})
    await unifi_controller.request(api_request.create(**input))
    assert unifi_called_with("post", "/api/s/default/cmd/devmgr", json=command)


@pytest.mark.parametrize(
    "device_payload, api_request, input, command",
    [
        [  # Outlet set relay without existing override
            [
                {
                    "device_id": "01",
                    "mac": "0",
                    "outlet_overrides": [],
                    "outlet_table": [
                        {
                            "index": 1,
                            "relay_state": True,
                            "cycle_enabled": False,
                            "name": "USB Outlet 1",
                            "outlet_caps": 1,
                        },
                    ],
                }
            ],
            DeviceSetOutletRelayRequest,
            {"outlet_idx": 1, "state": True},
            {
                "outlet_overrides": [
                    {"index": 1, "name": "USB Outlet 1", "relay_state": True}
                ]
            },
        ],
        [  # Outlet set relay with existing override
            [
                {
                    "device_id": "01",
                    "mac": "0",
                    "outlet_overrides": [{"index": 2}],
                    "outlet_table": [
                        {
                            "index": 2,
                            "relay_state": True,
                            "cycle_enabled": False,
                            "name": "USB Outlet 1",
                            "outlet_caps": 1,
                        },
                    ],
                }
            ],
            DeviceSetOutletRelayRequest,
            {"outlet_idx": 2, "state": False},
            {"outlet_overrides": [{"index": 2, "relay_state": False}]},
        ],
        [  # Outlet outlet cycle without existing override
            [
                {
                    "device_id": "01",
                    "mac": "0",
                    "outlet_overrides": [],
                    "outlet_table": [
                        {
                            "index": 1,
                            "relay_state": True,
                            "cycle_enabled": False,
                            "name": "USB Outlet 1",
                            "outlet_caps": 1,
                        },
                    ],
                }
            ],
            DeviceSetOutletCycleEnabledRequest,
            {"outlet_idx": 1, "state": True},
            {
                "outlet_overrides": [
                    {"index": 1, "name": "USB Outlet 1", "cycle_enabled": True}
                ]
            },
        ],
        [  # Outlet outlet cycle with existing override
            [
                {
                    "device_id": "01",
                    "mac": "0",
                    "outlet_overrides": [{"index": 2}],
                    "outlet_table": [
                        {
                            "index": 2,
                            "relay_state": True,
                            "cycle_enabled": False,
                            "name": "USB Outlet 1",
                            "outlet_caps": 1,
                        },
                    ],
                }
            ],
            DeviceSetOutletCycleEnabledRequest,
            {"outlet_idx": 2, "state": False},
            {"outlet_overrides": [{"index": 2, "cycle_enabled": False}]},
        ],
        [  # PoE port mode without existing override
            [
                {
                    "device_id": "01",
                    "mac": "0",
                    "port_overrides": [],
                    "port_table": [
                        {
                            "poe_mode": "Auto",
                            "name": "Port 1",
                            "port_idx": 1,
                        },
                    ],
                }
            ],
            DeviceSetPoePortModeRequest,
            {"port_idx": 1, "mode": "off"},
            {"port_overrides": [{"port_idx": 1, "poe_mode": "off"}]},
        ],
        [  # PoE port mode with portconf_id without existing override
            [
                {
                    "device_id": "01",
                    "mac": "0",
                    "port_overrides": [],
                    "port_table": [
                        {
                            "poe_mode": "Auto",
                            "name": "Port 1",
                            "port_idx": 1,
                            "portconf_id": "123",
                        },
                    ],
                }
            ],
            DeviceSetPoePortModeRequest,
            {"port_idx": 1, "mode": "off"},
            {
                "port_overrides": [
                    {"port_idx": 1, "poe_mode": "off", "portconf_id": "123"}
                ]
            },
        ],
        [  # PoE port mode with existing override
            [
                {
                    "device_id": "01",
                    "mac": "0",
                    "port_overrides": [{"port_idx": 1, "name": "Office"}],
                    "port_table": [
                        {
                            "poe_mode": "Auto",
                            "name": "Office",
                            "port_idx": 1,
                        },
                    ],
                }
            ],
            DeviceSetPoePortModeRequest,
            {"port_idx": 1, "mode": "off"},
            {"port_overrides": [{"port_idx": 1, "poe_mode": "off", "name": "Office"}]},
        ],
    ],
)
async def test_sub_device_requests(
    mock_aioresponse,
    unifi_controller,
    mock_endpoints,
    unifi_called_with,
    api_request,
    input,
    command,
):
    """Test sub device (port/outlet) commands."""
    devices = unifi_controller.devices
    await devices.update()
    device = next(iter(devices.values()))
    mock_aioresponse.put("https://host:8443/api/s/default/rest/device/01", payload={})
    await unifi_controller.request(api_request.create(device, **input))
    assert unifi_called_with("put", "/api/s/default/rest/device/01", json=command)
