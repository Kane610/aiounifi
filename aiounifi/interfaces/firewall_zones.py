"""Firewall zones as part of a UniFi network."""

from ..models.firewall_zone import FirewallZone, FirewallZoneListRequest
from .api_handlers import create_api_handler

# Create FirewallZones using factory pattern
FirewallZones = create_api_handler(
    obj_id_key="_id",
    item_cls=FirewallZone,
    api_request=FirewallZoneListRequest.create(),
)
