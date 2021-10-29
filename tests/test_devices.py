"""Test client configuration API.

pytest --cov-report term-missing --cov=aiounifi.devices tests/test_devices.py
"""

from aiounifi.devices import Devices

from .fixtures import ACCESS_POINT_AC_PRO, GATEWAY_USG3, SWITCH_16_PORT_POE
from .test_controller import verify_call


async def test_no_devices(mock_aioresponse, unifi_controller):
    """Test that no devices also work."""
    devices = Devices([], unifi_controller.request)

    mock_aioresponse.get("https://host:8443/api/s/default/stat/device", payload={})

    await devices.update()

    assert verify_call(
        mock_aioresponse, "get", "https://host:8443/api/s/default/stat/device"
    )

    assert len(devices.values()) == 0


async def test_device_access_point(unifi_controller):
    """Test device class on an access point."""
    devices = Devices([ACCESS_POINT_AC_PRO], unifi_controller.request)

    assert len(devices.values()) == 1

    access_point = devices[ACCESS_POINT_AC_PRO["mac"]]
    assert access_point.board_rev == 21
    assert access_point.considered_lost_at == 1588175837
    assert access_point.disabled is False
    assert access_point.id == "235678987654345678"
    assert access_point.ip == "192.168.0.4"
    assert access_point.fan_level is None
    assert access_point.has_fan is False
    assert access_point.last_seen == 1588175726
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

    assert len(access_point.ports.values()) == 2

    access_point_port_1 = access_point.ports[1]
    assert access_point_port_1.ifname == ""
    assert access_point_port_1.media == "GE"
    assert access_point_port_1.name == "Main"
    assert access_point_port_1.port_idx == 1
    assert access_point_port_1.poe_class == ""
    assert access_point_port_1.poe_enable is None
    assert access_point_port_1.poe_mode == ""
    assert access_point_port_1.poe_power == ""
    assert access_point_port_1.poe_voltage == ""
    assert access_point_port_1.portconf_id == "5a32aa4"
    assert access_point_port_1.port_poe is False
    assert access_point_port_1.up is True
    assert (
        access_point_port_1.__repr__()
        == f"<{access_point_port_1.name}: Poe {access_point_port_1.poe_enable}>"
    )

    access_point_port_2 = access_point.ports[2]
    assert access_point_port_2.ifname == ""
    assert access_point_port_2.media == "GE"
    assert access_point_port_2.name == "Secondary"
    assert access_point_port_2.port_idx == 2
    assert access_point_port_2.poe_class == ""
    assert access_point_port_2.poe_enable is None
    assert access_point_port_2.poe_mode == ""
    assert access_point_port_2.poe_power == ""
    assert access_point_port_2.poe_voltage == ""
    assert access_point_port_2.portconf_id == "5a32aa4"
    assert access_point_port_2.port_poe is False
    assert access_point_port_2.up is False
    assert (
        access_point_port_2.__repr__()
        == f"<{access_point_port_2.name}: Poe {access_point_port_2.poe_enable}>"
    )


