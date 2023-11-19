"""Traffic routes as part of a UniFi network."""

from copy import deepcopy

from ..models.api import TypedApiResponse
from ..models.traffic_route import (
    TrafficRoute,
    TrafficRouteListRequest,
    TrafficRouteSaveRequest,
)
from .api_handlers import APIHandler


class TrafficRoutes(APIHandler[TrafficRoute]):
    """Represents TrafficRoutes configurations."""

    obj_id_key = "_id"
    item_cls = TrafficRoute
    api_request = TrafficRouteListRequest.create()

    async def enable(self, traffic_route: TrafficRoute) -> TypedApiResponse:
        """Enable traffic route defined in controller."""
        return await self.save(traffic_route, state=True)

    async def disable(self, traffic_route: TrafficRoute) -> TypedApiResponse:
        """Disable traffic route defined in controller."""
        return await self.save(traffic_route, state=False)

    async def save(
        self, traffic_route: TrafficRoute, state: bool | None = None
    ) -> TypedApiResponse:
        """Set traffic route - defined in controller - to the desired state."""
        traffic_route_dict = deepcopy(traffic_route.raw)
        traffic_route_response = await self.controller.request(
            TrafficRouteSaveRequest.create(traffic_route_dict, enable=state)
        )
        self.process_raw(traffic_route_response.get("data", []))
        return traffic_route_response
