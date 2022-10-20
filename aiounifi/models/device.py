"""UniFi devices are network infrastructure.

Access points, Gateways, Switches.
"""

from __future__ import annotations

from collections.abc import Iterator, ValuesView
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Any, TypedDict

from .api import APIItem
from .event import Event
from .request_object import RequestObject

if TYPE_CHECKING:
    from ..controller import Controller

LOGGER = logging.getLogger(__name__)


class TypedDeviceAntennaTable(TypedDict):
    """Device antenna table type definition."""

    default: bool
    id: int
    name: str
    wifi0_gain: int
    wifi1_gain: int


class TypedDeviceConfigNetwork(TypedDict):
    """Device config network type definition."""

    ip: str
    type: str


class TypedDeviceEthernetOverrides(TypedDict):
    """Device ethernet overrides type definition."""

    ifname: str
    networkgroup: str


class TypedDeviceEthernetTable(TypedDict):
    """Device ethernet table type definition."""

    mac: str
    name: str
    num_port: int


class TypedDeviceLastUplink(TypedDict):
    """Device last uplink type definition."""

    port_idx: int
    type: str
    uplink_mac: str
    uplink_device_name: str
    uplink_remote_port: int


class TypedDeviceLldpTable(TypedDict):
    """Device LLDP table type definition."""

    chassis_id: str
    chassis_id_subtype: str
    is_wired: bool
    local_port_idx: int
    local_port_name: str
    port_id: str


class TypedDeviceNetworkTable(TypedDict):
    """Device network table type definition."""

    _id: str
    attr_hidden_id: str
    attr_no_delete: bool
    dhcp_relay_enabled: bool
    dhcpd_dns_1: str
    dhcpd_dns_enabled: bool
    dhcpd_enabled: bool
    dhcpd_gateway_enabled: bool
    dhcpd_leasetime: int
    dhcpd_start: str
    dhcpd_stop: str
    dhcpd_time_offset_enabled: bool
    dhcpd_unifi_controller: str
    domain_name: str
    enabled: bool
    ip: str
    ip_subnet: str
    is_guest: bool
    is_nat: bool
    lte_lan_enabled: bool
    mac: str
    name: str
    networkgroup: str
    num_sta: int
    purpose: str
    rx_bytes: int
    rx_packets: int
    site_id: str
    tx_bytes: int
    tx_packets: int
    up: str
    vlan_enabled: bool


class TypedDeviceOutletOverrides(TypedDict, total=False):
    """Device outlet overrides type definition."""

    cycle_enabled: bool
    index: int
    has_relay: bool
    has_metering: bool
    name: str
    relay_state: bool


class TypedDeviceOutletTable(TypedDict):
    """Device outlet table type definition."""

    cycle_enabled: bool
    index: int
    has_relay: bool
    has_metering: bool
    name: str
    outlet_caps: int
    outlet_voltage: str
    outlet_current: str
    outlet_power: str
    outlet_power_factor: str
    relay_state: bool


class TypedDevicePortOverrides(TypedDict, total=False):
    """Device port overrides type definition."""

    poe_mode: str
    port_idx: int
    portconf_id: str


class TypedDevicePortTableLldpTable(TypedDict):
    """Device port table mac table type definition."""

    lldp_chassis_id: str
    lldp_port_id: str
    lldp_system_name: str


class TypedDevicePortTableMacTable(TypedDict):
    """Device port table mac table type definition."""

    age: int
    mac: str
    static: bool
    uptime: int
    vlan: int


class TypedDevicePortTablePortDelta(TypedDict):
    """Device port table port delta type definition."""

    rx_bytes: int
    rx_packets: int
    time_delta: int
    time_delta_activity: int
    tx_bytes: int
    tx_packets: int


