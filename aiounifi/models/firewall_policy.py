"""Firewall policies as part of a UniFi network."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from typing import Any, NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequestV2


class FirewallPolicyScheduleMode(StrEnum):
    """When an enabled firewall policy applies."""

    ALWAYS = "ALWAYS"
    EVERY_DAY = "EVERY_DAY"
    EVERY_WEEK = "EVERY_WEEK"
    ONE_TIME_ONLY = "ONE_TIME_ONLY"
    CUSTOM = "CUSTOM"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> Self:
        """Map modes this library doesn't know to UNKNOWN."""
        return cls.UNKNOWN


class FirewallPolicySchedule(TypedDict):
    """Schedule settings for firewall policy.

    Only "mode" is always present; the other keys depend on the mode.
    """

    mode: str
    date: NotRequired[str]
    date_start: NotRequired[str]
    date_end: NotRequired[str]
    time_range_start: NotRequired[str]
    time_range_end: NotRequired[str]
    repeat_on_days: NotRequired[list[str]]
    time_all_day: NotRequired[bool]


_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


class _IncompleteScheduleError(Exception):
    """A schedule lacks a key its mode needs, or has a malformed value."""


def _schedule_value(schedule: Mapping[str, Any], key: str) -> Any:
    """Return a schedule key or raise if it is missing.

    Typed as a Mapping because mypy only allows literal keys on a TypedDict.
    """
    if (value := schedule.get(key)) is None:
        raise _IncompleteScheduleError(key)
    return value


def _parse_date(value: str) -> date:
    if not isinstance(value, str):
        raise _IncompleteScheduleError(value)
    try:
        return date.fromisoformat(value)
    except ValueError as err:
        raise _IncompleteScheduleError(value) from err


def _parse_time(value: str) -> time:
    if not isinstance(value, str):
        raise _IncompleteScheduleError(value)
    hour, _, minute = value.partition(":")
    try:
        return time(int(hour), int(minute))
    except ValueError as err:
        raise _IncompleteScheduleError(value) from err


def _window_contains(
    schedule: FirewallPolicySchedule, start_day: date, now: datetime, all_day: bool
) -> bool:
    """Whether now falls in the window that begins on start_day.

    Windows are compared on the wall clock, which is what the UDM follows.
    """
    wall_now = now.replace(tzinfo=None, second=0, microsecond=0, fold=0)
    if all_day:
        start = datetime.combine(start_day, time())
        return start <= wall_now < start + timedelta(days=1)
    start = datetime.combine(
        start_day, _parse_time(_schedule_value(schedule, "time_range_start"))
    )
    end = datetime.combine(
        start_day, _parse_time(_schedule_value(schedule, "time_range_end"))
    )
    if end <= start:
        end += timedelta(days=1)
    return start <= wall_now < end


def _window_may_start(
    schedule: FirewallPolicySchedule, mode: FirewallPolicyScheduleMode, start_day: date
) -> bool:
    """Whether a recurring schedule has a window beginning on start_day."""
    if mode in (
        FirewallPolicyScheduleMode.EVERY_WEEK,
        FirewallPolicyScheduleMode.CUSTOM,
    ):
        days = _schedule_value(schedule, "repeat_on_days")
        if not isinstance(days, list):
            raise _IncompleteScheduleError("repeat_on_days")
        if _WEEKDAYS[start_day.weekday()] not in days:
            return False
    if mode is FirewallPolicyScheduleMode.CUSTOM:
        first = _parse_date(_schedule_value(schedule, "date_start"))
        last = _parse_date(_schedule_value(schedule, "date_end"))
        return first <= start_day <= last
    return True


