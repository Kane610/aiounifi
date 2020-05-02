"""WLANs as part of a UniFi network."""

from .api import APIItem, APIItems

URL = "/rest/wlanconf"  # List WLAN configuration


class Wlans(APIItems):
    """Represents WLAN configurations."""

    KEY = "name"

    def __init__(self, raw: dict, request) -> None:
        super().__init__(raw, request, URL, Wlan)

    async def async_enable(self, wlan) -> None:
        """Block client from controller."""
        wlan_url = f"{URL}/{wlan.id}"
        data = {"enabled": True}
        await self._request("put", wlan_url, json=data)

    async def async_disable(self, wlan) -> None:
        """Unblock client from controller."""
        wlan_url = f"{URL}/{wlan.id}"
        data = {"enabled": False}
        await self._request("put", wlan_url, json=data)


class Wlan(APIItem):
    """Represents a WLAN configuration."""

    @property
    def id(self) -> str:
        return self.raw["_id"]

    @property
    def bc_filter_enabled(self) -> bool:
        return self.raw.get("bc_filter_enabled", False)

    @property
    def bc_filter_list(self) -> list:
        return self.raw["bc_filter_list"]

    @property
    def dtim_mode(self) -> str:
        return self.raw["dtim_mode"]

    @property
    def dtim_na(self) -> int:
        return self.raw["dtim_na"]

    @property
    def dtim_ng(self) -> int:
        return self.raw["dtim_ng"]

    @property
    def enabled(self) -> bool:
        return self.raw["enabled"]

    @property
    def group_rekey(self) -> int:
        return self.raw["group_rekey"]

    @property
    def is_guest(self) -> bool:
        return self.raw.get("is_guest", False)

    @property
    def mac_filter_enabled(self) -> bool:
        return self.raw.get("mac_filter_enabled", False)

    @property
    def mac_filter_list(self) -> list:
        return self.raw["mac_filter_list"]

    @property
    def mac_filter_policy(self) -> str:
        return self.raw["mac_filter_policy"]

    @property
    def minrate_na_advertising_rates(self) -> bool:
        return self.raw["minrate_na_advertising_rates"]

    @property
    def minrate_na_beacon_rate_kbps(self) -> int:
        return self.raw["minrate_na_beacon_rate_kbps"]

    @property
    def minrate_na_data_rate_kbps(self) -> int:
        return self.raw["minrate_na_data_rate_kbps"]

    @property
    def minrate_na_enabled(self) -> bool:
        return self.raw.get("minrate_na_enabled", False)

    @property
    def minrate_na_mgmt_rate_kbps(self) -> int:
        return self.raw["minrate_na_mgmt_rate_kbps"]

    @property
    def minrate_ng_advertising_rates(self) -> bool:
        return self.raw["minrate_ng_advertising_rates"]

    @property
    def minrate_ng_beacon_rate_kbps(self) -> int:
        return self.raw["minrate_ng_beacon_rate_kbps"]

    @property
    def minrate_ng_cck_rates_enabled(self) -> bool:
        return self.raw.get("minrate_ng_cck_rates_enabled", False)

    @property
    def minrate_ng_data_rate_kbps(self) -> int:
        return self.raw["minrate_ng_data_rate_kbps"]

    @property
    def minrate_ng_enabled(self) -> bool:
        return self.raw.get("minrate_ng_enabled", False)

    @property
    def minrate_ng_mgmt_rate_kbps(self) -> int:
        return self.raw["minrate_ng_mgmt_rate_kbps"]

    @property
    def name(self) -> str:
        return self.raw["name"]

    @property
    def name_combine_enabled(self) -> bool:
        """Describes if 2.5 and 5 GHz SSIDs should be combined."""
        return self.raw.get("name_combine_enabled", True)

    @property
    def name_combine_suffix(self) -> str:
        """Suffix for 2.4GHz SSID if name is not combined."""
        return self.raw.get("name_combine_suffix", "")

    @property
    def no2ghz_oui(self) -> bool:
        return self.raw["no2ghz_oui"]

    @property
    def schedule(self) -> list:
        return self.raw["schedule"]

    @property
    def security(self) -> str:
        return self.raw["security"]

    @property
    def site_id(self) -> str:
        return self.raw["site_id"]

    @property
    def usergroup_id(self) -> str:
        return self.raw["usergroup_id"]

    @property
    def wep_idx(self) -> int:
        return self.raw["wep_idx"]

    @property
    def wlangroup_id(self) -> str:
        return self.raw["wlangroup_id"]

    @property
    def wpa_enc(self) -> str:
        return self.raw["wpa_enc"]

    @property
    def wpa_mode(self) -> str:
        return self.raw["wpa_mode"]

    @property
    def x_iapp_key(self) -> str:
        return self.raw["x_iapp_key"]

    @property
    def x_passphrase(self) -> str:
        return self.raw["x_passphrase"]
