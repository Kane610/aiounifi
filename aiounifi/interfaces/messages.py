"""Manage events from UniFi Network Controller."""

import logging
from typing import TYPE_CHECKING, Any, Callable

from ..models.message import Message, MessageKey

if TYPE_CHECKING:
    from ..controller import Controller

LOGGER = logging.getLogger(__name__)


SubscriptionCallback = Callable[[Message], None]
SubscriptionType = tuple[SubscriptionCallback, tuple[MessageKey, ...] | None]
UnsubscribeType = Callable[[], None]


class MessageHandler:
    """Message handler class."""

    def __init__(self, controller: "Controller") -> None:
        """Initialize message handler class."""
        self.controller = controller
        self._subscribers: list[SubscriptionType] = []
        self._subscribed_messages: set[MessageKey] = set()

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

        if message_filter is not None:
            self._subscribed_messages.update(message_filter)

        subscription = (callback, message_filter)
        self._subscribers.append(subscription)

        def unsubscribe() -> None:
            self._subscribers.remove(subscription)

        return unsubscribe

    def handler(self, raw: dict[str, Any]) -> None:
        """Receive message from websocket and identifies where the message belong."""
        if "meta" not in raw or "data" not in raw:
            return

        for raw_data in raw["data"]:
            data = Message.from_dict(
                {
                    "meta": raw["meta"],
                    "data": raw_data,
                }
            )
            if data.meta.message not in self._subscribed_messages:
                break

            for callback, message_filter in self._subscribers:
                if (
                    message_filter is not None
                    and data.meta.message not in message_filter
                ):
                    continue
                callback(data)

    def __len__(self) -> int:
        """List number of message subscribers."""
        return len(self._subscribers)
