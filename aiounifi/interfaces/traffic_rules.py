"""Traffic rules as part of a UniFi network."""

from copy import deepcopy

from ..models.api import TypedApiResponse
from ..models.traffic_rule import (
    TrafficRule,
    TrafficRuleEnableRequest,
    TrafficRuleListRequest,
)
from .api_handlers import APIHandler


class TrafficRules(APIHandler[TrafficRule]):
    """Represents TrafficRules configurations."""

    obj_id_key = "_id"
    item_cls = TrafficRule
    api_request = TrafficRuleListRequest.create()

    async def enable(self, traffic_rule: TrafficRule) -> TypedApiResponse:
        """Enable traffic rule defined in controller."""
        return await self.toggle(traffic_rule, state=True)

    async def disable(self, traffic_rule: TrafficRule) -> TypedApiResponse:
        """Disable traffic rule defined in controller."""
        return await self.toggle(traffic_rule, state=False)

    async def toggle(self, traffic_rule: TrafficRule, state: bool) -> TypedApiResponse:
        """Set traffic rule - defined in controller - to the desired state."""
        traffic_rule_dict = deepcopy(traffic_rule.raw)
        traffic_rule_response = await self.controller.request(
            TrafficRuleEnableRequest.create(traffic_rule_dict, enable=state)
        )
        self.process_raw(traffic_rule_response.get("data", []))
        return traffic_rule_response
