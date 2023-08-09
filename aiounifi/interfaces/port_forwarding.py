"""UniFi port forwarding."""

from ..models.port_forward import PortForward
from .api_handlers import APIHandler


class PortForwarding(APIHandler[PortForward]):
    """Represents port forwarding."""

    obj_id_key = "_id"
    path = "/rest/portforward"
    item_cls = PortForward
