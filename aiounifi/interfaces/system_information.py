"""System information of a UniFi network."""

from ..models.system_information import SystemInformation, SystemInformationRequest
from .api_handlers import create_api_handler

# Using the new factory approach for cleaner, less boilerplate code
SystemInformationHandler = create_api_handler(
    obj_id_key="anonymous_controller_id",
    item_cls=SystemInformation,
    api_request=SystemInformationRequest.create(),
)
