"""Test API handlers."""

from unittest.mock import Mock

from aiounifi.interfaces.api_handlers import APIHandler, ItemEvent


async def test_api_handler_subscriptions():
    """Test process and remove item."""
    handler = APIHandler(Mock())
    handler.obj_id_key = "key"
    handler.item_cls = Mock()

    handler.subscribe(mock_subscribe_cb := Mock())

    assert handler.process_item({}) == ""
    mock_subscribe_cb.assert_not_called()

    assert handler.process_item({"key": 1}) == 1
    mock_subscribe_cb.assert_called_with(ItemEvent.ADDED, 1)

    assert handler.process_item({"key": 1}) == ""
    mock_subscribe_cb.assert_called_with(ItemEvent.CHANGED, 1)

    assert handler.remove_item({"key": 1}) == 1
    mock_subscribe_cb.assert_called_with(ItemEvent.DELETED, 1)

    assert handler.remove_item({"key": 2}) == ""

    # Process raw

    assert handler.process_raw([{}]) == set()

    assert handler.process_raw([{"key": 2}]) == {2}
    mock_subscribe_cb.assert_called_with(ItemEvent.ADDED, 2)

    assert handler.process_raw([{"key": 2}]) == set()
    mock_subscribe_cb.assert_called_with(ItemEvent.CHANGED, 2)

    assert handler.remove_item({"key": 2}) == 2
