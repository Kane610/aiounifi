"""WLANs as part of a UniFi network."""

from dataclasses import dataclass
import io
from typing import NotRequired, Self, TypedDict

import segno.helpers

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
    hide_ssid: NotRequired[bool]
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
    x_passphrase: NotRequired[str]


@dataclass
class WlanListRequest(ApiRequest):
    """Request object for wlan list."""

    @classmethod
    def create(cls) -> Self:
        """Create wlan list request."""
        return cls(method="get", path="/rest/wlanconf")


@dataclass
class WlanChangePasswordRequest(ApiRequest):
    """Request object for wlan password change."""

    @classmethod
    def create(cls, wlan_id: str, password: str) -> Self:
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
    def create(cls, wlan_id: str, enable: bool) -> Self:
        """Create wlan enable request."""
        return cls(
            method="put",
            path=f"/rest/wlanconf/{wlan_id}",
            data={"enabled": enable},
        )


def wlan_qr_code(
    name: str,
    password: str | None,
    kind: str = "png",
    scale: int = 4,
    hidden: bool = False,
) -> bytes:
    """Generate WLAN QR code."""
    buffer = io.BytesIO()
    qr_code = segno.helpers.make_wifi(
        ssid=name, password=password, security="WPA", hidden=hidden
    )
    qr_code.save(out=buffer, kind=kind, scale=scale)
    return buffer.getvalue()


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
    def hide_ssid(self) -> bool | None:
        """Hide SSID."""
        return self.raw.get("hide_ssid")

    @property
    def is_guest(self) -> bool | None:
        """Is WLAN a guest network."""
        return self.raw.get("is_guest")

    @property
    def mac_filter_enabled(self) -> bool | None:
        """Is MAC filtering enabled."""
        return self.raw.get("mac_filter_enabled")

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
        return self.raw.get("minrate_na_enabled")

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
        return self.raw.get("minrate_ng_cck_rates_enabled")

    @property
    def minrate_ng_data_rate_kbps(self) -> int:
        """Minrate NG data rate kbps."""
        return self.raw["minrate_ng_data_rate_kbps"]

    @property
    def minrate_ng_enabled(self) -> bool | None:
        """Is minrate NG enabled."""
        return self.raw.get("minrate_ng_enabled")

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
        return self.raw.get("name_combine_enabled")

    @property
    def name_combine_suffix(self) -> str | None:
        """Suffix for 2.4GHz SSID if name is not combined."""
        return self.raw.get("name_combine_suffix")

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
    def x_passphrase(self) -> str | None:
        """Passphrase."""
        return self.raw.get("x_passphrase")
