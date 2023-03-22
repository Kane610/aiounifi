"""WLANs as part of a UniFi network."""

from dataclasses import dataclass

from typing_extensions import NotRequired, TypedDict

from .api import ApiItem, ApiRequest


class TypedWlan(TypedDict):
    """Wlan type definition."""

    _id: str
    bc_filter_enabled: bool
    bc_filter_list: list[str]
    dtim_mode: str
    dtim_na: int
    dtim_ng: int
    enabled: bool
    group_rekey: int
    is_guest: NotRequired[bool]
    mac_filter_enabled: NotRequired[bool]
    mac_filter_list: list[str]
    mac_filter_policy: str
    minrate_na_advertising_rates: bool
    minrate_na_beacon_rate_kbps: int
    minrate_na_data_rate_kbps: int
    minrate_na_enabled: NotRequired[bool]
    minrate_na_mgmt_rate_kbps: int
    minrate_ng_advertising_rates: bool
    minrate_ng_beacon_rate_kbps: int
    minrate_ng_cck_rates_enabled: NotRequired[bool]
    minrate_ng_data_rate_kbps: int
    minrate_ng_enabled: NotRequired[bool]
    minrate_ng_mgmt_rate_kbps: int
    name: str
    name_combine_enabled: NotRequired[bool]
    name_combine_suffix: NotRequired[str]
    no2ghz_oui: bool
    schedule: list[str]
    security: str
    site_id: str
    usergroup_id: str
    wep_idx: int
    wlangroup_id: str
    wpa_enc: str
    wpa_mode: str
    x_iapp_key: str
    x_passphrase: str


@dataclass
class WlanChangePasswordRequest(ApiRequest):
    """Request object for wlan password change."""

    @classmethod
    def create(cls, wlan_id: str, password: str) -> "WlanChangePasswordRequest":
        """Create wlan password change request."""
        return cls(
            method="put",
            path=f"/rest/wlanconf/{wlan_id}",
            data={"x_passphrase": password},
        )


@dataclass
class WlanEnableRequest(ApiRequest):
    """Request object for wlan enable."""

    @classmethod
    def create(cls, wlan_id: str, enable: bool) -> "WlanEnableRequest":
        """Create wlan enable request."""
        return cls(
            method="put",
            path=f"/rest/wlanconf/{wlan_id}",
            data={"enabled": enable},
        )


