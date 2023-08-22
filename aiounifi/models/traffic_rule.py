"""Traffic rules as part of a UniFi network."""

from dataclasses import dataclass

from typing_extensions import NotRequired, TypedDict
from typing import TYPE_CHECKING, Any

from .api import ApiItem, ApiRequest
"""
{
    "_id":"63586097a5b3ff09d27963ca",
    "action":"BLOCK",
    "app_category_ids":[],
    "app_ids":[],
    "bandwidth_limit":
    {
        "download_limit_kbps":1024,
        "enabled":false,
        "upload_limit_kbps":1024
    },
    "description":"Hannah's WAN",
    "domains":[],
    "enabled":true,
    "ip_addresses":[],
    "ip_ranges":[],
    "matching_target":"INTERNET",
    "network_ids":[],
    "regions":[],
    "schedule":
    {
        "mode":"EVERY_DAY",
        "repeat_on_days":[],
        "time_all_day":false,
        "time_range_end":"07:00",
        "time_range_start":"18:00"
    },
    "target_devices":
    [
        {
            "client_mac":"2c:db:07:95:7f:d6",
            "type":"CLIENT"
        },
        {
            "client_mac":"04:6c:59:33:bf:9e",
            "type":"CLIENT"
        },
        {
            "client_mac":"92:be:20:0b:c4:1c",
            "type":"CLIENT"
        },
        {
            "client_mac":"d0:81:7a:db:db:36",
            "type":"CLIENT"
        },
        {
            "client_mac":"2c:db:07:d6:45:6b",
            "type":"CLIENT"
        },
        {
            "client_mac":"04:6c:59:2d:99:20",
            "type":"CLIENT"
        },
        {
            "client_mac":"de:22:49:8e:dd:1d",
            "type":"CLIENT"
        }
    ]
}
"""
class BandwidthLimit(TypedDict):
    """Bandwith limit type definition"""
    download_limit_kbps: int
    enabled: bool
    upload_limit_kbps: int

class PortRange(TypedDict):
    port_start: int
    port_stop: int
class IPAdress(TypedDict):
    ip_or_subnet: str
    ip_version: str
    port_ranges: list[PortRange]
    ports: list[int]

class IPRange(TypedDict):
    ip_start: str
    ip_stop: str
    ip_version: str

class Schedule(TypedDict):
    date_end: str
    date_start: str
    mode: str
    repeat_on_days: list[str]
    time_all_day: bool
    time_range_end: str
    time_range_start: str

class TargetDevice(TypedDict):
    client_mac: NotRequired[str]
    network_id: NotRequired[str]
    type: str
class TypedTrafficRule(TypedDict):
    """Traffic rule type definition."""

    _id: str
    action: str
    app_category_ids: list[str]
    app_ids: list[str]
    bandwidth_limit: BandwidthLimit
    description: str
    domains: list[str]
    enabled: bool
    ip_addresses: list[IPAdress]
    ip_ranges: list[IPRange]
    matching_target: str
    network_ids: list[str]
    regions: list[str]
    schedule: Schedule
    target_devices: list[TargetDevice]


@dataclass
class TrafficRuleRequest(ApiRequest):
    """Data class with required properties of a traffic rule request."""
    """We need a way to indicate if, for our model, the v2 API must be called.
    Therefore an intermediate dataclass 'TrafficRuleRequest' is made,
    for passing the correct path. This way, we do not need to alter any of the
    other classes that not need to know about the version of the api used.
    With the refactoring of the aiounifi-library, this is now possible.
    """

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        return f"/proxy/network/v2/api/site/{site}{self.path}"

@dataclass
class TrafficRuleListRequest(TrafficRuleRequest):
    """Request object for traffic rule list."""

    @classmethod
    def create(cls) -> "TrafficRuleListRequest":
        """Create traffic rule request."""
        return cls(method="get", path="/trafficrules", data=None)

@dataclass
class TrafficRuleEnableRequest(TrafficRuleRequest):
    """Request object for wlan enable."""

    @classmethod
    def create(cls, traffic_rule: dict[str, Any], enable: bool) -> "TrafficRuleEnableRequest":
        """Create traffic rule enable request."""
        traffic_rule['enabled'] = enable
        return cls(
            method="put",
            path=f"/trafficrules/{traffic_rule['_id']}",
            data=traffic_rule,
        )
    """
    {
        'errorCode': 400, 
        'message': 'updateTrafficRule.arg2.action: must not be null, 
                    updateTrafficRule.arg2.targetDevices: must not be empty, 
                    updateTrafficRule.arg2.matchingTarget: must not be null'                    
    }
    {'code': 'api.err.MissingIpAddressesOrIpRanges', 'errorCode': 400, 'message': 'Missing IP Addresses or IP Ranges'}    
    {
        '_id': '64628771859d5b11aa050792', 
    *   'action': 'BLOCK', 
        'app_category_ids': [], 
        'app_ids': [], 
        'bandwidth_limit': 
        {
            'download_limit_kbps': 1024, 
            'enabled': False, 
            'upload_limit_kbps': 1024
        }, 
        'description': 'nts', 
        'domains': [], 
        'enabled': True, 
        'ip_addresses': 
        [
            {
                'ip_or_subnet': '192.168.1.2', 
                'ip_version': 'v4', 
                'port_ranges': [{'port_start': 35, 'port_stop': 100}], 
                'ports': []
            }
        ], 
        'ip_ranges': [{'ip_start': '192.168.1.10', 'ip_stop': '192.168.1.22', 'ip_version': 'v4'}], 
    *   'matching_target': 'IP', 
        'network_ids': [], 
        'regions': [], 
        'schedule': 
        {
            'date_end': '2023-05-22', 
            'date_start': '2023-05-15', 
            'mode': 'CUSTOM', 
            'repeat_on_days': ['mon', 'thu'], 
            'time_all_day': False, 
            'time_range_end': '12:00', 
            'time_range_start': '09:00'
        }, 
    *   'target_devices': [{'network_id': '63e6a02941a10204ac6c74f2', 'type': 'NETWORK'}]}
    """


class TrafficRule(ApiItem):
    """Represent a WLAN configuration."""

    raw: TypedTrafficRule

    @property
    def id(self) -> str:
        """ID of traffic rule."""
        return self.raw["_id"]

    @property
    def description(self) -> str:
        """Description given by user to traffic rule."""
        return self.raw["description"]


    @property
    def enabled(self) -> bool:
        """Is traffic rule enabled."""
        return self.raw["enabled"]

    @property
    def action(self) -> str:
        """What action is defined by this traffic rule"""
        return self.raw["action"]

    @property
    def matching_target(self) -> str:
        """What target is matched by this traffic rule"""
        return self.raw["matching_target"]

    @property
    def target_devices(self) -> list[dict[str, str]]:
        """What target devices are affected by this traffic rule"""
        return self.raw["target_devices"]

