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


async def test_power_cycle_port(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test power cycle port work."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/devmgr", payload={})

    await unifi_controller.request(DevicePowerCyclePortRequest.create("00:..:11", 1))

    assert unifi_called_with(
        "post",
        "/api/s/default/cmd/devmgr",
        json={"cmd": "power-cycle", "mac": "00:..:11", "port_idx": 1},
    )


@pytest.mark.parametrize("input, expected", [(True, "soft"), (False, "hard")])
async def test_device_restart(
    mock_aioresponse, unifi_controller, unifi_called_with, input, expected
):
    """Test that no devices also work."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/devmgr", payload={})

    await unifi_controller.request(DeviceRestartRequest.create("00:..:11", input))

    assert unifi_called_with(
        "post",
        "/api/s/default/cmd/devmgr",
        json={"cmd": "restart", "mac": "00:..:11", "reboot_type": expected},
    )


async def test_device_upgrade_request(
    mock_aioresponse, unifi_controller, unifi_called_with
):
    """Test device upgrade request work."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/devmgr", payload={})

    await unifi_controller.request(DeviceUpgradeRequest.create("00:..:11"))

    assert unifi_called_with(
        "post",
        "/api/s/default/cmd/devmgr",
        json={"cmd": "upgrade", "mac": "00:..:11"},
    )


async def test_no_devices(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test that no devices also work."""
    mock_aioresponse.get("https://host:8443/api/s/default/stat/device", payload={})

    devices = unifi_controller.devices
    await devices.update()

    assert unifi_called_with("get", "/api/s/default/stat/device")
    assert len(devices.values()) == 0


async def test_device_access_point(unifi_controller):
    """Test device class on an access point."""
    devices = unifi_controller.devices
    devices.process_raw([ACCESS_POINT_AC_PRO])

    assert len(devices.values()) == 1

    access_point = devices[ACCESS_POINT_AC_PRO["mac"]]
    assert access_point.board_revision == 21
    assert access_point.considered_lost_at == 1588175837
    assert access_point.disabled is False
    assert access_point.id == "235678987654345678"
    assert access_point.ip == "192.168.0.4"
    assert access_point.downlink_table == []
    assert access_point.fan_level is None
    assert access_point.has_fan is False
    assert access_point.last_seen == 1588175726
    assert access_point.lldp_table == []
    assert access_point.mac == "80:2a:a8:00:01:02"
    assert access_point.model == "U7PG2"
    assert access_point.name == "ACCESS POINT AC PRO"
    assert access_point.next_heartbeat_at == 1588175763
    assert access_point.overheating is False
    assert access_point.port_overrides == []
    assert access_point.port_table == ACCESS_POINT_AC_PRO["port_table"]
    assert access_point.state == 1
    assert access_point.sys_stats == {
        "loadavg_1": "0.15",
        "loadavg_15": "0.02",
        "loadavg_5": "0.08",
        "mem_buffer": 0,
        "mem_total": 128622592,
        "mem_used": 63606784,
    }
    assert access_point.type == "uap"
    assert access_point.version == "4.0.69.10871"
    assert access_point.upgradable is True
    assert access_point.upgrade_to_firmware == "4.0.80.10875"
    assert access_point.uplink == ACCESS_POINT_AC_PRO["uplink"]
    assert access_point.uplink_depth is None
    assert access_point.user_num_sta == 12
    assert access_point.wlan_overrides == [
        {
            "name": "My5GHzSSID1",
            "radio": "na",
            "radio_name": "wifi1",
            "wlan_id": "012345678910111213141516",
        },
    ]
    assert (
        access_point.__repr__() == f"<Device {access_point.name}: {access_point.mac}>"
    )


async def test_device_security_gateway(unifi_controller):
    """Test device class on a security gateway."""
    devices = unifi_controller.devices
    devices.process_raw([GATEWAY_USG3])

    assert len(devices.values()) == 1

    gateway = devices[GATEWAY_USG3["mac"]]
    assert gateway.board_revision == 16
    assert gateway.considered_lost_at == 1588175842
    assert gateway.disabled is False
    assert gateway.id == "235678987654345678"
    assert gateway.ip == "1.2.3.4"
    assert gateway.downlink_table == []
    assert gateway.fan_level is None
    assert gateway.has_fan is False
    assert gateway.last_seen == 1588175740
    assert gateway.lldp_table == []
    assert gateway.mac == "78:8a:20:33:44:55"
    assert gateway.model == "UGW3"
    assert gateway.name == "USG"
    assert gateway.next_heartbeat_at == 1588175774
    assert gateway.overheating is False
    assert gateway.port_overrides == []
    assert gateway.port_table == GATEWAY_USG3["port_table"]
    assert gateway.state == 1
    assert gateway.sys_stats == {
        "loadavg_1": "0.03",
        "loadavg_15": "0.08",
        "loadavg_5": "0.07",
        "mem_buffer": 57561088,
        "mem_total": 507412480,
        "mem_used": 293453824,
    }
    assert gateway.type == "ugw"
    assert gateway.version == "4.4.44.5213844"
    assert gateway.upgradable is True
    assert gateway.upgrade_to_firmware == "4.4.50.5272448"
    assert gateway.uplink == GATEWAY_USG3["uplink"]
    assert gateway.uplink_depth is None
    assert gateway.user_num_sta == 20
    assert gateway.wlan_overrides == []
    assert gateway.__repr__() == f"<Device {gateway.name}: {gateway.mac}>"


async def test_device_plug(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test device class on a plug."""
    devices = unifi_controller.devices
    devices.process_raw([PLUG_UP1])

    assert len(devices.values()) == 1

    plug = devices[PLUG_UP1["mac"]]
    assert plug.board_revision == 2
    assert plug.downlink_table == []
    assert plug.id == "600c8356942a6ade50707b56"
    assert plug.ip == "192.168.0.189"
    assert plug.has_fan is False
    assert plug.last_seen == 1642055273
    assert plug.lldp_table == []
    assert plug.mac == "fc:ec:da:76:4f:5f"
    assert plug.model == "UP1"
    assert plug.name == "Plug"
    assert plug.next_interval == 40
    assert plug.outlet_table == [
        {
            "index": 1,
            "has_relay": True,
            "has_metering": False,
            "relay_state": False,
            "name": "Outlet 1",
        }
    ]
    assert plug.outlet_overrides == []
    assert plug.port_table == []
    assert plug.state == 1
    assert plug.sys_stats == {"mem_total": 98304, "mem_used": 87736}
    assert plug.type == "uap"
    assert plug.version == "2.2.1.511"
    assert plug.upgradable is False
    assert plug.uplink == PLUG_UP1["uplink"]

    mock_aioresponse.put(
        "https://host:8443/api/s/default/rest/device/600c8356942a6ade50707b56",
        payload="",
        repeat=True,
    )
    await unifi_controller.request(DeviceSetOutletRelayRequest.create(plug, 1, False))
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/device/600c8356942a6ade50707b56",
        json={
            "outlet_overrides": [
                {
                    "index": 1,
                    "relay_state": False,
                    "name": "Outlet 1",
                },
            ]
        },
    )

    await unifi_controller.request(
        DeviceSetOutletCycleEnabledRequest.create(plug, 1, True)
    )
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/device/600c8356942a6ade50707b56",
        json={
            "outlet_overrides": [
                {
                    "index": 1,
                    "name": "Outlet 1",
                    "relay_state": False,
                    "cycle_enabled": True,
                },
            ]
        },
    )


