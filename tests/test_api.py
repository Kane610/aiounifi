"""Test API handlers."""

from unittest.mock import Mock

import pytest

from aiounifi.interfaces.api_handlers import APIHandler, ItemEvent


@pytest.mark.parametrize(
    "event_filter",
    [
        None,
        {ItemEvent.ADDED, ItemEvent.CHANGED, ItemEvent.DELETED},
    ],
)
async def test_api_handler_subscriptions(event_filter):
    """Test process and remove item."""
    handler = APIHandler(Mock())
    handler.obj_id_key = "key"
    handler.item_cls = Mock()

    unsub = handler.subscribe(mock_subscribe_cb := Mock(), event_filter)

    handler.process_item({})
    mock_subscribe_cb.assert_not_called()

    handler.process_item({"key": "1"})
    mock_subscribe_cb.assert_called_with(ItemEvent.ADDED, "1")

    handler.process_item({"key": "1"})
    mock_subscribe_cb.assert_called_with(ItemEvent.CHANGED, "1")

    handler.remove_item({"key": "1"})
    mock_subscribe_cb.assert_called_with(ItemEvent.DELETED, "1")

    handler.remove_item({"key": "2"})

    # Process raw

    handler.process_raw([{"key": "2"}])
    mock_subscribe_cb.assert_called_with(ItemEvent.ADDED, "2")

    handler.process_raw([{"key": "2"}])
    mock_subscribe_cb.assert_called_with(ItemEvent.CHANGED, "2")

    handler.remove_item({"key": "2"})
    mock_subscribe_cb.assert_called_with(ItemEvent.DELETED, "2")

    unsub()

    unsub()  # Empty list of object ID

    handler._subscribers.clear()

    unsub()  # Object ID does not exist in subscribers


async def test_api_handler_subscriptions_event_filter_added():
    """Test process and remove item."""
    handler = APIHandler(Mock())
    handler.obj_id_key = "key"
    handler.item_cls = Mock()

    unsub = handler.subscribe(mock_subscribe_cb := Mock(), ItemEvent.ADDED)

    handler.process_item({})
    mock_subscribe_cb.assert_not_called()

    handler.process_item({"key": "1"})
    mock_subscribe_cb.assert_called_with(ItemEvent.ADDED, "1")

    handler.process_item({"key": "1"})
    assert mock_subscribe_cb.call_count == 1

    handler.remove_item({"key": "1"})
    assert mock_subscribe_cb.call_count == 1

    handler.remove_item({"key": "2"})

    # Process raw

    handler.process_raw([{"key": "2"}])
    mock_subscribe_cb.assert_called_with(ItemEvent.ADDED, "2")

    handler.process_raw([{"key": "2"}])
    assert mock_subscribe_cb.call_count == 2

    handler.remove_item({"key": "2"})
    assert mock_subscribe_cb.call_count == 2

    unsub()


async def test_api_handler_subscriptions_id_filter():
    """Test process and remove item."""
    handler = APIHandler(Mock())
    handler.obj_id_key = "key"
    handler.item_cls = Mock()

    unsub = handler.subscribe(mock_subscribe_cb := Mock(), id_filter="1")

    handler.process_item({})
    mock_subscribe_cb.assert_not_called()

    handler.process_item({"key": "1"})
    mock_subscribe_cb.assert_called_with(ItemEvent.ADDED, "1")

    handler.process_item({"key": "1"})
    mock_subscribe_cb.assert_called_with(ItemEvent.CHANGED, "1")

    handler.remove_item({"key": "1"})
    mock_subscribe_cb.assert_called_with(ItemEvent.DELETED, "1")

    handler.remove_item({"key": "2"})

    # Process raw

    handler.process_raw([{"key": "2"}])
    assert mock_subscribe_cb.call_count == 3

    handler.process_raw([{"key": "2"}])
    assert mock_subscribe_cb.call_count == 3

    handler.remove_item({"key": "2"})
    assert mock_subscribe_cb.call_count == 3

    unsub()
