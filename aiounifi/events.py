"""Event messages on state changes."""

#  https://demo.ui.com/manage/locales/en/eventStrings.json?v=5.4.11.2

CONTROLLER_UPDATE_AVAILABLE = "EVT_AD_UPDATE_AVAILABLE"

ACCESS_POINT_ADOPTED = "EVT_AP_ADOPTED"
ACCESS_POINT_CONFIGURED = "EVT_AP_CONFIGURED"
ACCESS_POINT_CONNECTED = "EVT_AP_CONNECTED"
ACCESS_POINT_DELETED = "EVT_AP_DELETED"
ACCESS_POINT_RESTARTED = "EVT_AP_RESTARTED"
ACCESS_POINT_UPGRADED = "EVT_AP_UPGRADED"

GATEWAY_ADOPTED = "EVT_GW_ADOPTED"
GATEWAY_CONNECTED = "EVT_GW_CONNECTED"
GATEWAY_DELETED = "EVT_GW_DELETED"
GATEWAY_LOST_CONTACT = "EVT_GW_LOST_CONTACT"
GATEWAY_RESTART = "EVT_GW_RESTARTED"
GATEWAY_UPGRADED = "EVT_GW_UPGRADED"

SWITCH_ADOPTED = "EVT_SW_ADOPTED"
SWITCH_CONNECTED = "EVT_SW_CONNECTED"
SWITCH_DELETED = "EVT_SW_DELETED"
SWITCH_LOST_CONTACT = "EVT_SW_LOST_CONTACT"
SWITCH_OVERHEAT = "EVT_SW_OVERHEAT"
SWITCH_POE_OVERLOAD = "EVT_SW_POE_OVERLOAD"
SWITCH_POE_DISCONNECT = "EVT_SW_POE_DISCONNECT"
SWITCH_RESTARTED = "EVT_SW_RESTARTED"
SWITCH_UPGRADED = "EVT_SW_UPGRADED"

CLIENT_BLOCKED = "EVT_WC_BLOCKED"
CLIENT_UNBLOCKED = "EVT_WC_UNBLOCKED"
WIRED_CLIENT_CONNECTED = "EVT_LU_CONNECTED"
WIRED_CLIENT_DISCONNECTED = "EVT_LU_DISCONNECTED"
WIRELESS_CLIENT_CONNECTED = "EVT_WU_CONNECTED"
WIRELESS_CLIENT_DISCONNECTED = "EVT_WU_DISCONNECTED"
WIRELESS_GUEST_CONNECTED = "EVT_WG_CONNECTED"
WIRELESS_GUEST_DISCONNECTED = "EVT_WG_DISCONNECTED"


class event:
    def __init__(self, raw):
        self.raw = raw

    @property
    def event(self):
        return self.raw["key"]

    @property
    def msg(self):
        return self.raw["msg"]

    @property
    def time(self):
        return self.raw["time"]

    @property
    def datetime(self):
        return self.raw["datetime"]

    @property
    def client(self):
        return self.raw.get("user", "")

    @property
    def hostname(self):
        return self.raw.get("hostname", "")

    @property
    def subsystem(self):
        return self.raw.get("subsystem", "")

    @property
    def ssid(self):
        return self.raw.get("ssid", "")