class TypedDevicePortTable(TypedDict):
    """Device port table type definition."""

    aggregated_by: bool
    attr_no_edit: bool
    autoneg: bool
    bytes_r: int
    dot1x_mode: str
    dot1x_status: str
    enable: bool
    flowctrl_rx: bool
    flowctrl_tx: bool
    full_duplex: bool
    ifname: str
    is_uplink: bool
    jumbo: bool
    lldp_table: list[TypedDevicePortTableLldpTable]
    mac_table: list[TypedDevicePortTableMacTable]
    masked: bool
    media: str
    name: str
    op_mode: str
    poe_caps: int
    poe_class: str
    poe_current: str
    poe_enable: bool
    poe_good: bool
    poe_mode: str
    poe_power: str
    poe_voltage: str
    port_delta: TypedDevicePortTablePortDelta
    port_idx: int
    port_poe: bool
    portconf_id: str
    rx_broadcast: int
    rx_bytes: int
    rx_bytes_r: int
    rx_dropped: int
    rx_errors: int
    rx_multicast: int
    rx_packets: int
    speed: int
    speed_caps: int
    stp_pathcost: int
    stp_state: str
    tx_broadcast: int
    tx_bytes: int
    tx_bytes_r: int
    tx_dropped: int
    tx_errors: int
    tx_multicast: int
    tx_packets: int
    up: bool


class TypedDeviceRadioTable(TypedDict):
    """Device radio table type definition."""

    antenna_gain: int
    builtin_ant_gain: int
    builtin_antenna: bool
    channel: int
    current_antenna_gain: int
    hard_noise_floor_enabled: bool
    has_dfs: bool
    has_fccdfs: bool
    ht: str
    is_11ac: bool
    max_txpower: int
    min_rssi_enabled: bool
    min_txpower: int
    name: str
    nss: int
    radio: str
    radio_caps: int
    sens_level_enabled: bool
    tx_power_mode: str
    wlangroup_id: str


class TypedDeviceRadioTableStats(TypedDict):
    """Device radio table statistics type definition."""

    ast_be_xmit: int
    ast_cst: int
    ast_txto: int
    channel: int
    cu_self_rx: int
    cu_self_tx: int
    cu_total: int
    extchannel: int
    gain: int
    guest_num_sta: int
    name: str
    num_sta: int
    radio: str
    satisfaction: int
    state: str
    tx_packets: str
    tx_power: str
    tx_retries: str
    user_num_sta: str


class TypedDeviceSwitchCaps(TypedDict):
    """Device switch caps type definition."""

    feature_caps: int
    max_aggregate_sessions: int
    max_mirror_sessions: int
    vlan_caps: int


class TypedDeviceSysStats(TypedDict):
    """Device sys stats type definition."""

    loadavg_1: str
    loadavg_15: str
    loadavg_5: str
    mem_buffer: int
    mem_total: int
    mem_used: int


class TypedDeviceSystemStats(TypedDict):
    """Device system stats type definition."""

    cpu: str
    mem: str
    uptime: str


class TypedDeviceUplink(TypedDict):
    """Device uplink type definition."""

    full_duplex: bool
    ip: str
    mac: str
    max_speed: int
    max_vlan: int
    media: str
    name: str
    netmask: str
    num_port: int
    rx_bytes: int
    rx_bytes_r: int
    rx_dropped: int
    rx_errors: int
    rx_multicast: int
    rx_packets: int
    speed: int
    tx_bytes: int
    tx_bytes_r: int
    tx_dropped: int
    tx_errors: int
    tx_packets: int
    type: str
    up: bool
    uplink_mac: str
    uplink_remote_port: int


class TypedDeviceWlanOverrides(TypedDict):
    """Device wlan overrides type definition."""

    name: str
    radio: str
    radio_name: str
    wlan_id: str