class Wlan(ApiItem):
    """Represent a WLAN configuration."""

    raw: TypedWlan

    @property
    def id(self) -> str:
        """ID of WLAN."""
        return self.raw["_id"]

    @property
    def bc_filter_enabled(self) -> bool:
        """Is BC filter enabled."""
        return self.raw.get("bc_filter_enabled", False)

    @property
    def bc_filter_list(self) -> list[str]:
        """List of BC filters."""
        return self.raw["bc_filter_list"]

    @property
    def dtim_mode(self) -> str:
        """DTIM mode."""
        return self.raw["dtim_mode"]

    @property
    def dtim_na(self) -> int:
        """DTIM NA."""
        return self.raw["dtim_na"]

    @property
    def dtim_ng(self) -> int:
        """DTIM NG."""
        return self.raw["dtim_ng"]

    @property
    def enabled(self) -> bool:
        """Is WLAN enabled."""
        return self.raw["enabled"]

    @property
    def group_rekey(self) -> int:
        """Group rekey."""
        return self.raw["group_rekey"]

    @property
    def is_guest(self) -> bool | None:
        """Is WLAN a guest network."""
        if "is_guest" in self.raw:
            return self.raw["is_guest"]
        return None

    @property
    def mac_filter_enabled(self) -> bool | None:
        """Is MAC filtering enabled."""
        if "mac_filter_enabled" in self.raw:
            return self.raw["mac_filter_enabled"]
        return None

    @property
    def mac_filter_list(self) -> list[str]:
        """List of MAC filters."""
        return self.raw["mac_filter_list"]

    @property
    def mac_filter_policy(self) -> str:
        """MAC filter policy."""
        return self.raw["mac_filter_policy"]

    @property
    def minrate_na_advertising_rates(self) -> bool:
        """Minrate NA advertising rates."""
        return self.raw["minrate_na_advertising_rates"]

    @property
    def minrate_na_beacon_rate_kbps(self) -> int:
        """Minrate NA beacon rate kbps."""
        return self.raw["minrate_na_beacon_rate_kbps"]

    @property
    def minrate_na_data_rate_kbps(self) -> int:
        """Minrate NA data rate kbps."""
        return self.raw["minrate_na_data_rate_kbps"]

    @property
    def minrate_na_enabled(self) -> bool | None:
        """Is minrate NA enabled."""
        if "minrate_na_enabled" in self.raw:
            return self.raw["minrate_na_enabled"]
        return None

    @property
    def minrate_na_mgmt_rate_kbps(self) -> int:
        """Minrate NA management rate kbps."""
        return self.raw["minrate_na_mgmt_rate_kbps"]

    @property
    def minrate_ng_advertising_rates(self) -> bool:
        """Minrate NG advertising rates."""
        return self.raw["minrate_ng_advertising_rates"]

    @property
    def minrate_ng_beacon_rate_kbps(self) -> int:
        """Minrate NG beacon rate kbps."""
        return self.raw["minrate_ng_beacon_rate_kbps"]

    @property
    def minrate_ng_cck_rates_enabled(self) -> bool | None:
        """Is minrate NG CCK rates enabled."""
        if "minrate_ng_cck_rates_enabled" in self.raw:
            return self.raw["minrate_ng_cck_rates_enabled"]
        return None

    @property
    def minrate_ng_data_rate_kbps(self) -> int:
        """Minrate NG data rate kbps."""
        return self.raw["minrate_ng_data_rate_kbps"]

    @property
    def minrate_ng_enabled(self) -> bool | None:
        """Is minrate NG enabled."""
        if "minrate_ng_enabled" in self.raw:
            return self.raw["minrate_ng_enabled"]
        return None

    @property
    def minrate_ng_mgmt_rate_kbps(self) -> int:
        """Minrate NG management rate kbps."""
        return self.raw["minrate_ng_mgmt_rate_kbps"]

    @property
    def name(self) -> str:
        """WLAN name."""
        return self.raw["name"]

    @property
    def name_combine_enabled(self) -> bool | None:
        """If 2.5 and 5 GHz SSIDs should be combined."""
        if "name_combine_enabled" in self.raw:
            return self.raw["name_combine_enabled"]
        return None

    @property
    def name_combine_suffix(self) -> str | None:
        """Suffix for 2.4GHz SSID if name is not combined."""
        if "name_combine_suffix" in self.raw:
            return self.raw["name_combine_suffix"]
        return None

    @property
    def no2ghz_oui(self) -> bool:
        """No 2GHz OUI."""
        return self.raw["no2ghz_oui"]

    @property
    def schedule(self) -> list[str]:
        """Schedule list."""
        return self.raw["schedule"]

    @property
    def security(self) -> str:
        """Security."""
        return self.raw["security"]

    @property
    def site_id(self) -> str:
        """WLAN site ID."""
        return self.raw["site_id"]

    @property
    def usergroup_id(self) -> str:
        """WLAN user group ID."""
        return self.raw["usergroup_id"]

    @property
    def wep_idx(self) -> int:
        """WEP index."""
        return self.raw["wep_idx"]

    @property
    def wlangroup_id(self) -> str:
        """WLAN group ID."""
        return self.raw["wlangroup_id"]

    @property
    def wpa_enc(self) -> str:
        """WPA encryption."""
        return self.raw["wpa_enc"]

    @property
    def wpa_mode(self) -> str:
        """WPA mode."""
        return self.raw["wpa_mode"]

    @property
    def x_iapp_key(self) -> str:
        """X iapp key."""
        return self.raw["x_iapp_key"]

    @property
    def x_passphrase(self) -> str:
        """X passphrase."""
        return self.raw["x_passphrase"]
