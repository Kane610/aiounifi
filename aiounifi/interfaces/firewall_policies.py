"""Firewall policies as part of a UniFi network."""

from copy import deepcopy
from typing import Any, cast

from ..models.api import TypedApiResponse
from ..models.firewall_policy import (
    FirewallPolicy,
    FirewallPolicyListRequest,
    FirewallPolicySchedule,
    FirewallPolicyUpdateRequest,
)
from .api_handlers import APIHandler


class FirewallPolicies(APIHandler[FirewallPolicy]):
    """Represents FirewallPolicies configurations."""

    obj_id_key = "_id"
    item_cls = FirewallPolicy
    api_request = FirewallPolicyListRequest.create()

    async def save(
        self,
        policy: FirewallPolicy,
        *,
        enabled: bool | None = None,
        schedule: FirewallPolicySchedule | None = None,
    ) -> TypedApiResponse:
        """Save changes to a firewall policy.

        The schedule, if given, replaces the current one wholesale. A rejected
        change raises and leaves the cached policy as it was. An accepted one
        updates the cache from the controller's response, or, when the
        controller sends no policy back, with what was sent, so the next
        change builds on it.
        """
        raw = deepcopy(policy.raw)
        if enabled is not None:
            raw["enabled"] = enabled
        if schedule is not None:
            raw["schedule"] = schedule
        response = await self.controller.request(
            FirewallPolicyUpdateRequest.create(raw)
        )
        self.process_raw(response.get("data") or [cast(dict[str, Any], raw)])
        return response
