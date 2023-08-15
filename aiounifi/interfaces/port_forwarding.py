"""UniFi port forwarding."""

from ..models.message import MessageKey
from ..models.port_forward import PortForward, PortForwardListRequest
from .api_handlers import APIHandler


class PortForwarding(APIHandler[PortForward]):
    """Represents port forwarding."""

    obj_id_key = "_id"
    path = "/rest/portforward"
    item_cls = PortForward
    process_messages = (MessageKey.PORT_FORWARD_ADDED, MessageKey.PORT_FORWARD_UPDATED)
    remove_messages = (MessageKey.PORT_FORWARD_DELETED,)
    api_request = PortForwardListRequest.create()
