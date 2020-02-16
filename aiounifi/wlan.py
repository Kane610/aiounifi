"""WLANs as part of a UniFi network."""

from .api import APIItem, APIItems

URL = "s/{site}/rest/wlanconf"  # List WLAN configuration


class Wlans(APIItems):
    """Represents WLAN configurations."""

    KEY = "name"

    def __init__(self, raw, request):
        super().__init__(raw, request, URL, Wlan)

    async def async_enable(self, wlan):
        """Block client from controller."""
        wlan_url = f"{URL}/{wlan.id}"
        # data = dict(wlan.raw)
        data = dict()
        data["enabled"] = True
        await self._request("put", wlan_url, json=data)

    async def async_disable(self, wlan):
        """Unblock client from controller."""
        wlan_url = f"{URL}/{wlan.id}"
        print(wlan_url)
        # data = dict(wlan.raw)
        data = dict()
        data["enabled"] = False
        await self._request("put", wlan_url, json=data)


class Wlan(APIItem):
    """Represents a WLAN configuration."""

    @property
    def id(self):
        return self.raw["_id"]

    @property
    def bc_filter_enabled(self):
        return self.raw.get("bc_filter_enabled", False)

    @property
    def bc_filter_list(self):
        return self.raw["bc_filter_list"]

    @property
    def dtim_mode(self):
        return self.raw["dtim_mode"]

    @property
    def dtim_na(self):
        return self.raw["dtim_na"]

    @property
    def dtim_ng(self):
        return self.raw["dtim_ng"]

    @property
    def enabled(self):
        return self.raw["enabled"]

    @property
    def group_rekey(self):
        return self.raw["group_rekey"]

    @property
    def is_guest(self):
        return self.raw.get("is_guest", False)

    @property
    def mac_filter_enabled(self):
        return self.raw.get("mac_filter_enabled", False)

    @property
    def mac_filter_list(self):
        return self.raw["mac_filter_list"]

    @property
    def mac_filter_policy(self):
        return self.raw["mac_filter_policy"]

    @property
    def minrate_na_advertising_rates(self):
        return self.raw["minrate_na_advertising_rates"]

    @property
    def minrate_na_beacon_rate_kbps(self):
        return self.raw["minrate_na_beacon_rate_kbps"]

    @property
    def minrate_na_data_rate_kbps(self):
        return self.raw["minrate_na_data_rate_kbps"]

    @property
    def minrate_na_enabled(self):
        return self.raw.get("minrate_na_enabled", False)

    @property
    def minrate_na_mgmt_rate_kbps(self):
        return self.raw["minrate_na_mgmt_rate_kbps"]

    @property
    def minrate_ng_advertising_rates(self):
        return self.raw["minrate_ng_advertising_rates"]

    @property
    def minrate_ng_beacon_rate_kbps(self):
        return self.raw["minrate_ng_beacon_rate_kbps"]

    @property
    def minrate_ng_cck_rates_enabled(self):
        return self.raw.get("minrate_ng_cck_rates_enabled", False)

    @property
    def minrate_ng_data_rate_kbps(self):
        return self.raw["minrate_ng_data_rate_kbps"]

    @property
    def minrate_ng_enabled(self):
        return self.raw.get("minrate_ng_enabled", False)

    @property
    def minrate_ng_mgmt_rate_kbps(self):
        return self.raw["minrate_ng_mgmt_rate_kbps"]

    @property
    def name(self):
        return self.raw["name"]

    @property
    def no2ghz_oui(self):
        return self.raw["no2ghz_oui"]

    @property
    def schedule(self):
        return self.raw["schedule"]

    @property
    def security(self):
        return self.raw["security"]

    @property
    def site_id(self):
        return self.raw["site_id"]

    @property
    def usergroup_id(self):
        return self.raw["usergroup_id"]

    @property
    def wep_idx(self):
        return self.raw["wep_idx"]

    @property
    def wlangroup_id(self):
        return self.raw["wlangroup_id"]

    @property
    def wpa_enc(self):
        return self.raw["wpa_enc"]

    @property
    def wpa_mode(self):
        return self.raw["wpa_mode"]

    @property
    def x_iapp_key(self):
        return self.raw["x_iapp_key"]

    @property
    def x_passphrase(self):
        return self.raw["x_passphrase"]
