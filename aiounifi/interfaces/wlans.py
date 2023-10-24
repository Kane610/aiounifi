"""WLANs as part of a UniFi network."""

from ..models.api import TypedApiResponse
from ..models.message import MessageKey
from ..models.wlan import Wlan, WlanEnableRequest, WlanListRequest, wlan_qr_code
from .api_handlers import APIHandler


class Wlans(APIHandler[Wlan]):
    """Represents WLAN configurations."""

    obj_id_key = "_id"
    item_cls = Wlan
    process_messages = (MessageKey.WLAN_CONF_UPDATED,)
    api_request = WlanListRequest.create()

    async def enable(self, wlan: Wlan) -> TypedApiResponse:
        """Block client from controller."""
        return await self.controller.request(
            WlanEnableRequest.create(wlan.id, enable=True)
        )

    async def disable(self, wlan: Wlan) -> TypedApiResponse:
        """Unblock client from controller."""
        return await self.controller.request(
            WlanEnableRequest.create(wlan.id, enable=False)
        )

    def generate_wlan_qr_code(self, wlan: Wlan) -> bytes:
        """Generate QR code based on WLAN properties."""
        return wlan_qr_code(wlan.name, wlan.x_passphrase)
