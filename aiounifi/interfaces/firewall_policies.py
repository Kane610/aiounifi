"""Firewall policies as part of a UniFi network."""

from copy import deepcopy

from ..models.api import TypedApiResponse
from ..models.traffic_rule import FirewallPolicy, FirewallPolicyListRequest, FirewallPolicyUpdateRequest
from .api_handlers import APIHandler


class FirewallPolicies(APIHandler[FirewallPolicy]):
    """Represents FirewallPolicies configurations."""

    obj_id_key = "_id"
    item_cls = FirewallPolicy
    api_request = FirewallPolicyListRequest.create()
