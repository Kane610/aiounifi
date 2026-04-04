"""Device port implementation."""

from __future__ import annotations

from enum import StrEnum
import logging
from typing import cast

from .api import ApiItem
from .device import TypedDevicePortTable

LOGGER = logging.getLogger(__name__)


class PortMedia(StrEnum):
    """Enum for network port media types."""

    GIGABIT = "GE"
    FAST = "FE"
    SFP = "SFP"
    SFP_PLUS = "SFP+"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> PortMedia:
        """Set default enum member if an unknown media type is provided."""
        LOGGER.warning("Unsupported port media %s, using UNKNOWN", value)
        return cls.UNKNOWN


class PortPoEMode(StrEnum):
    """Enum for Power over Ethernet modes."""

    AUTO = "auto"
    OFF = "off"
    PASSTHROUGH = "passthrough"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> PortPoEMode:
        """Set default enum member if an unknown PoE mode is provided."""
        LOGGER.warning("Unsupported port PoE mode %s, using UNKNOWN", value)
        return cls.UNKNOWN


class Port(ApiItem):
    """Represents a network port."""

    raw: TypedDevicePortTable

    @property
    def ifname(self) -> str | None:
        """Port name used by USG."""
        return self.raw.get("ifname")

    @property
    def media(self) -> PortMedia:
        """Media port is connected to."""
        return PortMedia(self.raw.get("media", "unknown"))

    @property
    def name(self) -> str:
        """Port name."""
        if (name := self.raw["name"]) == "":
            # Unifi controller allows to set an empty port name, but it
            # shows up as "Port N" consistently across UI. We mirror the
            # behavior, as empty name is rarely visually helpful.
            return f"Port {self.port_idx}"
        return name

    @property
    def port_idx(self) -> int | None:
        """Port index."""
        return self.raw.get("port_idx")

    @property
    def poe_caps(self) -> int | None:
        """Port PoE capabilities.

        0 - no caps
        3 - auto (PoE/PoE+)
        35 - auto (Poe/PoE+/PoE++)
        7 - 24V passive
        8 - Passthrough
        """
        return self.raw.get("poe_caps")

    @property
    def poe_class(self) -> str | None:
        """Port PoE class."""
        return self.raw.get("poe_class")

    @property
    def poe_enable(self) -> bool | None:
        """Is PoE supported/requested by client."""
        return self.raw.get("poe_enable")

    @property
    def poe_mode(self) -> PortPoEMode:
        """PoE mode (auto, passthrough, off, or unknown)."""
        return PortPoEMode(self.raw.get("poe_mode", "unknown"))

    @property
    def poe_power(self) -> str | None:
        """Is PoE power usage."""
        return self.raw.get("poe_power")

    @property
    def poe_voltage(self) -> str | None:
        """Is PoE voltage usage."""
        return self.raw.get("poe_voltage")

    @property
    def portconf_id(self) -> str | None:
        """Port configuration ID."""
        return self.raw.get("portconf_id")

    @property
    def port_poe(self) -> bool | None:
        """Is PoE used."""
        return self.raw.get("port_poe")

    @property
    def rx_bytes(self) -> int:
        """Bytes received."""
        return self.raw.get("rx_bytes", 0)

    @property
    def rx_bytes_r(self) -> int:
        """Bytes recently received."""
        return cast(int, self.raw.get("rx_bytes-r", 0))

    @property
    def tx_bytes(self) -> int:
        """Bytes transferred."""
        return self.raw.get("tx_bytes", 0)

    @property
    def tx_bytes_r(self) -> int:
        """Bytes recently transferred."""
        return cast(int, self.raw.get("tx_bytes-r", 0))

    @property
    def up(self) -> bool | None:
        """Is port up."""
        return self.raw.get("up")

    @property
    def enabled(self) -> bool | None:
        """Is port enabled."""
        return self.raw.get("enable")

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<{self.name}: Poe {self.poe_enable}>"
