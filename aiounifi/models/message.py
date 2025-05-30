"""Messages from websocket."""

from __future__ import annotations

from dataclasses import dataclass
import enum
import logging
from typing import Any, Self

LOGGER = logging.getLogger(__name__)


class MessageKey(enum.Enum):
    """Message as part of meta object of event.

    "meta": {"rc": "ok", "message": "device:sync"}.
    """

    ALERT = "alert"
    EVENT = "events"

    CLIENT = "sta:sync"
    CLIENT_REMOVED = "user:delete"
    CLIENT_UPDATED = "user:sync"
    DEVICE = "device:sync"
    DEVICE_ADD = "device:add"
    DEVICE_UPDATE = "device:update"
    DPI_APP_ADDED = "dpiapp:add"
    DPI_APP_REMOVED = "dpiapp:delete"
    DPI_APP_UPDATED = "dpiapp:sync"
    DPI_GROUP_ADDED = "dpigroup:add"
    DPI_GROUP_REMOVED = "dpigroup:delete"
    DPI_GROUP_UPDATED = "dpigroup:sync"
    FIREWALL_GROUP_ADDED = "firewallgroup:add"
    FIREWALL_GROUP_UPDATED = "firewallgroup:sync"
    FIREWALL_RULE_ADDED = "firewallrule:add"
    FIREWALL_RULE_UPDATED = "firewallrule:sync"
    NETWORK_CONF_UPDATED = "networkconf:sync"
    NOTIFICATION_TOAST = "notification-toast"
    PING_TEST_UPDATE = "ping-test:update"
    PORT_FORWARD_ADDED = "portforward:add"
    PORT_FORWARD_UPDATED = "portforward:sync"
    PORT_FORWARD_DELETED = "portforward:delete"
    SCHEDULE_TASK_ADDED = "scheduletask:add"
    SESSION_METADATA = "session-metadata:sync"
    SETTING_UPDATED = "setting:sync"
    SETUP_SYNC = "setup:sync"
    SPEED_TEST_UPDATE = "speed-test:update"
    UNIFI_DEVICE = "unifi-device:sync"
    UNIFI_DEVICE_ADD = "unifi-device:add"
    USER_GROUP_UPDATED = "usergroup:sync"
    VPN_CONNECT = "vpn:connect"
    VPN_DISCONNECT = "vpn:disconnect"
    VPN_CONNECTION_UPDATED = "vpn-connection:sync"
    WLAN_CONF_ADDED = "wlanconf:add"
    WLAN_CONF_UPDATED = "wlanconf:sync"
    WLAN_CONF_DELETED = "wlanconf:delete"

    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> MessageKey:
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
    def from_dict(cls, data: dict[str, Any]) -> Self:
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
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create data container instance from dict."""
        meta = Meta.from_dict(data["meta"])
        if meta.message is MessageKey.UNKNOWN:
            LOGGER.warning("Unsupported message %s", data)
        return cls(
            meta=meta,
            data=data["data"],
        )
