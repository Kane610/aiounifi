"""Test aioUniFi device ports.

pytest --cov-report term-missing --cov=aiounifi.ports tests/test_ports.py
"""
from unittest.mock import Mock

import pytest

from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.models.port import Port

from .fixtures import SWITCH_16_PORT_POE


async def test_handler_ports(unifi_controller):
    """Verify that device ports works."""
    ports = unifi_controller.ports
    assert len(ports.items()) == 0
    assert len(ports.values()) == 0

    assert "fc:ec:da:11:22:33_18" not in ports
    assert ports.get("fc:ec:da:11:22:33_18", "xy") == "xy"
    assert not isinstance(ports.get("fc:ec:da:11:22:33_18"), Port)
    unsub_all = ports.subscribe(mock_subscribe_all := Mock())
    unsub_18 = ports.subscribe(
        mock_subscribe_18 := Mock(), id_filter="fc:ec:da:11:22:33_18"
    )
    unsub_added = ports.subscribe(
        mock_subscribe_added := Mock(), event_filter=ItemEvent.ADDED
    )
    unsub_changed = ports.subscribe(
        mock_subscribe_changed := Mock(), event_filter=ItemEvent.CHANGED
    )
    unsub_deleted = ports.subscribe(
        mock_subscribe_deleted := Mock(), event_filter=ItemEvent.DELETED
    )
    unsub_bad = ports.subscribe(mock_subscribe_bad := Mock(), id_filter="bad")

    # Add ports
    unifi_controller.devices.process_raw([SWITCH_16_PORT_POE])
    assert next(iter(ports)) == "fc:ec:da:11:22:33_1"
    assert "fc:ec:da:11:22:33_18" in ports
    assert isinstance(ports.get("fc:ec:da:11:22:33_18"), Port)
    assert isinstance(ports["fc:ec:da:11:22:33_18"], Port)
    assert len(ports.values()) == 18
    assert mock_subscribe_all.call_count == 18
    mock_subscribe_all.assert_called_with(ItemEvent.ADDED, "fc:ec:da:11:22:33_18")
    mock_subscribe_18.assert_called_once()
    assert mock_subscribe_added.call_count == 18
    mock_subscribe_changed.assert_not_called()
    mock_subscribe_deleted.assert_not_called()
    mock_subscribe_bad.assert_not_called()

    # Update ports
    unifi_controller.devices.process_raw([SWITCH_16_PORT_POE])
    assert len(ports.values()) == 18
    assert mock_subscribe_all.call_count == 36
    mock_subscribe_all.assert_called_with(ItemEvent.CHANGED, "fc:ec:da:11:22:33_18")
    assert mock_subscribe_18.call_count == 2
    assert mock_subscribe_added.call_count == 18
    assert mock_subscribe_changed.call_count == 18
    mock_subscribe_deleted.assert_not_called()
    mock_subscribe_bad.assert_not_called()

    # Remove ports
    unifi_controller.devices.remove_item(SWITCH_16_PORT_POE)
    assert len(ports.values()) == 0
    assert mock_subscribe_all.call_count == 54
    mock_subscribe_all.assert_called_with(ItemEvent.DELETED, "fc:ec:da:11:22:33_18")
    assert mock_subscribe_18.call_count == 3
    assert mock_subscribe_added.call_count == 18
    assert mock_subscribe_changed.call_count == 18
    assert mock_subscribe_deleted.call_count == 18
    mock_subscribe_bad.assert_not_called()

    unsub_all()
    unsub_18()
    unsub_added()
    unsub_changed()
    unsub_deleted()
    unsub_bad()

    unsub_all()
    unsub_all()


async def test_handler_process_device_no_index(unifi_controller):
    """Verify that device ports works."""
    ports = unifi_controller.ports
    unifi_controller.devices.process_raw([{"mac": "1", "port_table": [{}]}])
    assert len(ports.items()) == 0


@pytest.mark.parametrize("device_payload", [[SWITCH_16_PORT_POE]])
async def test_port(unifi_controller, _mock_endpoints):
    """Verify that device port model works."""
    await unifi_controller.devices.update()
    port = unifi_controller.ports["fc:ec:da:11:22:33_1"]

    assert port.ifname is None
    assert port.media == "GE"
    assert port.name == "Port 1"
    assert port.port_idx == 1
    assert port.poe_class == "Unknown"
    assert port.poe_caps == 7
    assert port.poe_enable is False
    assert port.poe_mode == "auto"
    assert port.poe_power == "0.00"
    assert port.poe_voltage == "0.00"
    assert port.portconf_id == "5a32aa4ee4babd4452422ddd22222"
    assert port.port_poe is True
    assert port.up is True

    assert repr(port) == "<Port 1: Poe False>"