def is_schedule_active(schedule: FirewallPolicySchedule, now: datetime) -> bool | None:
    """Whether a firewall policy schedule applies at now.

    now must be timezone-aware and already in the UDM's timezone. Windows run
    from start (inclusive) to end (exclusive) at minute resolution; an end at
    or before the start means the following day. Returns None for an unknown
    mode or a schedule missing or mangling a key its mode needs.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    mode = FirewallPolicyScheduleMode(schedule.get("mode"))
    if mode is FirewallPolicyScheduleMode.ALWAYS:
        return True
    if mode is FirewallPolicyScheduleMode.UNKNOWN:
        return None

    # The UDM keeps keys a mode doesn't use, so all day only counts where the
    # mode has it: Every week and Custom.
    all_day = (
        mode
        in (FirewallPolicyScheduleMode.EVERY_WEEK, FirewallPolicyScheduleMode.CUSTOM)
        and schedule.get("time_all_day") is True
    )
    try:
        if mode is FirewallPolicyScheduleMode.ONE_TIME_ONLY:
            start_day = _parse_date(_schedule_value(schedule, "date"))
            return _window_contains(schedule, start_day, now, all_day)

        today = now.date()
        for start_day in (today - timedelta(days=1), today):
            if _window_may_start(schedule, mode, start_day) and _window_contains(
                schedule, start_day, now, all_day
            ):
                return True
    except _IncompleteScheduleError:
        return None
    return False


class FirewallPolicyEndpoint(TypedDict):
    """Source or destination endpoint configuration."""

    match_opposite_ports: bool
    matching_target: str
    port_matching_type: str
    zone_id: str
    client_macs: NotRequired[list[str]]


class TypedFirewallPolicy(TypedDict):
    """Firewall policy type definition."""

    _id: str
    action: str
    name: NotRequired[str]
    enabled: bool
    connection_state_type: str
    connection_states: list[str]
    create_allow_respond: bool
    description: NotRequired[str]
    destination: FirewallPolicyEndpoint
    source: FirewallPolicyEndpoint
    icmp_typename: str
    icmp_v6_typename: str
    index: int
    ip_version: str
    logging: bool
    match_ip_sec: bool
    match_opposite_protocol: bool
    predefined: bool
    protocol: str
    schedule: FirewallPolicySchedule


class FirewallPolicy(ApiItem):
    """Represent a firewall policy."""

    raw: TypedFirewallPolicy

    @property
    def id(self) -> str:
        """Unique id of firewall policy."""
        return self.raw["_id"]

    @property
    def name(self) -> str:
        """Firewall policy name."""
        return self.raw.get("name", "")

    @property
    def enabled(self) -> bool:
        """Is firewall policy enabled."""
        return self.raw["enabled"]

    @property
    def action(self) -> str:
        """Firewall policy action."""
        return self.raw["action"]

    @property
    def predefined(self) -> bool:
        """Is this a predefined policy."""
        return self.raw["predefined"]

    @property
    def description(self) -> str:
        """Policy description."""
        return self.raw.get("description", "")

    @property
    def protocol(self) -> str:
        """Policy protocol."""
        return self.raw["protocol"]

    @property
    def connection_state_type(self) -> str:
        """Connection state type."""
        return self.raw["connection_state_type"]

    @property
    def connection_states(self) -> list[str]:
        """List of connection states."""
        return self.raw["connection_states"]

    @property
    def create_allow_respond(self) -> bool:
        """Whether to create allow respond rule."""
        return self.raw["create_allow_respond"]

    @property
    def destination(self) -> FirewallPolicyEndpoint:
        """Destination endpoint configuration."""
        return self.raw["destination"]

    @property
    def source(self) -> FirewallPolicyEndpoint:
        """Source endpoint configuration."""
        return self.raw["source"]

    @property
    def icmp_typename(self) -> str:
        """ICMP type name."""
        return self.raw["icmp_typename"]

    @property
    def icmp_v6_typename(self) -> str:
        """ICMPv6 type name."""
        return self.raw["icmp_v6_typename"]

    @property
    def index(self) -> int:
        """Policy index/priority."""
        return self.raw["index"]

    @property
    def ip_version(self) -> str:
        """IP version (IPv4/IPv6/BOTH)."""
        return self.raw["ip_version"]

    @property
    def logging(self) -> bool:
        """Whether logging is enabled."""
        return self.raw["logging"]

    @property
    def match_ip_sec(self) -> bool:
        """Whether to match IPSec traffic."""
        return self.raw["match_ip_sec"]

    @property
    def match_opposite_protocol(self) -> bool:
        """Whether to match opposite protocol."""
        return self.raw["match_opposite_protocol"]

    @property
    def schedule(self) -> FirewallPolicySchedule:
        """Policy schedule configuration."""
        return self.raw["schedule"]

    @property
    def schedule_mode(self) -> FirewallPolicyScheduleMode:
        """Policy schedule mode."""
        return FirewallPolicyScheduleMode(self.raw["schedule"].get("mode"))

    def is_active(self, now: datetime) -> bool | None:
        """Whether the policy applies at now (see is_schedule_active)."""
        if not self.enabled:
            return False
        return is_schedule_active(self.schedule, now)


@dataclass
class FirewallPolicyListRequest(ApiRequestV2):
    """Request object for listing firewall policies."""

    @classmethod
    def create(cls) -> Self:
        """Create firewall policy list request."""
        return cls(method="get", path="/firewall-policies", data=None)


@dataclass
class FirewallPolicyUpdateRequest(ApiRequestV2):
    """Request object for updating a firewall policy. Note: You can't update the default policies - only ones you've created."""

    @classmethod
    def create(cls, policy: TypedFirewallPolicy) -> Self:
        """Create method for firewall policy update request."""
        return cls(
            method="put",
            path=f"/firewall-policies/{policy['_id']}",
            data=policy,
        )
