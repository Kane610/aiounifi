"""Firewall zones as part of a UniFi network."""

from ..models.firewall_zone import FirewallZone, FirewallZoneListRequest
from .api_handlers import APIHandler


class FirewallZones(APIHandler[FirewallZone]):
    """Represents FirewallZones configurations."""

    obj_id_key = "_id"
    item_cls = FirewallZone
    api_request = FirewallZoneListRequest.create()
