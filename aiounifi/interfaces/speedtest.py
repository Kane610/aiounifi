"""Speedtest interface."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models.speedtest import (
    SpeedtestStatus,
    SpeedtestStatusLegacyRequest,
    SpeedtestStatusRequest,
    SpeedtestTriggerLegacyRequest,
    SpeedtestTriggerRequest,
)

if TYPE_CHECKING:
    from ..controller import Controller

LOGGER = logging.getLogger(__name__)


class SpeedtestHandler:
    """Represents the speedtest interface."""

    def __init__(self, controller: Controller) -> None:
        """Initialize speedtest handler."""
        self.controller = controller

    async def fetch(self) -> SpeedtestStatus | None:
        """Fetch the latest speedtest status."""
        if self.controller.connectivity.is_unifi_os:
            # Hardware controllers use the V2 endpoint
            # It returns a list of tests in 'data'
            res = await self.controller.request(SpeedtestStatusRequest.create())
            raw_data = res.get("data", [])
            if raw_data:
                # Return the most recent test (sort by time instead of assuming last is newest)
                latest = sorted(raw_data, key=lambda x: x.get("time", 0))[-1]
                return SpeedtestStatus(latest)
            return None

        # Software controllers use the legacy health endpoint
        res = await self.controller.request(SpeedtestStatusLegacyRequest.create())
        raw_data = res.get("data", [])
        for subsystem in raw_data:
            if subsystem.get("subsystem") == "www":
                return SpeedtestStatus(subsystem)
        return None

    async def trigger(self) -> None:
        """Trigger a speedtest."""
        if self.controller.connectivity.is_unifi_os:
            await self.controller.request(SpeedtestTriggerRequest.create())
        else:
            await self.controller.request(SpeedtestTriggerLegacyRequest.create())