class TypedDevice(TypedDict):
    """Device type definition."""

    _id: str
    _uptime: int
    adoptable_when_upgraded: bool
    adopted: bool
    antenna_table: list[TypedDeviceAntennaTable]
    architecture: str
    board_rev: int
    bytes: int
    bytes_d: int
    bytes_r: int
    cfgversion: int
    config_network: TypedDeviceConfigNetwork
    connect_request_ip: str
    connect_request_port: str
    considered_lost_at: int
    country_code: int
    countrycode_table: list  # type: ignore[type-arg]
    device_id: str
    dhcp_server_table: list  # type: ignore[type-arg]
    disabled: bool
    disconnection_reason: str
    displayable_version: str
    dot1x_portctrl_enabled: bool
    downlink_table: list  # type: ignore[type-arg]
    element_ap_serial: str
    element_peer_mac: str
    element_uplink_ap_mac: str
    ethernet_overrides: list[TypedDeviceEthernetOverrides]
    ethernet_table: list[TypedDeviceEthernetTable]
    fan_level: int
    flowctrl_enabled: bool
    fw_caps: int
    gateway_mac: str
    general_temperature: int
    guest_num_sta: int
    guest_wlan_num_sta: int
    guest_token: str
    has_eth1: bool
    has_fan: bool
    has_speaker: bool
    has_temperature: bool
    hash_id: str
    hide_ch_width: str
    hw_caps: int
    inform_ip: str
    inform_url: str
    internet: bool
    ip: str
    isolated: bool
    jumboframe_enabled: bool
    kernel_version: str
    known_cfgversion: str
    last_seen: int
    last_uplink: TypedDeviceLastUplink
    lcm_brightness: int
    lcm_brightness_override: bool
    lcm_idle_timeout_override: bool
    lcm_night_mode_begins: str
    lcm_night_mode_enabled: bool
    lcm_night_mode_ends: str
    lcm_tracker_enabled: bool
    led_override: str
    led_override_color: str
    led_override_color_brightnes: int
    license_state: str
    lldp_table: list[TypedDeviceLldpTable]
    locating: bool
    mac: str
    manufacturer_id: int
    meshv3_peer_mac: str
    model: str
    model_in_eol: bool
    model_in_lts: bool
    model_incompatible: bool
    name: str
    network_table: list[TypedDeviceNetworkTable]
    next_heartbeat_at: int
    next_interval: int
    num_desktop: int
    num_handheld: int
    num_mobile: int
    num_sta: int
    outdoor_mode_override: str
    outlet_ac_power_budget: str
    outlet_ac_power_consumption: str
    outlet_enabled: bool
    outlet_overrides: list[TypedDeviceOutletOverrides]
    outlet_table: list[TypedDeviceOutletTable]
    overheating: bool
    power_source_ctrl_enabled: bool
    prev_non_busy_state: int
    provisioned_at: int
    port_overrides: list[TypedDevicePortOverrides]
    port_table: list[TypedDevicePortTable]
    radio_table: list[TypedDeviceRadioTable]
    radio_table_stats: list[TypedDeviceRadioTableStats]
    required_version: str
    rollupgrade: bool
    rx_bytes: int
    rx_bytes_d: int
    satisfaction: int
    scan_radio_table: list  # type: ignore[type-arg]
    scanning: bool
    serial: str
    site_id: str
    spectrum_scanning: bool
    ssh_session_table: list  # type: ignore[type-arg]
    start_connected_millis: int
    start_disconnected_millis: int
    stat: dict  # type: ignore[type-arg]
    state: int
    stp_priority: str
    stp_version: str
    switch_caps: TypedDeviceSwitchCaps
    sys_error_caps: int
    sys_stats: TypedDeviceSysStats
    syslog_key: str
    system_stats: TypedDeviceSystemStats
    two_phase_adopt: bool
    tx_bytes: int
    tx_bytes_d: int
    type: str
    unsupported: bool
    unsupported_reason: int
    upgradable: bool
    upgrade_state: int
    upgrade_to_firmware: str
    uplink: TypedDeviceUplink
    uplink_depth: int
    uplink_table: list  # type: ignore[type-arg]
    uptime: int
    user_num_sta: int
    user_wlan_num_sta: int
    usg_caps: int
    vap_table: list[dict]  # type: ignore[type-arg]
    version: str
    vwireEnabled: bool
    vwire_table: list  # type: ignore[type-arg]
    vwire_vap_table: list  # type: ignore[type-arg]
    wifi_caps: int
    wlan_overrides: list[TypedDeviceWlanOverrides]
    wlangroup_id_na: str
    wlangroup_id_ng: str
    x_aes_gcm: bool
    x_authkey: str
    x_fingerprint: str
    x_has_ssh_hostkey: bool
    x_inform_authkey: str
    x_ssh_hostkey_fingerprint: str
    x_vwirekey: str


