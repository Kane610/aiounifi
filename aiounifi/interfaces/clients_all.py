"""Clients are devices on a UniFi network."""

from ..models.client import AllClientListRequest, Client
from ..models.message import MessageKey
from .api_handlers import APIHandler


class ClientsAll(APIHandler[Client]):
    """Represents all client network devices."""

    obj_id_key = "mac"
    item_cls = Client
    process_messages = (MessageKey.CLIENT_ADDED, MessageKey.CLIENT_UPDATED)
    remove_messages = (MessageKey.CLIENT_REMOVED,)
    api_request = AllClientListRequest.create()
