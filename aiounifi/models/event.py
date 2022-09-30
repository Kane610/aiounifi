"""Event messages on state changes."""

#  https://demo.ui.com/manage/locales/en/eventStrings.json?v=5.4.11.2

from dataclasses import dataclass
import enum
import logging
from typing import Any, Final, TypedDict, final

LOGGER = logging.getLogger(__name__)


class EventKey(enum.Enum):
    """Key as part of event data object.

    "data": [{"key": "EVT_LU_Disconnected"}].
    """

    CONTROLLER_UPDATE_AVAILABLE = "EVT_AD_Update_Available"

    ACCESS_POINT_ADOPTED = "EVT_AP_Adopted"
    ACCESS_POINT_CONFIGURED = "EVT_AP_Configured"
    ACCESS_POINT_CONNECTED = "EVT_AP_Connected"
    ACCESS_POINT_DELETED = "EVT_AP_Deleted"
    ACCESS_POINT_LOST_CONTACT = "EVT_AP_Lost_Contact"
    ACCESS_POINT_AUTO_READOPTED = "EVT_AP_AutoReadopted"
    ACCESS_POINT_RESTARTED = "EVT_AP_Restarted"
    ACCESS_POINT_RESTARTED_UNKNOWN = "EVT_AP_RestartedUnknown"
    ACCESS_POINT_UPGRADED = "EVT_AP_Upgraded"

    GATEWAY_ADOPTED = "EVT_GW_Adopted"
    GATEWAY_CONFIGURED = "EVT_GW_Configured"
    GATEWAY_CONNECTED = "EVT_GW_Connected"
    GATEWAY_DELETED = "EVT_GW_Deleted"
    GATEWAY_LOST_CONTACT = "EVT_GW_Lost_Contact"
    GATEWAY_RESTARTED = "EVT_GW_Restarted"
    GATEWAY_RESTARTED_UNKNOWN = "EVT_GW_RestartedUnknown"
    GATEWAY_UPGRADED = "EVT_GW_Upgraded"

    SWITCH_ADOPTED = "EVT_SW_Adopted"
    SWITCH_CONFIGURED = "EVT_SW_Configured"
    SWITCH_CONNECTED = "EVT_SW_Connected"
    SWITCH_DELETED = "EVT_SW_Deleted"
    SWITCH_LOST_CONTACT = "EVT_SW_Lost_Contact"
    SWITCH_OVERHEAT = "EVT_SW_Overheat"
    SWITCH_POE_OVERLOAD = "EVT_SW_POE_Overload"
    SWITCH_POE_DISCONNECT = "EVT_SW_PoeDisconnect"
    SWITCH_RESTARTED = "EVT_SW_Restarted"
    SWITCH_RESTARTED_UNKNOWN = "EVT_SW_RestartedUnknown"
    SWITCH_UPGRADED = "EVT_SW_Upgraded"

    WIRED_CLIENT_CONNECTED = "EVT_LU_Connected"
    WIRED_CLIENT_DISCONNECTED = "EVT_LU_Disconnected"
    WIRED_CLIENT_BLOCKED = "EVT_LC_Blocked"
    WIRED_CLIENT_UNBLOCKED = "EVT_LC_Unblocked"
    WIRELESS_CLIENT_CONNECTED = "EVT_WU_Connected"
    WIRELESS_CLIENT_DISCONNECTED = "EVT_WU_Disconnected"
    WIRELESS_CLIENT_BLOCKED = "EVT_WC_Blocked"
    WIRELESS_CLIENT_UNBLOCKED = "EVT_WC_Unblocked"
    WIRELESS_CLIENT_ROAM = "EVT_WU_Roam"
    WIRELESS_CLIENT_ROAMRADIO = "EVT_WU_RoamRadio"
    WIRELESS_GUEST_CONNECTED = "EVT_WG_Connected"
    WIRELESS_GUEST_DISCONNECTED = "EVT_WG_Disconnected"
    WIRELESS_GUEST_ROAM = "EVT_WG_Roam"
    WIRELESS_GUEST_ROAMRADIO = "EVT_WG_RoamRadio"

    IPS_ALERT = "EVT_IPS_IpsAlert"

    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> "EventKey":
        """Set default enum member if an unknown value is provided."""
        LOGGER.warning("Unsupported event key %s", value)
        return EventKey.UNKNOWN