async def test_device_security_gateway(unifi_controller):
    """Test device class on a security gateway."""
    devices = Devices([GATEWAY_USG3], unifi_controller.request)

    assert len(devices.values()) == 1

    gateway = devices[GATEWAY_USG3["mac"]]
    assert gateway.board_rev == 16
    assert gateway.considered_lost_at == 1588175842
    assert gateway.disabled is False
    assert gateway.id == "235678987654345678"
    assert gateway.ip == "1.2.3.4"
    assert gateway.fan_level is None
    assert gateway.has_fan is False
    assert gateway.last_seen == 1588175740
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

    assert len(gateway.ports.values()) == 3

    gateway_port_eth0 = gateway.ports["eth0"]
    assert gateway_port_eth0.ifname == "eth0"
    assert gateway_port_eth0.media == ""
    assert gateway_port_eth0.name == "wan"
    assert gateway_port_eth0.port_idx is None
    assert gateway_port_eth0.poe_class == ""
    assert gateway_port_eth0.poe_enable is None
    assert gateway_port_eth0.poe_mode == ""
    assert gateway_port_eth0.poe_power == ""
    assert gateway_port_eth0.poe_voltage == ""
    assert gateway_port_eth0.portconf_id == ""
    assert gateway_port_eth0.port_poe is False
    assert gateway_port_eth0.up is True
    assert (
        gateway_port_eth0.__repr__()
        == f"<{gateway_port_eth0.name}: Poe {gateway_port_eth0.poe_enable}>"
    )

    gateway_port_eth1 = gateway.ports["eth1"]
    assert gateway_port_eth1.ifname == "eth1"
    assert gateway_port_eth1.media == ""
    assert gateway_port_eth1.name == "lan"
    assert gateway_port_eth1.port_idx is None
    assert gateway_port_eth1.poe_class == ""
    assert gateway_port_eth1.poe_enable is None
    assert gateway_port_eth1.poe_mode == ""
    assert gateway_port_eth1.poe_power == ""
    assert gateway_port_eth1.poe_voltage == ""
    assert gateway_port_eth1.portconf_id == ""
    assert gateway_port_eth1.port_poe is False
    assert gateway_port_eth1.up is True
    assert (
        gateway_port_eth1.__repr__()
        == f"<{gateway_port_eth1.name}: Poe {gateway_port_eth1.poe_enable}>"
    )

    gateway_port_eth2 = gateway.ports["eth2"]
    assert gateway_port_eth2.ifname == "eth2"
    assert gateway_port_eth2.media == ""
    assert gateway_port_eth2.name == "lan2"
    assert gateway_port_eth2.port_idx is None
    assert gateway_port_eth2.poe_class == ""
    assert gateway_port_eth2.poe_enable is None
    assert gateway_port_eth2.poe_mode == ""
    assert gateway_port_eth2.poe_power == ""
    assert gateway_port_eth2.poe_voltage == ""
    assert gateway_port_eth2.portconf_id == ""
    assert gateway_port_eth2.port_poe is False
    assert gateway_port_eth2.up is False
    assert (
        gateway_port_eth2.__repr__()
        == f"<{gateway_port_eth2.name}: Poe {gateway_port_eth2.poe_enable}>"
    )


