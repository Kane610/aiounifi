"""Firewall policies as part of a UniFi network."""

from ..models.firewall_policy import FirewallPolicy, FirewallPolicyListRequest
from .api_handlers import APIHandler


class FirewallPolicies(APIHandler[FirewallPolicy]):
    """Represents FirewallPolicies configurations."""

    obj_id_key = "_id"
    item_cls = FirewallPolicy
    api_request = FirewallPolicyListRequest.create()