CONTROLLER_UPDATE_AVAILABLE: Final = EventKey.CONTROLLER_UPDATE_AVAILABLE.value

ACCESS_POINT_ADOPTED: Final = EventKey.ACCESS_POINT_ADOPTED.value
ACCESS_POINT_CONFIGURED: Final = EventKey.ACCESS_POINT_CONFIGURED.value
ACCESS_POINT_CONNECTED: Final = EventKey.ACCESS_POINT_CONNECTED.value
ACCESS_POINT_DELETED: Final = EventKey.ACCESS_POINT_DELETED.value
ACCESS_POINT_LOST_CONTACT: Final = EventKey.ACCESS_POINT_LOST_CONTACT.value
ACCESS_POINT_RESTARTED: Final = EventKey.ACCESS_POINT_RESTARTED.value
ACCESS_POINT_RESTARTED_UNKNOWN: Final = EventKey.ACCESS_POINT_RESTARTED_UNKNOWN.value
ACCESS_POINT_UPGRADED: Final = EventKey.ACCESS_POINT_UPGRADED.value

GATEWAY_ADOPTED: Final = EventKey.GATEWAY_ADOPTED.value
GATEWAY_CONFIGURED: Final = EventKey.GATEWAY_CONFIGURED.value
GATEWAY_CONNECTED: Final = EventKey.GATEWAY_CONNECTED.value
GATEWAY_DELETED: Final = EventKey.GATEWAY_DELETED.value
GATEWAY_LOST_CONTACT: Final = EventKey.GATEWAY_LOST_CONTACT.value
GATEWAY_RESTARTED: Final = EventKey.GATEWAY_RESTARTED.value
GATEWAY_RESTARTED_UNKNOWN: Final = EventKey.GATEWAY_RESTARTED_UNKNOWN.value
GATEWAY_UPGRADED: Final = EventKey.GATEWAY_UPGRADED.value

SWITCH_ADOPTED: Final = EventKey.SWITCH_ADOPTED.value
SWITCH_CONFIGURED: Final = EventKey.SWITCH_CONFIGURED.value
SWITCH_CONNECTED: Final = EventKey.SWITCH_CONNECTED.value
SWITCH_DELETED: Final = EventKey.SWITCH_DELETED.value
SWITCH_LOST_CONTACT: Final = EventKey.SWITCH_LOST_CONTACT.value
SWITCH_OVERHEAT: Final = EventKey.SWITCH_OVERHEAT.value
SWITCH_POE_OVERLOAD: Final = EventKey.SWITCH_POE_OVERLOAD.value
SWITCH_POE_DISCONNECT: Final = EventKey.SWITCH_POE_DISCONNECT.value
SWITCH_RESTARTED: Final = EventKey.SWITCH_RESTARTED.value
SWITCH_RESTARTED_UNKNOWN: Final = EventKey.SWITCH_RESTARTED_UNKNOWN.value
SWITCH_UPGRADED: Final = EventKey.SWITCH_UPGRADED.value

