"""WLANs as part of a UniFi network."""

from typing import Awaitable, Callable, List

from .api import APIItem, APIItems

URL = "/rest/wlanconf"  # List WLAN configuration


class Wlan(APIItem):
    """Represent a WLAN configuration."""

    @property
    def id(self) -> str:
        """ID of WLAN."""
        return self.raw["_id"]

    @property
    def bc_filter_enabled(self) -> bool:
        """Is BC filter enabled."""
        return self.raw.get("bc_filter_enabled", False)

    @property
    def bc_filter_list(self) -> list:
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
    def is_guest(self) -> bool:
        """Is WLAN a guest network."""
        return self.raw.get("is_guest", False)

    @property
    def mac_filter_enabled(self) -> bool:
        """Is MAC filtering enabled."""
        return self.raw.get("mac_filter_enabled", False)

    @property
    def mac_filter_list(self) -> list:
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
    def minrate_na_enabled(self) -> bool:
        """Is minrate NA enabled."""
        return self.raw.get("minrate_na_enabled", False)

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
    def minrate_ng_cck_rates_enabled(self) -> bool:
        """Is minrate NG CCK rates enabled."""
        return self.raw.get("minrate_ng_cck_rates_enabled", False)

    @property
    def minrate_ng_data_rate_kbps(self) -> int:
        """Minrate NG data rate kbps."""
        return self.raw["minrate_ng_data_rate_kbps"]

    @property
    def minrate_ng_enabled(self) -> bool:
        """Is minrate NG enabled."""
        return self.raw.get("minrate_ng_enabled", False)

    @property
    def minrate_ng_mgmt_rate_kbps(self) -> int:
        """Minrate NG management rate kbps."""
        return self.raw["minrate_ng_mgmt_rate_kbps"]

    @property
    def name(self) -> str:
        """WLAN name."""
        return self.raw["name"]

    @property
    def name_combine_enabled(self) -> bool:
        """If 2.5 and 5 GHz SSIDs should be combined."""
        return self.raw.get("name_combine_enabled", True)

    @property
    def name_combine_suffix(self) -> str:
        """Suffix for 2.4GHz SSID if name is not combined."""
        return self.raw.get("name_combine_suffix", "")

    @property
    def no2ghz_oui(self) -> bool:
        """No 2GHz OUI."""
        return self.raw["no2ghz_oui"]

    @property
    def schedule(self) -> list:
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


class Wlans(APIItems):
    """Represents WLAN configurations."""

    KEY = "name"

    def __init__(
        self,
        raw: List[dict],
        request: Callable[..., Awaitable[List[dict]]],
    ) -> None:
        """Initialize WLAN manager."""
        super().__init__(raw, request, URL, Wlan)

    async def async_enable(self, wlan: Wlan) -> List[dict]:
        """Block client from controller."""
        wlan_url = f"{URL}/{wlan.id}"
        data = {"enabled": True}
        return await self._request("put", wlan_url, json=data)

    async def async_disable(self, wlan: Wlan) -> List[dict]:
        """Unblock client from controller."""
        wlan_url = f"{URL}/{wlan.id}"
        data = {"enabled": False}
        return await self._request("put", wlan_url, json=data)
