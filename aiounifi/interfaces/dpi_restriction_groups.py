"""DPI Restrictions as part of a UniFi network."""

from ..models.dpi_restriction_group import (
    DPIRestrictionGroup,
    DpiRestrictionGroupListRequest,
)
from ..models.message import MessageKey
from .api_handlers import create_api_handler

# Create DPIRestrictionGroups using factory pattern
DPIRestrictionGroups = create_api_handler(
    obj_id_key="_id",
    item_cls=DPIRestrictionGroup,
    api_request=DpiRestrictionGroupListRequest.create(),
    process_messages=(MessageKey.DPI_GROUP_ADDED, MessageKey.DPI_GROUP_UPDATED),
    remove_messages=(MessageKey.DPI_GROUP_REMOVED,),
)
