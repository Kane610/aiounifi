"""UniFi system information model."""

from dataclasses import dataclass
from typing import TypedDict

from .api import ApiItem, ApiRequest


class TypedSystemInfo(TypedDict):
    """System information type definition."""

    anonymous_controller_id: str
    autobackup: bool
    build: str
    console_display_version: str
    data_retention_days: int
    data_retention_time_in_hours_for_5minutes_scale: int
    data_retention_time_in_hours_for_daily_scale: int
    data_retention_time_in_hours_for_hourly_scale: int
    data_retention_time_in_hours_for_monthly_scale: int
    data_retention_time_in_hours_for_others: int
    debug_device: str
    debug_mgmt: str
    debug_sdn: str
    debug_setting_preference: str
    debug_system: str
    default_site_device_auth_password_alert: bool
    facebook_wifi_registered: bool
    has_webrtc_support: bool
    hostname: str
    https_port: int
    image_maps_use_google_engine: bool
    inform_port: int
    ip_addrs: list[str]
    is_cloud_console: bool
    live_chat: str
    name: str
    override_inform_host: bool
    portal_http_port: int
    previous_version: str
    radius_disconnect_running: bool
    sso_app_id: str
    sso_app_sec: str
    store_enabled: str
    timezone: str
    ubnt_device_type: str
    udm_version: str
    unifi_go_enabled: bool
    unsupported_device_count: int
    unsupported_device_list: list[str]
    update_available: bool
    update_downloaded: bool
    uptime: int
    version: str


@dataclass
class SystemInformationRequest(ApiRequest):
    """Request object for system information."""

    @classmethod
    def create(cls) -> "SystemInformationRequest":
        """Create system information request."""
        return cls(method="get", path="/stat/sysinfo")


class SystemInformation(ApiItem):
    """Represents a client network device."""

    raw: TypedSystemInfo

    @property
    def anonymous_controller_id(self) -> str:
        """Anonymous controller ID."""
        return self.raw["anonymous_controller_id"]

    @property
    def device_type(self) -> str:
        """Network host device type."""
        return self.raw["ubnt_device_type"]

    @property
    def hostname(self) -> str:
        """Host name."""
        return self.raw["hostname"]

    @property
    def ip_address(self) -> list[str]:
        """External IP address."""
        return self.raw["ip_addrs"]

    @property
    def is_cloud_console(self) -> bool:
        """Cloud hosted console."""
        return self.raw["is_cloud_console"]

    @property
    def name(self) -> str:
        """Name."""
        return self.raw["name"]

    @property
    def previous_version(self) -> str:
        """Previous application version."""
        return self.raw["previous_version"]

    @property
    def update_available(self) -> bool:
        """Application update available."""
        return self.raw["update_available"]

    @property
    def uptime(self) -> int:
        """Application uptime."""
        return self.raw["uptime"]

    @property
    def version(self) -> str:
        """Current application version."""
        return self.raw["version"]