async def test_device_strip(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test device class on a usp-strip-us."""
    devices = unifi_controller.devices
    devices.process_raw([STRIP_UP6])

    assert len(devices.values()) == 1

    strip = devices[STRIP_UP6["mac"]]
    assert strip.board_revision == 5
    assert strip.downlink_table == []
    assert strip.id == "61eb1a75942a6a859b45d2bc"
    assert strip.ip == "192.168.0.138"
    assert strip.has_fan is False
    assert strip.last_seen == 1642800247
    assert strip.lldp_table == []
    assert strip.mac == "78:45:58:fc:16:7d"
    assert strip.model == "UP6"
    assert strip.name == ""
    assert strip.next_interval == 41
    assert strip.outlet_table == [
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
    ]
    assert strip.outlet_overrides == [
        {"index": 1, "name": "Outlet 1", "cycle_enabled": False, "relay_state": False},
        {"index": 2, "name": "Outlet 2", "cycle_enabled": False, "relay_state": False},
        {"index": 3, "name": "Outlet 3", "cycle_enabled": False, "relay_state": True},
        {"index": 4, "name": "Outlet 4", "cycle_enabled": True, "relay_state": True},
        {"index": 5, "name": "Outlet 5", "cycle_enabled": False, "relay_state": False},
        {"index": 6, "name": "Outlet 6", "cycle_enabled": False, "relay_state": False},
        {
            "index": 7,
            "name": "USB Outlets",
            "cycle_enabled": False,
            "relay_state": False,
        },
    ]
    assert strip.port_table == []
    assert strip.state == 1
    assert strip.sys_stats == {"mem_total": 98304, "mem_used": 88056}
    assert strip.type == "uap"
    assert strip.version == "2.2.1.511"
    assert strip.upgradable is False
    assert strip.uplink == STRIP_UP6["uplink"]

    mock_aioresponse.put(
        "https://host:8443/api/s/default/rest/device/61eb1a75942a6a859b45d2bc",
        payload="",
        repeat=True,
    )
    await unifi_controller.request(DeviceSetOutletRelayRequest.create(strip, 5, True))
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/device/61eb1a75942a6a859b45d2bc",
        json={
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
                    "relay_state": True,
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
            ]
        },
    )


async def test_device_pdu_pro(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test device class on a PDU Pro 20 port power dispersion unit."""
    devices = unifi_controller.devices
    devices.process_raw([PDU_PRO])

    print({k: PDU_PRO[k] for k in sorted(PDU_PRO)})
    assert len(devices.values()) == 1

    pdupro = devices[PDU_PRO["mac"]]
    assert pdupro.board_revision == 1
    assert pdupro.downlink_table == []
    assert pdupro.id == "61e4a1e60bbb2d53aeb430ea"
    assert pdupro.ip == "192.168.1.66"
    assert pdupro.has_fan is False
    assert pdupro.last_seen == 1643721168
    assert pdupro.lldp_table == [
        {
            "chassis_id": "00:00:00:00:00:83",
            "chassis_id_subtype": "mac",
            "is_wired": True,
            "local_port_idx": 1,
            "local_port_name": "eth0",
            "port_id": "local Port 1",
        }
    ]
    assert pdupro.mac == "00:00:00:00:00:84"
    assert pdupro.model == "USPPDUP"
    assert pdupro.name == "Main Server Cabinet PDU"
    assert pdupro.next_interval == 56
    assert pdupro.outlet_ac_power_budget == "1875.000"
    assert pdupro.outlet_ac_power_consumption == "307.741"
    assert pdupro.outlet_table == [
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
    ]
    assert pdupro.outlet_overrides == [
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
    ]
    assert pdupro.port_table == [
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
    ]
    assert pdupro.state == 1
    assert pdupro.sys_stats == {
        "loadavg_1": "0.08",
        "loadavg_15": "0.01",
        "loadavg_5": "0.02",
        "mem_buffer": 0,
        "mem_total": 61792256,
        "mem_used": 18235392,
    }
    assert pdupro.type == "usw"
    assert pdupro.version == "5.76.7.13442"
    assert pdupro.upgradable is False
    assert pdupro.uplink == PDU_PRO["uplink"]

    mock_aioresponse.put(
        "https://host:8443/api/s/default/rest/device/61e4a1e60bbb2d53aeb430ea",
        payload="",
        repeat=True,
    )
    await unifi_controller.request(DeviceSetOutletRelayRequest.create(pdupro, 5, True))
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/device/61e4a1e60bbb2d53aeb430ea",
        json={
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
            ]
        },
    )


