"""Clients are devices on a UniFi network."""

from ..models.client import Client
from .api_handlers import APIHandler


class ClientsAll(APIHandler[Client]):
    """Represents all client network devices."""

    obj_id_key = "mac"
    path = "/rest/user"
    item_cls = Client