@dataclass
class DevicePowerCyclePortRequest(RequestObject):
    """Request object for power cycle PoE port."""

    @classmethod
    def create(cls, mac: str, port_idx: int) -> "DevicePowerCyclePortRequest":
        """Create power cycle of PoE request."""
        return cls(
            method="post",
            path="/cmd/devmgr",
            data={
                "cmd": "power-cycle",
                "mac": mac,
                "port_idx": port_idx,
            },
        )


@dataclass
class DeviceRestartRequest(RequestObject):
    """Request object for device restart."""

    @classmethod
    def create(cls, mac: str, soft: bool = True) -> "DeviceRestartRequest":
        """Create device restart request.

        Hard is specifically for PoE switches and will additionally cycle PoE ports.
        """
        return cls(
            method="post",
            path="/cmd/devmgr",
            data={
                "cmd": "restart",
                "mac": mac,
                "reboot_type": "soft" if soft else "hard",
            },
        )


@dataclass
class DeviceUpgradeRequest(RequestObject):
    """Request object for device upgrade."""

    @classmethod
    def create(cls, mac: str) -> "DeviceUpgradeRequest":
        """Create device upgrade request."""
        return cls(
            method="post",
            path="/cmd/devmgr",
            data={
                "cmd": "upgrade",
                "mac": mac,
            },
        )


@dataclass
class DeviceSetOutletRelayRequest(RequestObject):
    """Request object for outlet relay state."""

    @classmethod
    def create(
        cls, device: Device, outlet_idx: int, state: bool
    ) -> "DeviceSetOutletRelayRequest":
        """Create device outlet relay state request.

        True:  outlet power output on.
        False: outlet power output off.
        """
        existing_override = False
        for outlet_override in device.outlet_overrides:
            if outlet_idx == outlet_override["index"]:
                outlet_override["relay_state"] = state
                existing_override = True
                break

        if not existing_override:
            device.outlet_overrides.append(
                {
                    "index": outlet_idx,
                    "name": device.outlets[outlet_idx].name,
                    "relay_state": state,
                }
            )

        return cls(
            method="put",
            path=f"/rest/device/{device.id}",
            data={"outlet_overrides": device.outlet_overrides},
        )


@dataclass
class DeviceSetOutletCycleEnabledRequest(RequestObject):
    """Request object for outlet cycle_enabled flag."""

    @classmethod
    def create(
        cls, device: Device, outlet_idx: int, state: bool
    ) -> "DeviceSetOutletCycleEnabledRequest":
        """Create device outlet outlet cycle_enabled flag request.

        True:  UniFi Network will power cycle this outlet if the internet goes down.
        False: UniFi Network will not power cycle this outlet if the internet goes down.
        """
        existing_override = False
        for outlet_override in device.outlet_overrides:
            if outlet_idx == outlet_override["index"]:
                outlet_override["cycle_enabled"] = state
                existing_override = True
                break

        if not existing_override:
            device.outlet_overrides.append(
                {
                    "index": outlet_idx,
                    "name": device.outlets[outlet_idx].name,
                    "cycle_enabled": state,
                }
            )

        return cls(
            method="put",
            path=f"/rest/device/{device.id}",
            data={"outlet_overrides": device.outlet_overrides},
        )


