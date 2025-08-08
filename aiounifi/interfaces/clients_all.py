"""Clients are devices on a UniFi network."""

from ..models.client import AllClientListRequest, Client
from .api_handlers import create_api_handler

# Create ClientsAll using factory pattern
ClientsAll = create_api_handler(
    obj_id_key="mac",
    item_cls=Client,
    api_request=AllClientListRequest.create(),
)