async def test_device_switch(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test device class on aswitch."""
    devices = unifi_controller.devices
    devices.process_raw([SWITCH_16_PORT_POE])

    assert len(devices.values()) == 1

    switch = devices[SWITCH_16_PORT_POE["mac"]]
    assert switch.board_revision == 9
    assert switch.considered_lost_at == 1588175821
    assert switch.disabled is False
    assert switch.id == "235678987654345678"
    assert switch.ip == "192.168.0.57"
    assert switch.downlink_table == []
    assert switch.fan_level == 0
    assert switch.has_fan is True
    assert switch.last_seen == 1588175722
    assert switch.lldp_table == []
    assert switch.mac == "fc:ec:da:11:22:33"
    assert switch.model == "US16P150"
    assert switch.name == "Switch 16"
    assert switch.next_interval == 23
    assert switch.next_heartbeat_at == 1588175755
    assert switch.overheating is False
    assert switch.port_overrides == [
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
    ]
    assert switch.port_table == SWITCH_16_PORT_POE["port_table"]
    assert switch.state == 1
    assert switch.sys_stats == {
        "loadavg_1": "2.82",
        "loadavg_15": "2.81",
        "loadavg_5": "2.80",
        "mem_buffer": 0,
        "mem_total": 262402048,
        "mem_used": 129331200,
    }
    assert switch.type == "usw"
    assert switch.version == "4.0.66.10832"
    assert switch.upgradable is True
    assert switch.upgrade_to_firmware == "4.0.80.10875"
    assert switch.uplink == SWITCH_16_PORT_POE["uplink"]
    assert switch.uplink_depth == 2
    assert switch.user_num_sta == 4
    assert switch.wlan_overrides == []
    assert switch.__repr__() == f"<Device {switch.name}: {switch.mac}>"

    mock_aioresponse.put(
        "https://host:8443/api/s/default/rest/device/235678987654345678",
        payload="",
        repeat=True,
    )
    await unifi_controller.request(DeviceSetPoePortModeRequest.create(switch, 1, "off"))
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/device/235678987654345678",
        json={
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
                {
                    "port_idx": 1,
                    "portconf_id": "5a32aa4ee4babd4452422ddd22222",
                    "poe_mode": "off",
                },
            ]
        },
    )

    await unifi_controller.request(DeviceSetPoePortModeRequest.create(switch, 3, "off"))
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/device/235678987654345678",
        json={
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
                {
                    "port_idx": 1,
                    "portconf_id": "5a32aa4ee4babd4452422ddd22222",
                    "poe_mode": "off",
                },
            ]
        },
    )


async def test_device_upgrade(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test device upgrade command."""

    devices = unifi_controller.devices
    devices.process_raw([ACCESS_POINT_AC_PRO])

    assert len(devices.values()) == 1

    mock_aioresponse.post(
        "https://host:8443/api/s/default/cmd/devmgr", payload={}, repeat=True
    )
    await devices.upgrade(mac="80:2a:a8:00:01:02")
    assert unifi_called_with(
        "post",
        "/api/s/default/cmd/devmgr",
        json={"mac": ACCESS_POINT_AC_PRO["mac"], "cmd": "upgrade"},
    )