@dataclass
class DeviceSetPoePortModeRequest(RequestObject):
    """Request object for setting port POE mode."""

    @classmethod
    def create(
        cls, device: Device, port_idx: int, mode: str
    ) -> "DeviceSetPoePortModeRequest":
        """Create device set port poe mode request.

        Auto, 24v, passthrough, off.
        Make sure to not overwrite any existing configs.
        """
        existing_override = False
        for port_override in device.port_overrides:
            if "port_idx" in port_override and port_idx == port_override["port_idx"]:
                port_override["poe_mode"] = mode
                existing_override = True
                break

        if not existing_override:
            device.port_overrides.append(
                {
                    "port_idx": port_idx,
                    "portconf_id": device.ports[port_idx].portconf_id,
                    "poe_mode": mode,
                }
            )

        return cls(
            method="put",
            path=f"/rest/device/{device.id}",
            data={"port_overrides": device.port_overrides},
        )


class Device(APIItem):
    """Represents a network device."""

    raw: TypedDevice

    def __init__(
        self,
        raw: Any,
        controller: Controller,
    ) -> None:
        """Initialize device."""
        super().__init__(raw, controller)
        self.ports = Ports(self.port_table)
        self.outlets = Outlets(self.outlet_table)

    def update(
        self,
        raw: Any | None = None,
        event: Event | None = None,
    ) -> None:
        """Refresh data."""
        if raw:
            self.ports.update(raw.get("port_table", []))
            self.outlets.update(raw.get("outlet_table", []))
        super().update(raw, event)

    @property
    def board_revision(self) -> int:
        """Board revision of device."""
        return self.raw["board_rev"]

    @property
    def considered_lost_at(self) -> int:
        """When device is considered lost."""
        return self.raw["considered_lost_at"]

    @property
    def disabled(self) -> bool:
        """Is device disabled."""
        if "disabled" in self.raw:
            return self.raw["disabled"]
        return False

    @property
    def downlink_table(self) -> list[dict[str, Any]]:
        """All devices with device as uplink."""
        return self.raw.get("downlink_table", [])

    @property
    def id(self) -> str:
        """ID of device."""
        return self.raw["device_id"]

    @property
    def ip(self) -> str:
        """IP of device."""
        return self.raw["ip"]

    @property
    def fan_level(self) -> int | None:
        """Fan level of device."""
        return self.raw.get("fan_level")

    @property
    def has_fan(self) -> bool:
        """Do device have a fan."""
        return self.raw.get("has_fan", False)

    @property
    def last_seen(self) -> int | None:
        """When was device last seen."""
        return self.raw.get("last_seen")

    @property
    def lldp_table(self) -> list[TypedDeviceLldpTable]:
        """All clients and devices directly attached to device."""
        return self.raw.get("lldp_table", [])

    @property
    def mac(self) -> str:
        """MAC address of device."""
        return self.raw["mac"]

    @property
    def model(self) -> str:
        """Model of device."""
        return self.raw["model"]

    @property
    def name(self) -> str:
        """Name of device."""
        return self.raw.get("name", "")

    @property
    def next_heartbeat_at(self) -> int | None:
        """Next heart beat full UNIX time."""
        return self.raw.get("next_heartbeat_at")

    @property
    def next_interval(self) -> int:
        """Next heart beat in seconds."""
        return self.raw.get("next_interval", 30)

    @property
    def overheating(self) -> bool:
        """Is device overheating."""
        return self.raw.get("overheating", False)

    @property
    def outlet_overrides(self) -> list[TypedDeviceOutletOverrides]:
        """Overridden outlet configuration."""
        return self.raw.get("outlet_overrides", [])

    @property
    def outlet_table(self) -> list[TypedDeviceOutletTable]:
        """List of outlets."""
        return self.raw.get("outlet_table", [])

    @property
    def port_overrides(self) -> list[TypedDevicePortOverrides]:
        """Overridden port configuration."""
        return self.raw.get("port_overrides", [])

    @property
    def port_table(self) -> list[TypedDevicePortTable]:
        """List of ports and data."""
        return self.raw.get("port_table", [])

    @property
    def state(self) -> int:
        """State of device."""
        return self.raw["state"]

    @property
    def sys_stats(self) -> TypedDeviceSysStats:
        """Output from top."""
        return self.raw["sys_stats"]

    @property
    def type(self) -> str:
        """Type of device."""
        return self.raw["type"]

    @property
    def version(self) -> str:
        """Firmware version."""
        return self.raw["version"]

    @property
    def upgradable(self) -> bool:
        """Is a new firmware available."""
        return self.raw.get("upgradable", False)

    @property
    def upgrade_to_firmware(self) -> str:
        """Firmware version to update to."""
        return self.raw.get("upgrade_to_firmware", "")

    @property
    def uplink(self) -> TypedDeviceUplink:
        """Information about uplink."""
        return self.raw["uplink"]

    @property
    def uplink_depth(self) -> int | None:
        """Hops to gateway."""
        return self.raw.get("uplink_depth")

    @property
    def user_num_sta(self) -> int:
        """Amount of connected clients."""
        value = self.raw.get("user-num_sta")
        assert isinstance(value, int)
        return value

    @property
    def wlan_overrides(self) -> list[TypedDeviceWlanOverrides]:
        """Wlan configuration override."""
        return self.raw.get("wlan_overrides", [])

    async def set_outlet_relay_state(
        self, outlet_idx: int, state: bool
    ) -> list[dict[str, Any]]:
        """Set outlet relay state."""
        LOGGER.debug("Override outlet %d with relay_state %s", outlet_idx, str(state))
        return await self._controller.request(
            DeviceSetOutletRelayRequest.create(self, outlet_idx, state)
        )

    async def set_outlet_cycle_enabled(
        self, outlet_idx: int, state: bool
    ) -> list[dict[str, Any]]:
        """Set outlet cycle_enabled flag."""
        LOGGER.debug("Override outlet %d with cycle_enabled %s", outlet_idx, str(state))
        return await self._controller.request(
            DeviceSetOutletCycleEnabledRequest.create(self, outlet_idx, state)
        )

    async def set_port_poe_mode(self, port_idx: int, mode: str) -> list[dict[str, Any]]:
        """Set port poe mode."""
        LOGGER.debug("Override port %d with mode %s", port_idx, mode)
        return await self._controller.request(
            DeviceSetPoePortModeRequest.create(self, port_idx, mode)
        )

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Device {self.name}: {self.mac}>"


