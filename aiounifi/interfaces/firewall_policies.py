"""Firewall policies as part of a UniFi network."""

from ..models.firewall_policy import FirewallPolicy, FirewallPolicyListRequest
from .api_handlers import create_api_handler

# Create FirewallPolicies using factory pattern
FirewallPolicies = create_api_handler(
    obj_id_key="_id",
    item_cls=FirewallPolicy,
    api_request=FirewallPolicyListRequest.create(),
)
