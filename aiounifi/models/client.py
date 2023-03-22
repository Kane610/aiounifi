"""Clients are devices on a UniFi network."""

from dataclasses import dataclass
from typing import TypedDict

from .api import ApiItem, ApiRequest


class TypedClient(TypedDict):
    """Client type definition."""

    _id: str
    _is_guest_by_uap: bool
    _is_guest_by_ugw: bool
    _is_guest_by_usw: bool
    _last_seen_by_uap: int
    _last_seen_by_ugw: int
    _last_seen_by_usw: int
    _uptime_by_uap: int
    _uptime_by_ugw: int
    _uptime_by_usw: int
    anomalies: int
    ap_mac: str
    assoc_time: int
    authorized: bool
    blocked: bool
    bssid: str
    bytes_r: int
    ccq: int
    channel: int
    dev_cat: int
    dev_family: int
    dev_id: int
    dev_id_override: int
    dev_vendor: int
    device_name: str
    dhcpend_time: int
    disconnect_timestamp: int
    eagerly_discovered: bool
    essid: str
    fingerprint_engine_version: str
    fingerprint_override: bool
    fingerprint_source: int
    first_seen: int
    fixed_ip: str
    fw_version: str
    gw_mac: str
    hostname: str
    hostname_source: str
    idletime: int
    ip: str
    is_11r: bool
    is_guest: bool
    is_wired: bool
    last_seen: bool
    latest_assoc_time: bool
    mac: str
    name: str
    network: str
    network_id: str
    noise: int
    noted: bool
    os_class: int
    os_name: int
    oui: str
    powersave_enabled: bool
    qos_policy_applied: bool
    radio: str
    radio_name: str
    radio_proto: str
    rssi: int
    rx_bytes: int
    rx_packets: int
    rx_rate: int
    satisfaction: int
    score: int
    signal: int
    site_id: str
    sw_depth: int
    sw_mac: str
    sw_port: int
    tx_bytes: int
    tx_packets: int
    tx_power: int
    tx_rate: int
    tx_retries: int
    uptime: int
    use_fixedip: bool
    user_id: str
    usergroup_id: str
    vlan: int
    wifi_tx_attempts: int
    wired_rate_mbps: int
    wired_tx_bytes: int
    wired_rx_bytes: int
    wired_tx_packets: int
    wired_rx_packets: int
    wired_tx_bytes_r: int
    wired_rx_bytes_r: int


@dataclass
class ClientBlockRequest(ApiRequest):
    """Request object for client block."""

    @classmethod
    def create(cls, mac: str, block: bool) -> "ClientBlockRequest":
        """Create client block request."""
        return cls(
            method="post",
            path="/cmd/stamgr",
            data={
                "cmd": "block-sta" if block else "unblock-sta",
                "mac": mac,
            },
        )


@dataclass
class ClientReconnectRequest(ApiRequest):
    """Request object for client reconnect."""

    @classmethod
    def create(cls, mac: str) -> "ClientReconnectRequest":
        """Create client reconnect request."""
        return cls(
            method="post",
            path="/cmd/stamgr",
            data={
                "cmd": "kick-sta",
                "mac": mac,
            },
        )


@dataclass
class ClientRemoveRequest(ApiRequest):
    """Request object for client removal."""

    @classmethod
    def create(cls, macs: list[str]) -> "ClientRemoveRequest":
        """Create client removal request."""
        return cls(
            method="post",
            path="/cmd/stamgr",
            data={
                "cmd": "forget-sta",
                "macs": macs,
            },
        )


