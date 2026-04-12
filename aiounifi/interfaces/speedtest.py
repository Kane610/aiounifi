"""Speedtest interface."""

from __future__ import annotations

import logging

from aiounifi.models.speedtest import (
    SpeedtestStatus,
    SpeedtestStatusRequest,
    SpeedtestTriggerRequest,
)

from .api_handlers import APIHandler

LOGGER = logging.getLogger(__name__)


class SpeedtestHandler(APIHandler[SpeedtestStatus]):
    """Represents the speedtest interface."""

    obj_id_key = "id"
    item_cls = SpeedtestStatus
    api_request = SpeedtestStatusRequest.create()

    async def trigger(self) -> None:
        """Trigger a speedtest."""
        await self.controller.request(SpeedtestTriggerRequest.create())
