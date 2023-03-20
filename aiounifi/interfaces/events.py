"""Manage events from UniFi Network Controller."""

import logging
from typing import TYPE_CHECKING, Callable

from ..models.event import Event, EventKey
from ..models.message import Message, MessageKey

if TYPE_CHECKING:
    from ..controller import Controller

LOGGER = logging.getLogger(__name__)


SubscriptionCallback = Callable[[Event], None]
SubscriptionType = tuple[SubscriptionCallback, tuple[EventKey, ...] | None]
UnsubscribeType = Callable[[], None]


class EventHandler:
    """Event handler class."""

    def __init__(self, controller: "Controller") -> None:
        """Initialize API items."""
        self.controller = controller
        self._subscribers: list[SubscriptionType] = []

        controller.messages.subscribe(self.handler, MessageKey.EVENT)

    def subscribe(
        self,
        callback: SubscriptionCallback,
        event_filter: tuple[EventKey, ...] | EventKey | None = None,
    ) -> UnsubscribeType:
        """Subscribe to events.

        "callback" - callback function to call when on event.
        Return function to unsubscribe.
        """
        if isinstance(event_filter, EventKey):
            event_filter = (event_filter,)

        subscription = (callback, event_filter)
        self._subscribers.append(subscription)

        def unsubscribe() -> None:
            self._subscribers.remove(subscription)

        return unsubscribe

    def handler(self, message: Message) -> None:
        """Receive event from message handler and identifies where the event belong."""
        event = Event(message.data)

        for callback, event_filter in self._subscribers:
            if event_filter is not None and event.key not in event_filter:
                continue
            callback(event)

    def __len__(self) -> int:
        """List number of event subscribers."""
        return len(self._subscribers)
