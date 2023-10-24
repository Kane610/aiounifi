"""Clients are devices on a UniFi network."""

from ..models.client import AllClientListRequest, Client
from .api_handlers import APIHandler


class ClientsAll(APIHandler[Client]):
    """Represents all client network devices."""

    obj_id_key = "mac"
    item_cls = Client
    api_request = AllClientListRequest.create()
