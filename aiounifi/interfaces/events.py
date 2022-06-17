"""Manage events from UniFi Network Controller."""

from __future__ import annotations

import logging
from typing import Any, Callable, Final, Optional

from ..models.event import EventKey, MessageKey, WebsocketData

LOGGER = logging.getLogger(__name__)


SubscriptionType = tuple[
    Callable[[WebsocketData], set[str]],
    Optional[tuple[MessageKey, ...]],
    Optional[tuple[EventKey, ...]],
]
UnsubscribeType = Callable[[], None]


ATTR_MESSAGE: Final = "message"
ATTR_META: Final = "meta"
ATTR_DATA: Final = "data"

DATA_CLIENT: Final = "client"
DATA_CLIENT_REMOVED: Final = "client_removed"
DATA_DEVICE: Final = "device"
DATA_EVENT: Final = "event"
DATA_DPI_APP: Final = "dpi_app"
DATA_DPI_APP_REMOVED: Final = "dpi_app_removed"
DATA_DPI_GROUP: Final = "dpi_group"
DATA_DPI_GROUP_REMOVED: Final = "dpi_group_removed"

MESSAGE_TO_CHANGE = {
    MessageKey.EVENT: DATA_EVENT,
    MessageKey.CLIENT: DATA_CLIENT,
    MessageKey.CLIENT_REMOVED: DATA_CLIENT_REMOVED,
    MessageKey.DEVICE: DATA_DEVICE,
    MessageKey.DPI_APP_ADDED: DATA_DPI_APP,
    MessageKey.DPI_APP_UPDATED: DATA_DPI_APP,
    MessageKey.DPI_APP_REMOVED: DATA_DPI_APP_REMOVED,
    MessageKey.DPI_GROUP_ADDED: DATA_DPI_GROUP,
    MessageKey.DPI_GROUP_UPDATED: DATA_DPI_GROUP,
    MessageKey.DPI_GROUP_REMOVED: DATA_DPI_GROUP_REMOVED,
}


class EventHandler:
    """Event handler class."""

    def __init__(self, controller) -> None:
        """Initialize API items."""
        self.controller = controller
        self._subscribers: list[SubscriptionType] = []
        self._messages_of_interest: tuple[MessageKey, ...] = ()

    def subscribe(
        self,
        callback: Callable[[WebsocketData], set[str]],
        message_filter: tuple[MessageKey, ...] | MessageKey | None = None,
        *,
        event_filter: tuple[EventKey, ...] | EventKey | None = None,
    ) -> UnsubscribeType:
        """Subscribe to events.

        "callback" - callback function to call when on event.
        Return function to unsubscribe.
        """
        if isinstance(message_filter, MessageKey):
            message_filter = (message_filter,)
        if message_filter:
            self._messages_of_interest += message_filter

        if isinstance(event_filter, EventKey):
            event_filter = (event_filter,)

        subscription = (callback, message_filter, event_filter)
        self._subscribers.append(subscription)

        def unsubscribe() -> None:
            self._subscribers.remove(subscription)

        return unsubscribe

    def handler(self, raw: dict[str, Any]) -> dict[str, set]:
        """Receive event from websocket and identifies where the event belong."""
        message_key: str
        changes = set()

        if "meta" not in raw or "data" not in raw:
            return {}

        for raw_data in raw["data"]:
            data = WebsocketData.from_dict(
                {
                    "meta": raw["meta"],
                    "data": raw_data,
                }
            )
            if data.meta.message not in MESSAGE_TO_CHANGE:
                break

            message_key = MESSAGE_TO_CHANGE[data.meta.message]
            is_event = data.meta.message == MessageKey.EVENT

            for callback, message_filter, event_filter in self._subscribers:
                if (
                    message_filter is not None
                    and data.meta.message not in message_filter
                ):
                    continue
                if (
                    is_event
                    and event_filter is not None
                    and data.event.key not in event_filter
                ):
                    continue
                change = callback(data)
                if data.meta.message in MESSAGE_TO_CHANGE and change:
                    changes.add(change)

        if message_key:
            return {message_key: changes}
        return {}
