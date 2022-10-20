"""Test aioUniFi device outlets.

pytest --cov-report term-missing --cov=aiounifi.outlets tests/test_outlets.py
"""

from unittest.mock import Mock

from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.models.outlet import Outlet

from .fixtures import STRIP_UP6


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

    outlets._subscribers.clear()
    unsub_all()


async def test_handler_process_device_no_index(unifi_controller):
    """Verify that device ports works."""
    ports = unifi_controller.ports
    unifi_controller.devices.process_raw([{"mac": "1", "outlet_table": [{}]}])
    assert len(ports.items()) == 0


async def test_outlet(unifi_controller):
    """Verify that device outlet model works."""
    unifi_controller.devices.process_raw([STRIP_UP6])
    outlet = unifi_controller.outlets["78:45:58:fc:16:7d_1"]

    assert outlet.name == "Outlet 1"
    assert outlet.index == 1
    assert outlet.relay_state is False
    assert outlet.has_relay is True
    assert outlet.cycle_enabled is False
    assert outlet.has_metering is False
    assert outlet.caps is None
    assert outlet.voltage is None
    assert outlet.current is None
    assert outlet.power is None
    assert outlet.power_factor is None

    assert repr(outlet) == "<Outlet 1: relay state False>"
