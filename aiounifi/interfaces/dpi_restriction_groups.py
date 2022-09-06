"""DPI Restrictions as part of a UniFi network."""

from typing import Final

from ..models.dpi_restriction_group import DPIRestrictionGroup
from ..models.message import MessageKey
from .api import APIItems

GROUP_URL: Final = "/rest/dpigroup"


class DPIRestrictionGroups(APIItems):
    """Represents DPI Group configurations."""

    obj_id_key = "_id"
    path = GROUP_URL
    item_cls = DPIRestrictionGroup
    process_messages = (MessageKey.DPI_GROUP_ADDED, MessageKey.DPI_GROUP_UPDATED)
    remove_messages = (MessageKey.DPI_GROUP_REMOVED,)