class Client(ApiItem):
    """Represents a client network device."""

    raw: TypedClient

    @property
    def access_point_mac(self) -> str:
        """MAC address of access point."""
        return self.raw.get("ap_mac", "")

    @property
    def association_time(self) -> int:
        """When was client associated with controller."""
        return self.raw.get("assoc_time", 0)

    @property
    def blocked(self) -> bool:
        """Is client blocked."""
        return self.raw.get("blocked", False)

    @property
    def device_name(self) -> str:
        """Device name of client."""
        return self.raw.get("device_name", "")

    @property
    def essid(self) -> str:
        """ESSID client is connected to."""
        return self.raw.get("essid", "")

    @property
    def firmware_version(self) -> str:
        """Firmware version of client."""
        return self.raw.get("fw_version", "")

    @property
    def first_seen(self) -> int:
        """When was client first seen."""
        return self.raw.get("first_seen", 0)

    @property
    def fixed_ip(self) -> str:
        """List IP if fixed IP is configured."""
        return self.raw.get("fixed_ip", "")

    @property
    def hostname(self) -> str:
        """Hostname of client."""
        return self.raw.get("hostname", "")

    @property
    def idle_time(self) -> int:
        """Idle time of client."""
        return self.raw.get("idletime", 0)

    @property
    def ip(self) -> str:
        """IP of client."""
        return self.raw.get("ip", "")

    @property
    def is_guest(self) -> bool:
        """Is client guest."""
        return self.raw.get("is_guest", False)

    @property
    def is_wired(self) -> bool:
        """Is client wired."""
        return self.raw.get("is_wired", False)

    @property
    def last_seen(self) -> int:
        """When was client last seen."""
        return self.raw.get("last_seen", 0)

    @property
    def last_seen_by_access_point(self) -> int:
        """When was client last seen by access point."""
        return self.raw.get("_last_seen_by_uap", 0)

    @property
    def last_seen_by_gateway(self) -> int:
        """When was client last seen by gateway."""
        return self.raw.get("_last_seen_by_ugw", 0)

    @property
    def last_seen_by_switch(self) -> int:
        """When was client last seen by network switch."""
        return self.raw.get("_last_seen_by_usw", 0)

    @property
    def latest_association_time(self) -> int:
        """When was client last associated with controller."""
        return self.raw.get("latest_assoc_time", 0)

    @property
    def mac(self) -> str:
        """MAC address of client."""
        return self.raw.get("mac", "")

    @property
    def name(self) -> str:
        """Name of client."""
        return self.raw.get("name", "")

    @property
    def oui(self) -> str:
        """Vendor string for client MAC."""
        return self.raw.get("oui", "")

    @property
    def powersave_enabled(self) -> bool | None:
        """Powersave functionality enabled for wireless client."""
        return self.raw.get("powersave_enabled")

    @property
    def site_id(self) -> str:
        """Site ID client belongs to."""
        return self.raw.get("site_id", "")

    @property
    def switch_depth(self) -> int | None:
        """How many layers of switches client is in."""
        return self.raw.get("sw_depth")

    @property
    def switch_mac(self) -> str:
        """MAC for switch client is connected to."""
        return self.raw.get("sw_mac", "")

    @property
    def switch_port(self) -> int | None:
        """Switch port client is connected to."""
        return self.raw.get("sw_port")

    @property
    def rx_bytes(self) -> int:
        """Bytes received over wireless connection."""
        return self.raw.get("rx_bytes", 0)

    @property
    def rx_bytes_r(self) -> int:
        """Bytes recently received over wireless connection."""
        value = self.raw.get("rx_bytes-r", 0)
        assert isinstance(value, int)
        return value

    @property
    def tx_bytes(self) -> int:
        """Bytes transferred over wireless connection."""
        return self.raw.get("tx_bytes", 0)

    @property
    def tx_bytes_r(self) -> int:
        """Bytes recently transferred over wireless connection."""
        value = self.raw.get("tx_bytes-r", 0)
        assert isinstance(value, int)
        return value

    @property
    def uptime(self) -> int:
        """Uptime of client."""
        return self.raw.get("uptime", 0)

    @property
    def uptime_by_access_point(self) -> int:
        """Uptime of client observed by access point."""
        return self.raw.get("_uptime_by_uap", 0)

    @property
    def uptime_by_gateway(self) -> int:
        """Uptime of client observed by gateway."""
        return self.raw.get("_uptime_by_ugw", 0)

    @property
    def uptime_by_switch(self) -> int:
        """Uptime of client observed by network switch."""
        return self.raw.get("_uptime_by_usw", 0)

    @property
    def wired_rate_mbps(self) -> int:
        """Wired rate in Mbps."""
        return self.raw.get("wired_rate_mbps", 0)

    @property
    def wired_rx_bytes(self) -> int:
        """Bytes received over wired connection."""
        value = self.raw.get("wired-rx_bytes", 0)
        assert isinstance(value, int)
        return value

    @property
    def wired_rx_bytes_r(self) -> int:
        """Bytes recently received over wired connection."""
        value = self.raw.get("wired-rx_bytes-r", 0)
        assert isinstance(value, int)
        return value

    @property
    def wired_tx_bytes(self) -> int:
        """Bytes transferred over wired connection."""
        value = self.raw.get("wired-tx_bytes", 0)
        assert isinstance(value, int)
        return value

    @property
    def wired_tx_bytes_r(self) -> int:
        """Bytes recently transferred over wired connection."""
        value = self.raw.get("wired-tx_bytes-r", 0)
        assert isinstance(value, int)
        return value
