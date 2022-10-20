"""Manage events from UniFi Network Controller."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Final, Optional, Union

from ..models.event import Event
from ..models.message import Message, MessageKey

if TYPE_CHECKING:
    from ..controller import Controller

LOGGER = logging.getLogger(__name__)


SubscriptionCallback = Callable[[Message], Union[Event, str]]
SubscriptionType = tuple[
    SubscriptionCallback,
    Optional[tuple[MessageKey, ...]],
]
UnsubscribeType = Callable[[], None]

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


class MessageHandler:
    """Message handler class."""

    def __init__(self, controller: Controller) -> None:
        """Initialize message handler class."""
        self.controller = controller
        self._subscribers: list[SubscriptionType] = []

    def subscribe(
        self,
        callback: SubscriptionCallback,
        message_filter: tuple[MessageKey, ...] | MessageKey | None = None,
    ) -> UnsubscribeType:
        """Subscribe to messages.

        "callback" - callback function to call when on event.
        Return function to unsubscribe.
        """
        if isinstance(message_filter, MessageKey):
            message_filter = (message_filter,)

        subscription = (callback, message_filter)
        self._subscribers.append(subscription)

        def unsubscribe() -> None:
            self._subscribers.remove(subscription)

        return unsubscribe

    def handler(self, raw: dict[str, Any]) -> dict[str, set[Event | str]]:
        """Receive message from websocket and identifies where the message belong."""
        message_key = ""
        changes = set()

        if "meta" not in raw or "data" not in raw:
            return {}

        for raw_data in raw["data"]:
            data = Message.from_dict(
                {
                    "meta": raw["meta"],
                    "data": raw_data,
                }
            )
            if data.meta.message not in MESSAGE_TO_CHANGE:
                break

            message_key = MESSAGE_TO_CHANGE[data.meta.message]

            for callback, message_filter in self._subscribers:
                if (
                    message_filter is not None
                    and data.meta.message not in message_filter
                ):
                    continue

                change = callback(data)
                if data.meta.message in MESSAGE_TO_CHANGE and change:
                    changes.add(change)

        if message_key:
            return {message_key: changes}
        return {}

    def __len__(self) -> int:
        """List number of message subscribers."""
        return len(self._subscribers)
