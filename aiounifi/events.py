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

        # {
        #     "meta": {"rc": "ok", "message": "events"},
        #     "data": [
        #         {
        #             "user": "dc:a6:32:05:81:90",
        #             "hostname": "rpi4",
        #             "network": "LAN",
        #             "duration": 367,
        #             "bytes": 42,
        #             "key": "EVT_LU_Disconnected",
        #             "subsystem": "lan",
        #             "site_id": "5a32aa4ee4b047ede36a859f",
        #             "time": 1579546533000,
        #             "datetime": "2020-01-20T18:55:33Z",
        #             "msg": 'User[dc:a6:32:05:81:90] disconnected from "LAN" (6m 7s connected, 42.00 bytes)',
        #             "_id": "5e25f9042ab79c00fde39886",
        #         }
        #     ],
        # }
        # {
        #     "meta": {"rc": "ok", "message": "events"},
        #     "data": [
        #         {
        #             "user": "b8:e8:56:3f:e9:96",
        #             "ssid": "PhG",
        #             "hostname": "mbpr",
        #             "ap": "80:2a:a8:c0:74:13",
        #             "duration": 201,
        #             "bytes": 1820713,
        #             "key": "EVT_WU_Disconnected",
        #             "subsystem": "wlan",
        #             "site_id": "5a32aa4ee4b047ede36a859f",
        #             "time": 1579549202000,
        #             "datetime": "2020-01-20T19:40:02Z",
        #             "msg": 'User[b8:e8:56:3f:e9:96] disconnected from "PhG" (3m 21s connected, 1.74M bytes, last AP[80:2a:a8:c0:74:13])',
        #             "_id": "5e26021a2ab79c00fde3cbc8",
        #         }
        #     ],
        # }
        # {
        #     "meta": {"rc": "ok", "message": "events"},
        #     "data": [
        #         {
        #             "user": "b8:e8:56:3f:e9:96",
        #             "network": "LAN",
        #             "key": "EVT_LU_Connected",
        #             "subsystem": "lan",
        #             "site_id": "5a32aa4ee4b047ede36a859f",
        #             "time": 1579549024893,
        #             "datetime": "2020-01-20T19:37:04Z",
        #             "msg": "User[b8:e8:56:3f:e9:96] has connected to LAN",
        #             "_id": "5e26022c2ab79c00fde3cca7",
        #         }
        #     ],
        # }

