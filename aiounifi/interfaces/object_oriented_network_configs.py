"""Object-oriented network configurations as part of a UniFi network."""

from copy import deepcopy

from ..models.api import TypedApiResponse
from ..models.object_oriented_network_config import (
    ObjectOrientedNetworkConfig,
    ObjectOrientedNetworkConfigListRequest,
    ObjectOrientedNetworkConfigUpdateRequest,
)
from .api_handlers import APIHandler


class ObjectOrientedNetworkConfigs(APIHandler[ObjectOrientedNetworkConfig]):
    """Represents object-oriented network configurations."""

    obj_id_key = ("_id", "id")
    item_cls = ObjectOrientedNetworkConfig
    api_request = ObjectOrientedNetworkConfigListRequest.create()

    async def enable(self, config: ObjectOrientedNetworkConfig) -> TypedApiResponse:
        """Enable object-oriented network configuration."""
        return await self.save(config, state=True)

    async def disable(self, config: ObjectOrientedNetworkConfig) -> TypedApiResponse:
        """Disable object-oriented network configuration."""
        return await self.save(config, state=False)

    async def save(
        self, config: ObjectOrientedNetworkConfig, state: bool | None = None
    ) -> TypedApiResponse:
        """Set object-oriented network configuration to the desired state."""
        config_dict = deepcopy(config.raw)
        config_response = await self.controller.request(
            ObjectOrientedNetworkConfigUpdateRequest.create(config_dict, enable=state)
        )
        self.process_raw(config_response.get("data", []))
        return config_response
