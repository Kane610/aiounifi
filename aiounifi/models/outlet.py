"""Device outlet implementation."""

from dataclasses import dataclass

from .api import ApiItem
from .device import TypedDeviceOutletTable


@dataclass
class Outlet2:
    """Power outlet representation."""

    name: str
    index: int
    has_relay: bool | None
    relay_state: bool
    cycle_enabled: bool | None

    # Metering capabilities of outlet
    has_metering: bool | None
    caps: int | None
    voltage: str | None
    current: str | None
    power: str | None
    power_factor: str | None

    @classmethod
    def from_dict(cls, data: TypedDeviceOutletTable) -> "Outlet2":
        """Create data container instance from dict."""
        return cls(
            name=data["name"],
            index=data["index"],
            relay_state=data["relay_state"],
            has_relay=data.get("has_relay"),
            cycle_enabled=data.get("cycle_enabled"),
            has_metering=data.get("has_metering"),
            caps=data.get("outlet_caps"),
            voltage=data.get("outlet_voltage"),
            current=data.get("outlet_current"),
            power=data.get("outlet_power"),
            power_factor=data.get("outlet_power_factor"),
        )


class Outlet(ApiItem):
    """Represents an outlet."""

    raw: TypedDeviceOutletTable

    @property
    def name(self) -> str:
        """Name of outlet."""
        return self.raw["name"]

    @property
    def index(self) -> int:
        """Outlet index."""
        return self.raw["index"]

    @property
    def has_relay(self) -> bool | None:
        """Is the outlet controllable."""
        return self.raw.get("has_relay")

    @property
    def relay_state(self) -> bool:
        """Is outlet power on."""
        return self.raw["relay_state"]

    @property
    def cycle_enabled(self) -> bool | None:
        """Modem Power Cycle."""
        return self.raw.get("cycle_enabled")

    # Metering capabilities of outlet

    @property
    def has_metering(self) -> bool | None:
        """Is metering supported.

        Reported false by UP1 and UP6 which does not have power metering.
        Not reported by UPD Pro which does report power metering.
        """
        return self.raw.get("has_metering")

    @property
    def caps(self) -> int | None:
        """Unknown."""
        return self.raw.get("outlet_caps")

    @property
    def voltage(self) -> str | None:
        """Voltage draw of outlet."""
        return self.raw.get("outlet_voltage")

    @property
    def current(self) -> str | None:
        """Usage of outlet."""
        return self.raw.get("outlet_current")

    @property
    def power(self) -> str | None:
        """Power consumption of the outlet."""
        return self.raw.get("outlet_power")

    @property
    def power_factor(self) -> str | None:
        """Power factor."""
        return self.raw.get("outlet_power_factor")

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<{self.name}: relay state {self.relay_state}>"