WIRED_CLIENT_CONNECTED: Final = EventKey.WIRED_CLIENT_CONNECTED.value
WIRED_CLIENT_DISCONNECTED: Final = EventKey.WIRED_CLIENT_DISCONNECTED.value
WIRED_CLIENT_BLOCKED: Final = EventKey.WIRED_CLIENT_BLOCKED.value
WIRED_CLIENT_UNBLOCKED: Final = EventKey.WIRED_CLIENT_UNBLOCKED.value
WIRELESS_CLIENT_CONNECTED: Final = EventKey.WIRELESS_CLIENT_CONNECTED.value
WIRELESS_CLIENT_DISCONNECTED: Final = EventKey.WIRELESS_CLIENT_DISCONNECTED.value
WIRELESS_CLIENT_BLOCKED: Final = EventKey.WIRELESS_CLIENT_BLOCKED.value
WIRELESS_CLIENT_UNBLOCKED: Final = EventKey.WIRELESS_CLIENT_UNBLOCKED.value
WIRELESS_CLIENT_ROAM: Final = EventKey.WIRELESS_CLIENT_ROAM.value
WIRELESS_CLIENT_ROAMRADIO: Final = EventKey.WIRELESS_CLIENT_ROAMRADIO.value
WIRELESS_GUEST_CONNECTED: Final = EventKey.WIRELESS_GUEST_CONNECTED.value
WIRELESS_GUEST_DISCONNECTED: Final = EventKey.WIRELESS_GUEST_DISCONNECTED.value
WIRELESS_GUEST_ROAM: Final = EventKey.WIRELESS_GUEST_ROAM.value
WIRELESS_GUEST_ROAMRADIO: Final = EventKey.WIRELESS_GUEST_ROAMRADIO.value

CLIENT_EVENTS: Final = (
    WIRED_CLIENT_CONNECTED,
    WIRED_CLIENT_DISCONNECTED,
    WIRED_CLIENT_BLOCKED,
    WIRED_CLIENT_UNBLOCKED,
    WIRELESS_CLIENT_CONNECTED,
    WIRELESS_CLIENT_DISCONNECTED,
    WIRELESS_CLIENT_BLOCKED,
    WIRELESS_CLIENT_UNBLOCKED,
    WIRELESS_CLIENT_ROAM,
    WIRELESS_CLIENT_ROAMRADIO,
    WIRELESS_GUEST_CONNECTED,
    WIRELESS_GUEST_DISCONNECTED,
    WIRELESS_GUEST_ROAM,
    WIRELESS_GUEST_ROAMRADIO,
)
DEVICE_EVENTS: Final = (
    ACCESS_POINT_ADOPTED,
    ACCESS_POINT_CONFIGURED,
    ACCESS_POINT_CONNECTED,
    ACCESS_POINT_DELETED,
    ACCESS_POINT_LOST_CONTACT,
    ACCESS_POINT_RESTARTED,
    ACCESS_POINT_RESTARTED_UNKNOWN,
    ACCESS_POINT_UPGRADED,
    GATEWAY_ADOPTED,
    GATEWAY_CONFIGURED,
    GATEWAY_CONNECTED,
    GATEWAY_DELETED,
    GATEWAY_LOST_CONTACT,
    GATEWAY_RESTARTED,
    GATEWAY_RESTARTED_UNKNOWN,
    GATEWAY_UPGRADED,
    SWITCH_ADOPTED,
    SWITCH_CONFIGURED,
    SWITCH_CONNECTED,
    SWITCH_DELETED,
    SWITCH_LOST_CONTACT,
    SWITCH_OVERHEAT,
    SWITCH_POE_OVERLOAD,
    SWITCH_POE_DISCONNECT,
    SWITCH_RESTARTED,
    SWITCH_RESTARTED_UNKNOWN,
    SWITCH_UPGRADED,
)


class TypedEvent(TypedDict):
    """Event type definition."""

    _id: str
    ap: str
    bytes: int
    channel: int
    client: str
    datetime: str
    duration: int
    guest: str
    gw: str
    hostname: str
    key: str
    msg: str
    network: str
    radio: str
    site_id: str
    ssid: str
    sw: str
    sw_name: str
    subsystem: str
    time: int
    user: str
    version_from: str
    version_to: str


