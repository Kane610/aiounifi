"""WLANs as part of a UniFi network."""

from typing import Any

from ..models.traffic_rule import TrafficRule, TrafficRuleListRequest, TrafficRuleEnableRequest
from .api_handlers import APIHandler


class TrafficRules(APIHandler[TrafficRule]):
    """Represents TrafficRules configurations."""

    obj_id_key = "_id"
    path = "/trafficrules"
    item_cls = TrafficRule
    api_request = TrafficRuleListRequest.create()

    async def enable(self, traffic_rule: TrafficRule) -> list[dict[str, Any]]:
        """Enable traffic rule defined in controller."""
        tr = self.controller.traffic_rules.get(traffic_rule.id)
        traffic_rule_dict = tr.raw
        return await self.controller.request(
            TrafficRuleEnableRequest.create(traffic_rule_dict, enable=True)
        )

    async def disable(self, traffic_rule: TrafficRule) -> list[dict[str, Any]]:
        """Disable traffic rule defined in controller."""
        tr = self.controller.traffic_rules.get(traffic_rule.id)
        traffic_rule_dict = tr.raw
        return await self.controller.request(
            TrafficRuleEnableRequest.create(traffic_rule_dict, enable=False)
        )
