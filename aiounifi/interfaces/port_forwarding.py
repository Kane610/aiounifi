"""UniFi port forwarding."""

from ..models.message import MessageKey
from ..models.port_forward import PortForward, PortForwardListRequest
from .api_handlers import create_api_handler

# Create PortForwarding using factory pattern
PortForwarding = create_api_handler(
    obj_id_key="_id",
    item_cls=PortForward,
    api_request=PortForwardListRequest.create(),
    process_messages=(MessageKey.PORT_FORWARD_ADDED, MessageKey.PORT_FORWARD_UPDATED),
    remove_messages=(MessageKey.PORT_FORWARD_DELETED,),
)
