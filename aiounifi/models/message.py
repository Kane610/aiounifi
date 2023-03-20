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
    CLIENT_UPDATED = "user:sync"
    DEVICE = "device:sync"
    DEVICE_UPDATE = "device:update"
    DPI_APP_ADDED = "dpiapp:add"
    DPI_APP_REMOVED = "dpiapp:delete"
    DPI_APP_UPDATED = "dpiapp:sync"
    DPI_GROUP_ADDED = "dpigroup:add"
    DPI_GROUP_REMOVED = "dpigroup:delete"
    DPI_GROUP_UPDATED = "dpigroup:sync"
    EVENT = "events"
    FIREWALL_RULE_ADDED = "firewallrule:add"
    FIREWALL_RULE_UPDATED = "firewallrule:sync"
    NETWORK_CONF_UPDATED = "networkconf:sync"
    SETTING_UPDATED = "setting:sync"
    SPEED_TEST_UPDATE = "speed-test:update"
    UNIFI_DEVICE = "unifi-device:sync"
    WLAN_CONF_UPDATED = "wlanconf:sync"

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
        meta = Meta.from_dict(data["meta"])
        if meta.message == MessageKey.UNKNOWN:
            LOGGER.warning("Unsupported message %s", data)
        return cls(
            meta=meta,
            data=data["data"],
        )