class Port:
    """Represents a network port."""

    def __init__(self, raw: TypedDevicePortTable) -> None:
        """Initialize port."""
        self.raw = raw

    @property
    def ifname(self) -> str:
        """Port name used by USG."""
        return self.raw.get("ifname", "")

    @property
    def media(self) -> str:
        """Media port is connected to."""
        return self.raw.get("media", "")

    @property
    def name(self) -> str:
        """Port name."""
        return self.raw["name"]

    @property
    def port_idx(self) -> int | None:
        """Port index."""
        return self.raw.get("port_idx")

    @property
    def poe_class(self) -> str:
        """Port POE class."""
        return self.raw.get("poe_class", "")

    @property
    def poe_enable(self) -> bool | None:
        """Is POE supported/requested by client."""
        return self.raw.get("poe_enable")

    @property
    def poe_mode(self) -> str:
        """Is POE auto, pasv24, passthrough, off or None."""
        return self.raw.get("poe_mode", "")

    @property
    def poe_power(self) -> str:
        """POE power usage."""
        return self.raw.get("poe_power", "")

    @property
    def poe_voltage(self) -> str:
        """POE voltage usage."""
        return self.raw.get("poe_voltage", "")

    @property
    def portconf_id(self) -> str:
        """Port configuration ID."""
        return self.raw.get("portconf_id", "")

    @property
    def port_poe(self) -> bool:
        """Is POE used."""
        return self.raw.get("port_poe") is True

    @property
    def up(self) -> bool | None:
        """Is port up."""
        if "up" in self.raw:
            return self.raw["up"]
        return None

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<{self.name}: Poe {self.poe_enable}>"


