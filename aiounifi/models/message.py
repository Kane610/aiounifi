"""Messages from websocket."""

from __future__ import annotations

from dataclasses import dataclass
import enum
import logging
from typing import Any, Self

LOGGER = logging.getLogger(__name__)

# Unknown keys are logged once, their data can hold credentials
_unsupported_keys: set[str] = set()


class MessageKey(enum.Enum):
    """Message as part of meta object of event.

    "meta": {"rc": "ok", "message": "device:sync"}.
    """

    ALERT = "alert"
    EVENT = "events"

    ACCOUNT_ADDED = "account:add"
    ACCOUNT_UPDATED = "account:sync"
    ACCOUNT_DELETED = "account:delete"
    AFC_EVENT = "afc-event"
    CHANNEL_PLAN_ADDED = "channelplan:add"
    CHANNEL_PLAN_UPDATED = "channelplan:sync"
    CHANNEL_PLAN_DELETED = "channelplan:delete"
    CLIENT = "sta:sync"
    CLIENT_ADDED = "user:add"
    CLIENT_REMOVED = "user:delete"
    CLIENT_UPDATED = "user:sync"
    DEVICE = "device:sync"
    DEVICE_ADD = "device:add"
    DEVICE_UPDATE = "device:update"
    DEVICE_SDP_OFFER = "device:sdp-offer"
    DEVICE_UNMANAGED_ADD = "device-unmanaged:add"
    DEVICE_UNMANAGED_DELETE = "device-unmanaged:delete"
    DHCP_OPTION_ADDED = "dhcpoption:add"
    DHCP_OPTION_UPDATED = "dhcpoption:sync"
    DHCP_OPTION_DELETED = "dhcpoption:delete"
    DPI_APP_ADDED = "dpiapp:add"
    DPI_APP_REMOVED = "dpiapp:delete"
    DPI_APP_UPDATED = "dpiapp:sync"
    DPI_GROUP_ADDED = "dpigroup:add"
    DPI_GROUP_REMOVED = "dpigroup:delete"
    DPI_GROUP_UPDATED = "dpigroup:sync"
    DYNAMIC_DNS_ADDED = "dynamicdns:add"
    DYNAMIC_DNS_UPDATED = "dynamicdns:sync"
    DYNAMIC_DNS_DELETED = "dynamicdns:delete"
    FEATURE_CHANGE = "feature:change"
    FIREWALL_GROUP_ADDED = "firewallgroup:add"
    FIREWALL_GROUP_UPDATED = "firewallgroup:sync"
    FIREWALL_GROUP_DELETED = "firewallgroup:delete"
    FIREWALL_RULE_ADDED = "firewallrule:add"
    FIREWALL_RULE_UPDATED = "firewallrule:sync"
    FIREWALL_RULE_DELETED = "firewallrule:delete"
    FLOORPLAN_FILE_ADDED = "floorplan_file:add"
    FLOORPLAN_FILE_UPDATED = "floorplan_file:sync"
    FLOORPLAN_FILE_DELETED = "floorplan_file:delete"
    HOTSPOT2_CONF_ADDED = "hotspot2conf:add"
    HOTSPOT2_CONF_UPDATED = "hotspot2conf:sync"
    HOTSPOT2_CONF_DELETED = "hotspot2conf:delete"
    HOTSPOT_OPERATOR_ADDED = "hotspotop:add"
    HOTSPOT_OPERATOR_UPDATED = "hotspotop:sync"
    HOTSPOT_OPERATOR_DELETED = "hotspotop:delete"
    HOTSPOT_PACKAGE_ADDED = "hotspotpackage:add"
    HOTSPOT_PACKAGE_UPDATED = "hotspotpackage:sync"
    HOTSPOT_PACKAGE_DELETED = "hotspotpackage:delete"
    MBB_SPEED_TEST_UPDATE = "mbb-speed-test:update"
    MODEL_META_UPDATE = "model-meta:update"
    NETWORK_CONF_ADDED = "networkconf:add"
    NETWORK_CONF_UPDATED = "networkconf:sync"
    NETWORK_CONF_DELETED = "networkconf:delete"
    NOTIFICATION_TOAST = "notification-toast"
    PING_TEST_UPDATE = "ping-test:update"
    PORTAL_FILE_ADDED = "portalfile:add"
    PORTAL_FILE_UPDATED = "portalfile:sync"
    PORTAL_FILE_DELETED = "portalfile:delete"
    PORT_CONF_ADDED = "portconf:add"
    PORT_CONF_UPDATED = "portconf:sync"
    PORT_CONF_DELETED = "portconf:delete"
    PORT_FORWARD_ADDED = "portforward:add"
    PORT_FORWARD_UPDATED = "portforward:sync"
    PORT_FORWARD_DELETED = "portforward:delete"
    RADIO_AI_PLAN = "radio-ai:plan"
    RADIUS_PROFILE_ADDED = "radiusprofile:add"
    RADIUS_PROFILE_UPDATED = "radiusprofile:sync"
    RADIUS_PROFILE_DELETED = "radiusprofile:delete"
    ROUTING_ADDED = "routing:add"
    ROUTING_UPDATED = "routing:sync"
    ROUTING_DELETED = "routing:delete"
    SCAN_SCHEDULER_NEIGHBOR_SCAN = "scan-scheduler:neighbor-scan"
    SCHEDULE_TASK_ADDED = "scheduletask:add"
    SCHEDULE_TASK_UPDATED = "scheduletask:sync"
    SCHEDULE_TASK_DELETED = "scheduletask:delete"
    SESSION_METADATA = "session-metadata:sync"
    SETTING_ADDED = "setting:add"
    SETTING_UPDATED = "setting:sync"
    SETUP_SYNC = "setup:sync"
    SPATIAL_RECORD_ADDED = "spatialrecord:add"
    SPATIAL_RECORD_UPDATED = "spatialrecord:sync"
    SPATIAL_RECORD_DELETED = "spatialrecord:delete"
    SPEED_TEST_UPDATE = "speed-test:update"
    UNIFI_DEVICE = "unifi-device:sync"
    UNIFI_DEVICE_ADD = "unifi-device:add"
    UNIFI_DEVICE_UNMANAGED_ADD = "unifi-device-unmanaged:add"
    UNIFI_DEVICE_UNMANAGED_DELETE = "unifi-device-unmanaged:delete"
    USER_GROUP_ADDED = "usergroup:add"
    USER_GROUP_UPDATED = "usergroup:sync"
    USER_GROUP_DELETED = "usergroup:delete"
    VPN_CONNECT = "vpn:connect"
    VPN_DISCONNECT = "vpn:disconnect"
    VPN_CONNECTION_UPDATED = "vpn-connection:sync"
    VPN_USER_UPDATED = "vpn-users:sync"
    WLAN_CONF_ADDED = "wlanconf:add"
    WLAN_CONF_UPDATED = "wlanconf:sync"
    WLAN_CONF_DELETED = "wlanconf:delete"
    WLAN_GROUP_ADDED = "wlangroup:add"
    WLAN_GROUP_UPDATED = "wlangroup:sync"
    WLAN_GROUP_DELETED = "wlangroup:delete"

    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> MessageKey:
        """Set default enum member if an unknown value is provided."""
        if (key := str(value)) not in _unsupported_keys:
            _unsupported_keys.add(key)
            LOGGER.warning("Unsupported message key %s", key)
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
        return cls(
            meta=meta,
            data=data["data"],
        )
