"""Hotspot vouchers as part of a UniFi network."""

from ..models.api import TypedApiResponse
from ..models.message import MessageKey
from ..models.voucher import (
    Voucher,
    VoucherCreateRequest,
    VoucherDeleteRequest,
    VoucherListRequest,
)
from .api_handlers import APIHandler


class Vouchers(APIHandler[Voucher]):
    """Represents Hotspot vouchers."""

    obj_id_key = "_id"
    item_cls = Voucher
    process_messages = (MessageKey.VOUCHER_CREATED,)
    remove_messages = (MessageKey.VOUCHER_DELETED,)
    api_request = VoucherListRequest.create()

    async def create(self, voucher: Voucher) -> TypedApiResponse:
        """Create voucher on controller."""
        return await self.controller.request(
            VoucherCreateRequest.create(
                number=1,
                quota=voucher.quota,
                expire_number=int(voucher.duration.total_seconds() / 60),
                expire_unit=1,
                usage_quota=voucher.qos_usage_quota,
                rate_max_up=voucher.qos_rate_max_up,
                rate_max_down=voucher.qos_rate_max_down,
                note=voucher.note,
            )
        )

    async def delete(self, voucher: Voucher) -> TypedApiResponse:
        """Delete voucher from controller."""
        return await self.controller.request(
            VoucherDeleteRequest.create(
                obj_id=voucher.id,
            )
        )