"""Test aioUniFi device outlets.

pytest --cov-report term-missing --cov=aiounifi.outlets tests/test_outlets.py
"""

from unittest.mock import Mock

import pytest

from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.models.outlet import Outlet

from .fixtures import PDU_PRO, PLUG_UP1, STRIP_UP6


async def test_handler_ports(unifi_controller):
    """Verify that device ports works."""
    outlets = unifi_controller.outlets
    assert len(outlets.items()) == 0
    assert len(outlets.values()) == 0

    assert "78:45:58:fc:16:7d_1" not in outlets
    assert outlets.get("78:45:58:fc:16:7d_1", "xy") == "xy"
    assert not isinstance(outlets.get("78:45:58:fc:16:7d_1"), Outlet)
    unsub_all = outlets.subscribe(mock_subscribe_all := Mock())
    unsub_7 = outlets.subscribe(
        mock_subscribe_7 := Mock(), id_filter="78:45:58:fc:16:7d_7"
    )
    unsub_added = outlets.subscribe(
        mock_subscribe_added := Mock(), event_filter=ItemEvent.ADDED
    )
    unsub_changed = outlets.subscribe(
        mock_subscribe_changed := Mock(), event_filter=ItemEvent.CHANGED
    )
    unsub_deleted = outlets.subscribe(
        mock_subscribe_deleted := Mock(), event_filter=ItemEvent.DELETED
    )
    unsub_bad = outlets.subscribe(mock_subscribe_bad := Mock(), id_filter="bad")

    # Add outlets
    unifi_controller.devices.process_raw([STRIP_UP6])
    assert next(iter(outlets)) == "78:45:58:fc:16:7d_1"
    assert "78:45:58:fc:16:7d_2" in outlets
    assert isinstance(outlets.get("78:45:58:fc:16:7d_3"), Outlet)
    assert isinstance(outlets["78:45:58:fc:16:7d_4"], Outlet)
    assert len(outlets.values()) == 7
    assert mock_subscribe_all.call_count == 7
    mock_subscribe_all.assert_called_with(ItemEvent.ADDED, "78:45:58:fc:16:7d_7")
    mock_subscribe_7.assert_called_once()
    assert mock_subscribe_added.call_count == 7
    mock_subscribe_changed.assert_not_called()
    mock_subscribe_deleted.assert_not_called()
    mock_subscribe_bad.assert_not_called()

    # Update outlets
    unifi_controller.devices.process_raw([STRIP_UP6])
    assert len(outlets.values()) == 7
    assert mock_subscribe_all.call_count == 14
    mock_subscribe_all.assert_called_with(ItemEvent.CHANGED, "78:45:58:fc:16:7d_7")
    assert mock_subscribe_7.call_count == 2
    assert mock_subscribe_added.call_count == 7
    assert mock_subscribe_changed.call_count == 7
    mock_subscribe_deleted.assert_not_called()
    mock_subscribe_bad.assert_not_called()

    # Remove outlets
    unifi_controller.devices.remove_item(STRIP_UP6)
    assert len(outlets.values()) == 0
    assert mock_subscribe_all.call_count == 21
    mock_subscribe_all.assert_called_with(ItemEvent.DELETED, "78:45:58:fc:16:7d_7")
    assert mock_subscribe_7.call_count == 3
    assert mock_subscribe_added.call_count == 7
    assert mock_subscribe_changed.call_count == 7
    assert mock_subscribe_deleted.call_count == 7
    mock_subscribe_bad.assert_not_called()

    unsub_all()
    unsub_7()
    unsub_added()
    unsub_changed()
    unsub_deleted()
    unsub_bad()

    unsub_all()
    unsub_all()


async def test_handler_process_device_no_index(unifi_controller):
    """Verify that device ports works."""
    ports = unifi_controller.ports
    unifi_controller.devices.process_raw([{"mac": "1", "outlet_table": []}])
    assert len(ports.items()) == 0


data_test_outlet = [
    (
        [PDU_PRO],
        {
            "device": PDU_PRO,
            "obj_id": "00:00:00:00:00:84_1",
            "name": "USB Outlet 1",
            "index": 1,
            "relay_state": True,
            "has_relay": None,
            "cycle_enabled": False,
            "has_metering": None,
            "caps": 1,
            "voltage": None,
            "current": None,
            "power": None,
            "power_factor": None,
            "repr": "<USB Outlet 1: relay state True>",
        },
    ),
    (
        [PDU_PRO],
        {
            "device": PDU_PRO,
            "obj_id": "00:00:00:00:00:84_5",
            "name": "Console",
            "index": 5,
            "relay_state": True,
            "has_relay": None,
            "cycle_enabled": None,
            "has_metering": None,
            "caps": 3,
            "voltage": "118.566",
            "current": "0.061",
            "power": "3.815",
            "power_factor": "0.527",
            "repr": "<Console: relay state True>",
        },
    ),
    (
        [PLUG_UP1],
        {
            "device": PLUG_UP1,
            "obj_id": "fc:ec:da:76:4f:5f_1",
            "name": "Outlet 1",
            "index": 1,
            "relay_state": False,
            "has_relay": True,
            "cycle_enabled": None,
            "has_metering": False,
            "caps": None,
            "voltage": None,
            "current": None,
            "power": None,
            "power_factor": None,
            "repr": "<Outlet 1: relay state False>",
        },
    ),
    (
        [STRIP_UP6],
        {
            "device": STRIP_UP6,
            "obj_id": "78:45:58:fc:16:7d_1",
            "name": "Outlet 1",
            "index": 1,
            "relay_state": False,
            "has_relay": True,
            "cycle_enabled": False,
            "has_metering": False,
            "caps": None,
            "voltage": None,
            "current": None,
            "power": None,
            "power_factor": None,
            "repr": "<Outlet 1: relay state False>",
        },
    ),
]


@pytest.mark.parametrize(("device_payload", "test_data"), data_test_outlet)
async def test_outlet(unifi_controller, _mock_endpoints, test_data):
    """Verify that device outlet model works."""
    await unifi_controller.devices.update()
    outlet = unifi_controller.outlets[test_data["obj_id"]]

    assert outlet.name == test_data["name"]
    assert outlet.index == test_data["index"]
    assert outlet.relay_state == test_data["relay_state"]
    assert outlet.has_relay == test_data["has_relay"]
    assert outlet.cycle_enabled == test_data["cycle_enabled"]
    assert outlet.has_metering == test_data["has_metering"]
    assert outlet.caps == test_data["caps"]
    assert outlet.voltage == test_data["voltage"]
    assert outlet.current == test_data["current"]
    assert outlet.power == test_data["power"]
    assert outlet.power_factor == test_data["power_factor"]

    assert repr(outlet) == test_data["repr"]
