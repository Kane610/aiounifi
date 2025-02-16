"""Firewall zones as part of a UniFi network."""

from copy import deepcopy

from ..models.api import TypedApiResponse
from ..models.traffic_rule import FirewallZone, FirewallZoneListRequest, FirewallZoneUpdateRequest
from .api_handlers import APIHandler


class FirewallZones(APIHandler[FirewallZone]):
    """Represents FirewallZones configurations."""

    obj_id_key = "_id"
    item_cls = FirewallZone
    api_request = FirewallZoneListRequest.create()