@dataclass
class Event2:
    """Event type definition.

    NOT DONE
    """

    _id: str
    ap: str
    bytes: int
    channel: int
    client: str
    datetime: str
    duration: int
    guest: str
    gw: str
    hostname: str
    key: EventKey
    event: str
    msg: str
    network: str
    radio: str
    site_id: str
    ssid: str
    sw: str
    sw_name: str
    subsystem: str
    time: int
    user: str
    version_from: str
    version_to: str

    def mac(self) -> str:
        """Help retrieve mac from event."""
        return self.client or self.guest or self.user or self.ap or self.gw or self.sw

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event2":
        """Create data container instance from dict."""
        return cls(
            _id=data["_id"],
            datetime=data["datetime"],
            event=data["key"],
            key=EventKey(data["key"]),
            msg=data["msg"],
            time=data["time"],
            ap=data.get("ap", ""),
            bytes=data.get("bytes", 0),
            channel=data.get("channel", 0),
            client=data.get("client", ""),
            duration=data.get("duration", 0),
            guest=data.get("guest", ""),
            gw=data.get("gw", ""),
            hostname=data.get("hostname", ""),
            network=data.get("network", ""),
            radio=data.get("radio", ""),
            site_id=data.get("site_id", ""),
            ssid=data.get("ssid", ""),
            sw=data.get("sw", ""),
            sw_name=data.get("sw_name", ""),
            subsystem=data.get("subsystem", ""),
            user=data.get("user", ""),
            version_from=data.get("version_from", ""),
            version_to=data.get("version_to", ""),
        )


@final
class Event:
    """UniFi event."""

    # raw: TypedEvent

    # def __init__(self, raw: TypedEvent) -> None:
    # def __init__(self, raw: dict[str, Any]) -> None:
    def __init__(self, raw: Any) -> None:
        """Initialize event."""
        self.raw: TypedEvent = raw

    @property
    def datetime(self) -> str:
        """Datetime of event '2020-03-01T15:35:08Z'."""
        return self.raw["datetime"]

    @property
    def key(self) -> EventKey:
        """Event key e.g. 'EVT_WU_Disconnected'."""
        return EventKey(self.raw["key"])

    @property
    def event(self) -> str:
        """Event key e.g. 'EVT_WU_Disconnected'.

        To be removed.
        """
        return self.raw["key"]

    @property
    def msg(self) -> str:
        """Message 'User[00:00:00:00:00:01] disconnected from "Access point" (1h 27m connected, 58.97M bytes, last AP[00:11:22:33:44:55])'."""
        return self.raw["msg"]

    @property
    def time(self) -> int:
        """Time of event 1583076908000."""
        return self.raw["time"]

    @property
    def mac(self) -> str:
        """MAC of client or device."""
        if self.client:
            return self.client
        if self.device:
            return self.device
        return ""

    @property
    def ap(self) -> str:
        """Access point connected to."""
        return self.raw.get("ap", "")

    @property
    def bytes(self) -> int:
        """Bytes of data consumed."""
        return self.raw.get("bytes", 0)

    @property
    def channel(self) -> int:
        """Wi-Fi channel."""
        return self.raw.get("channel", 0)

    @property
    def client(self) -> str:
        """MAC address of client."""
        return (
            self.raw.get("user")
            or self.raw.get("client")
            or self.raw.get("guest")
            or ""
        )

    @property
    def device(self) -> str:
        """MAC address of device."""
        return self.raw.get("ap") or self.raw.get("gw") or self.raw.get("sw") or ""

    @property
    def duration(self) -> int:
        """Duration."""
        return self.raw.get("duration", 0)

    @property
    def hostname(self) -> str:
        """Nice name."""
        return self.raw.get("hostname", "")

    @property
    def radio(self) -> str:
        """Radio."""
        return self.raw.get("radio", "")

    @property
    def subsystem(self) -> str:
        """Subsystem like 'lan' or 'wlan'."""
        return self.raw.get("subsystem", "")

    @property
    def site_id(self) -> str:
        """Site ID."""
        return self.raw.get("site_id", "")

    @property
    def ssid(self) -> str:
        """SSID."""
        return self.raw.get("ssid", "")

    @property
    def version_from(self) -> str:
        """Version from."""
        return self.raw.get("version_from", "")

    @property
    def version_to(self) -> str:
        """Version to."""
        return self.raw.get("version_to", "")