class Ports:
    """Represents ports on a device."""

    def __init__(self, raw: list[TypedDevicePortTable]) -> None:
        """Initialize port manager."""
        self.ports: dict[int | str, Port] = {}
        for raw_port in raw:
            port = Port(raw_port)

            if (index := port.port_idx) is not None:
                self.ports[index] = port
            elif ifname := port.ifname:
                self.ports[ifname] = port

    def update(self, raw: list[TypedDevicePortTable]) -> None:
        """Update ports."""
        for raw_port in raw:
            index: int | str | None = None

            if "port_idx" in raw_port:
                index = raw_port["port_idx"]

            elif "ifname" in raw_port:
                index = raw_port["ifname"]

            if index in self.ports:
                self.ports[index].raw = raw_port

    def values(self) -> ValuesView[Port]:
        """Return ports."""
        return self.ports.values()

    def __getitem__(self, obj_id: int) -> Port:
        """Get specific port based on key."""
        return self.ports[obj_id]

    def __iter__(self) -> Iterator[int | str]:
        """Iterate over ports."""
        return iter(self.ports)


class Outlet:
    """Represents an outlet."""

    def __init__(self, raw: TypedDeviceOutletTable) -> None:
        """Initialize outlet."""
        self.raw = raw

    @property
    def name(self) -> str:
        """Name of outlet."""
        return self.raw["name"]

    @property
    def index(self) -> int:
        """Outlet index."""
        return self.raw["index"]

    @property
    def has_relay(self) -> bool | None:
        """Is the outlet controllable."""
        if "has_relay" in self.raw:
            return self.raw["has_relay"]
        return None

    @property
    def relay_state(self) -> bool:
        """Is outlet power on."""
        return self.raw["relay_state"]

    @property
    def cycle_enabled(self) -> bool | None:
        """Modem Power Cycle."""
        if "cycle_enabled" in self.raw:
            return self.raw["cycle_enabled"]
        return None

    # Metering capabilities of outlet

    @property
    def has_metering(self) -> bool | None:
        """Is metering supported.

        Reported false by UP1 and UP6 which does not have power metering.
        Not reported by UPD Pro which does report power metering.
        """
        if "has_metering" in self.raw:
            return self.raw["has_metering"]
        return None

    @property
    def caps(self) -> int:
        """Unknown."""
        return self.raw["outlet_caps"]

    @property
    def voltage(self) -> str | None:
        """Voltage draw of outlet."""
        if "outlet_voltage" in self.raw:
            return self.raw["outlet_voltage"]
        return None

    @property
    def current(self) -> str | None:
        """Usage of outlet."""
        if "outlet_current" in self.raw:
            return self.raw["outlet_current"]
        return None

    @property
    def power(self) -> str | None:
        """Power consumption of the outlet."""
        if "outlet_power" in self.raw:
            return self.raw["outlet_power"]
        return None

    @property
    def power_factor(self) -> str | None:
        """Power factor."""
        if "outlet_power_factor" in self.raw:
            return self.raw["outlet_power_factor"]
        return None


class Outlets:
    """Represents outlets on a device."""

    def __init__(self, raw: list[TypedDeviceOutletTable]) -> None:
        """Initialize outlet manager."""
        self.outlets: dict[int, Outlet] = {}
        for raw_outlet in raw:
            outlet = Outlet(raw_outlet)
            self.outlets[outlet.index] = outlet

    def update(self, raw: list[TypedDeviceOutletTable]) -> None:
        """Update outlets."""
        for raw_outlet in raw:
            index = raw_outlet["index"]
            self.outlets[index].raw = raw_outlet

    def values(self) -> ValuesView[Outlet]:
        """Return outlets."""
        return self.outlets.values()

    def __getitem__(self, obj_id: int) -> Outlet:
        """Get specific outlet based on key."""
        return self.outlets[obj_id]

    def __iter__(self) -> Iterator[int]:
        """Iterate over outlets."""
        return iter(self.outlets)
