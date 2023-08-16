"""System information of a UniFi network."""

from ..models.system_information import SystemInformation, SystemInformationRequest
from .api_handlers import APIHandler


class SystemInformationHandler(APIHandler[SystemInformation]):
    """Represents system information interface."""

    obj_id_key = "anonymous_controller_id"
    item_cls = SystemInformation
    api_request = SystemInformationRequest.create()
