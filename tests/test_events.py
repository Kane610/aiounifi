"""Test events.

pytest --cov-report term-missing --cov=aiounifi.events tests/test_events.py
"""

from unittest.mock import Mock

import pytest

from aiounifi.interfaces.events import EventHandler
from aiounifi.models.event import Event, EventKey
from aiounifi.models.message import Message, MessageKey, Meta

from .fixtures import EVENT_SWITCH_16_CONNECTED, EVENT_WIRELESS_CLIENT_CONNECTED

EVENT_HANDLER_DATA = [
    (None, True),  # No filters
    (EventKey.SWITCH_LOST_CONTACT, True),  # Filter correct
    (EventKey.SWITCH_CONNECTED, False),  # Filter incorrect
]


@pytest.mark.parametrize(("event_filter", "expected"), EVENT_HANDLER_DATA)
async def test_event_handler(event_filter, expected):
    """Verify event handler behaves according to configured filters."""
    event_handler = EventHandler(controller=Mock())

    filters = {}
    if event_filter:
        filters["event_filter"] = event_filter

    unsubscribe_callback = event_handler.subscribe(mock_callback := Mock(), **filters)
    assert len(event_handler) == 1
    assert unsubscribe_callback

    event_handler.handler(
        Message(
            meta=Meta("ok", MessageKey.EVENT, {}),
            data={
                "_id": "5eae7fe02ab79c00f9d38960",
                "datetime": "2020-05-03T08:25:04Z",
                "key": "EVT_SW_Lost_Contact",
                "msg": "Switch[00:..:00] was disconnected",
                "site_id": "default",
                "subsystem": "lan",
                "sw": "00:..:00",
                "sw_name": "switch name",
                "time": 1588494304030,
            },
        ),
    )
    assert mock_callback.called is expected

    unsubscribe_callback()
    assert len(event_handler) == 0


async def test_unsupported_event_key():
    """Test empty event."""
    event = Event({"key": "unsupported"})
    assert event.key == EventKey.UNKNOWN


async def test_empty_event():
    """Test empty event."""
    empty = Event({})

    with pytest.raises(KeyError):
        assert empty.event
    with pytest.raises(KeyError):
        assert empty.key
    with pytest.raises(KeyError):
        assert empty.datetime
    with pytest.raises(KeyError):
        assert empty.msg
    with pytest.raises(KeyError):
        assert empty.time
    assert empty.mac == ""
    assert empty.ap == ""
    assert empty.bytes == 0
    assert empty.channel == 0
    assert empty.duration == 0
    assert empty.hostname == ""
    assert empty.radio == ""
    assert empty.subsystem == ""
    assert empty.site_id == ""
    assert empty.ssid == ""


async def test_client_event():
    """Test client event."""
    event_data = EVENT_WIRELESS_CLIENT_CONNECTED["data"][0]
    client = Event(event_data)

    assert client.event == "EVT_WU_Connected"
    assert client.key == EventKey.WIRELESS_CLIENT_CONNECTED
    assert client.datetime == "2020-04-24T18:37:36Z"
    assert (
        client.msg
        == "User[00:00:00:00:00:01] has connected to AP[80:2a:a8:00:01:02] "
        + 'with SSID "SSID" on "channel 44(na)"'
    )
    assert client.time == 1587753456179
    assert client.mac == "00:00:00:00:00:01"
    assert client.ap == "80:2a:a8:00:01:02"
    assert client.bytes == 0
    assert client.channel == 44
    assert client.duration == 0
    assert client.hostname == "client"
    assert client.radio == "na"
    assert client.subsystem == "wlan"
    assert client.site_id == "5a32aa4ee4b0412345678910"
    assert client.ssid == "SSID"


async def test_device_event():
    """Test device event."""
    event_data = EVENT_SWITCH_16_CONNECTED["data"][0]
    device = Event(event_data)

    assert device.event == "EVT_SW_Connected"
    assert device.key == EventKey.SWITCH_CONNECTED
    assert device.datetime == "2020-05-03T08:35:35Z"
    assert device.msg == "Switch[fc:ec:da:11:22:33] was connected"
    assert device.time == 1588494935241
    assert device.mac == "fc:ec:da:11:22:33"
    assert device.ap == ""
    assert device.bytes == 0
    assert device.channel == 0
    assert device.duration == 0
    assert device.hostname == ""
    assert device.radio == ""
    assert device.subsystem == "lan"
    assert device.site_id == "5a32aa4ee4b0412345678910"
    assert device.ssid == ""
    assert device.version_from == ""
    assert device.version_to == ""
