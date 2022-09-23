"""Messages from websocket."""

#  https://demo.ui.com/manage/locales/en/eventStrings.json?v=5.4.11.2

from dataclasses import dataclass
import enum
import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


class MessageKey(enum.Enum):
    """Message as part of meta object of event.

    "meta": {"rc": "ok", "message": "device:sync"}.
    """

    ALERT = "alert"
    CLIENT = "sta:sync"
    CLIENT_REMOVED = "user:delete"
    DEVICE = "device:sync"
    DEVICE_UPDATE = "device:update"
    UNIFI_DEVICE = "unifi-device:sync"
    EVENT = "events"
    DPI_APP_ADDED = "dpiapp:add"
    DPI_APP_REMOVED = "dpiapp:delete"
    DPI_APP_UPDATED = "dpiapp:sync"
    DPI_GROUP_ADDED = "dpigroup:add"
    DPI_GROUP_REMOVED = "dpigroup:delete"
    DPI_GROUP_UPDATED = "dpigroup:sync"

    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> "MessageKey":
        """Set default enum member if an unknown value is provided."""
        LOGGER.warning("Unsupported message key %s", value)
        return MessageKey.UNKNOWN


@dataclass
class Meta:
    """Meta description of UniFi websocket data."""

    rc: str
    message: MessageKey
    data: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Meta":
        """Create meta instance from dict."""
        return cls(
            rc=data.get("rc", ""),
            message=MessageKey(data.get("message", "")),
            data=data,
        )


@dataclass
class Message:
    """Websocket package representation."""

    meta: Meta
    data: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create data container instance from dict."""
        return cls(
            meta=Meta.from_dict(data["meta"]),
            data=data["data"],
        )