async def test_device_switch(mock_aioresponse, unifi_controller):
    """Test device class on aswitch."""
    devices = Devices([SWITCH_16_PORT_POE], unifi_controller.request)

    assert len(devices.values()) == 1

    switch = devices[SWITCH_16_PORT_POE["mac"]]
    assert switch.board_rev == 9
    assert switch.considered_lost_at == 1588175821
    assert switch.disabled is False
    assert switch.id == "235678987654345678"
    assert switch.ip == "192.168.0.57"
    assert switch.fan_level == 0
    assert switch.has_fan is True
    assert switch.last_seen == 1588175722
    assert switch.mac == "fc:ec:da:11:22:33"
    assert switch.model == "US16P150"
    assert switch.name == "Switch 16"
    assert switch.next_interval == 23
    assert switch.next_heartbeat_at == 1588175755
    assert switch.overheating is False
    assert switch.port_overrides == [
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
    await switch.async_set_port_poe_mode(1, "off")
    assert verify_call(
        mock_aioresponse,
        "put",
        "https://host:8443/api/s/default/rest/device/235678987654345678",
        json={
            "port_overrides": [
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

    await switch.async_set_port_poe_mode(3, "off")
    assert verify_call(
        mock_aioresponse,
        "put",
        "https://host:8443/api/s/default/rest/device/235678987654345678",
        json={
            "port_overrides": [
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

    assert len(switch.ports.values()) == 18

    switch_port_1 = switch.ports[1]
    assert switch_port_1.ifname == ""
    assert switch_port_1.media == "GE"
    assert switch_port_1.name == "Port 1"
    assert switch_port_1.port_idx == 1
    assert switch_port_1.poe_class == "Unknown"
    assert switch_port_1.poe_enable is False
    assert switch_port_1.poe_mode == "auto"
    assert switch_port_1.poe_power == "0.00"
    assert switch_port_1.poe_voltage == "0.00"
    assert switch_port_1.portconf_id == "5a32aa4ee4babd4452422ddd22222"
    assert switch_port_1.port_poe is True
    assert switch_port_1.up is True
    assert (
        switch_port_1.__repr__()
        == f"<{switch_port_1.name}: Poe {switch_port_1.poe_enable}>"
    )

    switch_port_2 = switch.ports[2]
    assert switch_port_2.ifname == ""
    assert switch_port_2.media == "GE"
    assert switch_port_2.name == "Port 2"
    assert switch_port_2.port_idx == 2
    assert switch_port_2.poe_class == "Unknown"
    assert switch_port_2.poe_enable is False
    assert switch_port_2.poe_mode == "auto"
    assert switch_port_2.poe_power == "0.00"
    assert switch_port_2.poe_voltage == "0.00"
    assert switch_port_2.portconf_id == "5a32aa4ee4babd4452422ddd22222"
    assert switch_port_2.port_poe is True
    assert switch_port_2.up is False
    assert (
        switch_port_2.__repr__()
        == f"<{switch_port_2.name}: Poe {switch_port_2.poe_enable}>"
    )

    switch_port_3 = switch.ports[3]
    assert switch_port_3.ifname == ""
    assert switch_port_3.media == "GE"
    assert switch_port_3.name == "Port 3"
    assert switch_port_3.port_idx == 3
    assert switch_port_3.poe_class == "Class 3"
    assert switch_port_3.poe_enable is True
    assert switch_port_3.poe_mode == "auto"
    assert switch_port_3.poe_power == "3.24"
    assert switch_port_3.poe_voltage == "53.78"
    assert switch_port_3.portconf_id == "5a32aa4ee4babd4452422ddd22222"
    assert switch_port_3.port_poe is True
    assert switch_port_3.up is True
    assert (
        switch_port_3.__repr__()
        == f"<{switch_port_3.name}: Poe {switch_port_3.poe_enable}>"
    )

    switch_port_4 = switch.ports[4]
    assert switch_port_4.ifname == ""
    assert switch_port_4.media == "GE"
    assert switch_port_4.name == "Port 4"
    assert switch_port_4.port_idx == 4
    assert switch_port_4.poe_class == "Class 2"
    assert switch_port_4.poe_enable is True
    assert switch_port_4.poe_mode == "auto"
    assert switch_port_4.poe_power == "1.50"
    assert switch_port_4.poe_voltage == "53.85"
    assert switch_port_4.portconf_id == "5a32aa4ee4babd4452422ddd22222"
    assert switch_port_4.port_poe is True
    assert switch_port_4.up is True
    assert (
        switch_port_4.__repr__()
        == f"<{switch_port_4.name}: Poe {switch_port_4.poe_enable}>"
    )

    switch_port_5 = switch.ports[5]
    assert switch_port_5.ifname == ""
    assert switch_port_5.media == "GE"
    assert switch_port_5.name == "Port 5"
    assert switch_port_5.port_idx == 5
    assert switch_port_5.poe_class == "Unknown"
    assert switch_port_5.poe_enable is False
    assert switch_port_5.poe_mode == "auto"
    assert switch_port_5.poe_power == "0.00"
    assert switch_port_5.poe_voltage == "0.00"
    assert switch_port_5.portconf_id == "5a32aa4ee4babd4452422ddd22222"
    assert switch_port_5.port_poe is True
    assert switch_port_5.up is False
    assert (
        switch_port_5.__repr__()
        == f"<{switch_port_5.name}: Poe {switch_port_5.poe_enable}>"
    )

    switch_port_6 = switch.ports[6]
    assert switch_port_6.ifname == ""
    assert switch_port_6.media == "GE"
    assert switch_port_6.name == "Port 6"
    assert switch_port_6.port_idx == 6
    assert switch_port_6.poe_class == "Unknown"
    assert switch_port_6.poe_enable is False
    assert switch_port_6.poe_mode == "auto"
    assert switch_port_6.poe_power == "0.00"
    assert switch_port_6.poe_voltage == "0.00"
    assert switch_port_6.portconf_id == "5a32aa4ee4babd4452422ddd22222"
    assert switch_port_6.port_poe is True
    assert switch_port_6.up is False
    assert (
        switch_port_6.__repr__()
        == f"<{switch_port_6.name}: Poe {switch_port_6.poe_enable}>"
    )
