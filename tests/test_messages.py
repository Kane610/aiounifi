"""Test messages.

pytest --cov-report term-missing --cov=aiounifi.messages tests/test_messages.py
"""

from unittest.mock import Mock, patch

import pytest

from aiounifi.interfaces.messages import MessageHandler
from aiounifi.models.message import Message, MessageKey

MESSAGE_HANDLER_DATA = [
    (None, False),  # No subscriber registered
    (MessageKey.CLIENT_REMOVED, True),  # Filter correct
    (MessageKey.CLIENT, False),  # Filter incorrect
    ((MessageKey.CLIENT, MessageKey.CLIENT_REMOVED), True),  # Filter correct
]


@pytest.mark.parametrize(("message_filter", "expected"), MESSAGE_HANDLER_DATA)
async def test_message_handler(message_filter, expected):
    """Verify message handler behaves according to configured filters."""
    message_handler = MessageHandler(controller=Mock())

    filters = {}
    if message_filter:
        filters["message_filter"] = message_filter

    unsubscribe_callback = message_handler.subscribe(mock_callback := Mock(), **filters)
    assert len(message_handler) == 1
    assert unsubscribe_callback

    message_handler.handler(
        {
            "meta": {
                "rc": "ok",
                "message": MessageKey.CLIENT_REMOVED.value,
            },
            "data": [{}],
        }
    )
    assert mock_callback.called is expected

    unsubscribe_callback()
    assert len(message_handler) == 0


async def test_unsupported_message_key(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate unsupported message key handling."""
    monkeypatch.setattr("aiounifi.models.message._unsupported_keys", set())
    for _ in range(2):
        message = Message.from_dict(
            {
                "meta": {
                    "rc": "ok",
                    "message": "unsupported:sync",
                },
                "data": {"x_password": "secret"},
            }
        )
        assert message.meta.message == MessageKey.UNKNOWN

    assert [record.getMessage() for record in caplog.records] == [
        "Unsupported message key unsupported:sync"
    ]
    assert "secret" not in caplog.text


@pytest.mark.parametrize(
    "key",
    [
        "account:add",
        "account:sync",
        "account:delete",
        "dhcpoption:add",
        "dhcpoption:delete",
        "firewallgroup:delete",
        "firewallrule:delete",
        "hotspotop:add",
        "hotspotop:delete",
        "portconf:add",
        "portconf:sync",
        "portconf:delete",
        "radiusprofile:add",
        "radiusprofile:sync",
        "radiusprofile:delete",
        "routing:add",
        "routing:sync",
        "routing:delete",
        "user:add",
        "usergroup:add",
        "usergroup:delete",
    ],
)
async def test_observed_message_keys_are_supported(key: str) -> None:
    """Verify message keys sent by a Network application are known."""
    assert MessageKey(key) is not MessageKey.UNKNOWN


@patch("aiounifi.interfaces.messages.LOGGER")
async def test_message_handler_bad_json_data(logger_mock):
    """Verify message handler catches json error."""
    MessageHandler(controller=Mock()).new_data("")
    assert logger_mock.debug.called
