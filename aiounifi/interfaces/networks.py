"""Networks as part of a UniFi network."""

from ..models.api import TypedApiResponse
from ..models.message import MessageKey
from ..models.network import (
    Network,
    NetworkListRequest,
    NetworkUpdateRequest,
    WanLoadBalanceType,
)
from .api_handlers import APIHandler


class Networks(APIHandler[Network]):
    """Represents network configurations."""

    obj_id_key = "_id"
    item_cls = Network
    process_messages = (MessageKey.NETWORK_CONF_UPDATED,)
    api_request = NetworkListRequest.create()

    async def save(
        self,
        network: Network,
        *,
        enabled: bool | None = None,
        wan_failover_priority: int | None = None,
        wan_load_balance_type: WanLoadBalanceType | None = None,
        wan_load_balance_weight: int | None = None,
    ) -> TypedApiResponse:
        """Set network - defined in controller - to the desired state."""
        response = await self.controller.request(
            NetworkUpdateRequest.create(
                network,
                enabled=enabled,
                wan_failover_priority=wan_failover_priority,
                wan_load_balance_type=wan_load_balance_type,
                wan_load_balance_weight=wan_load_balance_weight,
            )
        )
        self.process_raw(response.get("data", []))
        return response
