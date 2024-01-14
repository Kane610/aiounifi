"""Device outlet implementation."""


from .api import ApiItem
from .device import TypedDeviceOutletTable


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
        """Is the outlet controllable.

        Not reported by USP-PDU-Pro, see caps.
        """
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
        Not reported by by USP-PDU-Pro, see caps.
        """
        return self.raw.get("has_metering")

    @property
    def caps(self) -> int | None:
        """Outlet capabilities.

        1: Outlet supports relay (switching)
        3: Outlet supports relay and metering
        """
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
