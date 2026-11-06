"""Firewall policies as part of a UniFi network."""

from collections.abc import Collection, Mapping
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

    @property
    def has_time_window(self) -> bool:
        """Whether the mode applies in a time window, unless it runs all day."""
        return self not in (
            FirewallPolicyScheduleMode.ALWAYS,
            FirewallPolicyScheduleMode.UNKNOWN,
        )

    @property
    def has_days(self) -> bool:
        """Whether the mode applies on chosen days of the week."""
        return self in (
            FirewallPolicyScheduleMode.EVERY_WEEK,
            FirewallPolicyScheduleMode.CUSTOM,
        )

    @property
    def has_start_date(self) -> bool:
        """Whether the mode starts on a date."""
        return self in (
            FirewallPolicyScheduleMode.ONE_TIME_ONLY,
            FirewallPolicyScheduleMode.CUSTOM,
        )

    @property
    def has_end_date(self) -> bool:
        """Whether the mode ends on a date."""
        return self is FirewallPolicyScheduleMode.CUSTOM


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


SCHEDULE_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
"""The days of the week as a schedule names them, Monday first."""

# The UniFi Network UI fills these in when a mode needs a time window.
DEFAULT_SCHEDULE_START_TIME = time(9, 0)
DEFAULT_SCHEDULE_END_TIME = time(12, 0)


class _IncompleteScheduleError(Exception):
    """A schedule lacks a key its mode needs, or has a malformed value."""


def _schedule_value(schedule: Mapping[str, Any], key: str) -> Any:
    """Return a schedule key or raise if it is missing.

    Typed as a Mapping because mypy only allows literal keys on a TypedDict.
    """
    if (value := schedule.get(key)) is None:
        raise _IncompleteScheduleError(key)
    return value


def _parse_date(value: object) -> date:
    if not isinstance(value, str):
        raise _IncompleteScheduleError(value)
    try:
        return date.fromisoformat(value)
    except ValueError as err:
        raise _IncompleteScheduleError(value) from err


def _parse_time(value: object) -> time:
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
    if mode.has_days:
        days = _schedule_value(schedule, "repeat_on_days")
        if not isinstance(days, list):
            raise _IncompleteScheduleError("repeat_on_days")
        if SCHEDULE_WEEKDAYS[start_day.weekday()] not in days:
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
    all_day = mode.has_days and schedule.get("time_all_day") is True
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


class FirewallPolicyScheduleError(ValueError):
    """A schedule change the policy's mode can't hold or the UDM would reject.

    Raised before any request is made.
    """


class ScheduleSettingUnusedError(FirewallPolicyScheduleError):
    """The schedule's mode doesn't use a setting being changed."""


class ScheduleDatesOutOfOrderError(FirewallPolicyScheduleError):
    """A Custom schedule wouldn't end after the day it starts."""


class ScheduleWithoutDaysError(FirewallPolicyScheduleError):
    """A schedule would have no days of the week left."""


def _optional_date(value: object) -> date | None:
    try:
        return _parse_date(value)
    except _IncompleteScheduleError:
        return None


def _optional_time(value: object) -> time | None:
    try:
        return _parse_time(value)
    except _IncompleteScheduleError:
        return None


@dataclass(frozen=True, kw_only=True)
class FirewallPolicyScheduleSettings:
    """The settings a schedule's mode uses, parsed.

    The UDM keeps keys a mode doesn't use, so those are ignored: a setting is
    None when the mode doesn't use it, or when it is missing or malformed.
    """

    mode: FirewallPolicyScheduleMode
    start_time: time | None = None
    end_time: time | None = None
    start_date: date | None = None
    """The day a One time schedule applies on, or a Custom schedule's first."""
    end_date: date | None = None
    all_day: bool | None = None
    days: tuple[str, ...] | None = None
    """Days of the week, Monday first; days this library doesn't know are left out."""

    @classmethod
    def from_schedule(cls, schedule: Mapping[str, Any]) -> Self:
        """Parse a schedule as the UDM stores it.

        Typed as a Mapping because mypy only allows literal keys on a TypedDict.
        """
        mode = FirewallPolicyScheduleMode(schedule.get("mode", ""))
        all_day: bool | None = None
        days: tuple[str, ...] | None = None
        if mode.has_days:
            all_day = schedule.get("time_all_day") is True
            stored = schedule.get("repeat_on_days")
            stored_days = stored if isinstance(stored, list) else []
            days = tuple(day for day in SCHEDULE_WEEKDAYS if day in stored_days)
        has_time_window = mode.has_time_window and not all_day
        date_key = (
            "date" if mode is FirewallPolicyScheduleMode.ONE_TIME_ONLY else "date_start"
        )
        return cls(
            mode=mode,
            start_time=(
                _optional_time(schedule.get("time_range_start"))
                if has_time_window
                else None
            ),
            end_time=(
                _optional_time(schedule.get("time_range_end"))
                if has_time_window
                else None
            ),
            start_date=(
                _optional_date(schedule.get(date_key)) if mode.has_start_date else None
            ),
            end_date=(
                _optional_date(schedule.get("date_end")) if mode.has_end_date else None
            ),
            all_day=all_day,
            days=days,
        )

    @property
    def has_time_window(self) -> bool:
        """Whether the schedule applies in a time window."""
        return self.mode.has_time_window and not self.all_day


def build_schedule(
    current: Mapping[str, Any],
    today: date,
    *,
    mode: FirewallPolicyScheduleMode | None = None,
    start_time: time | None = None,
    end_time: time | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    all_day: bool | None = None,
    days: Collection[str] | None = None,
) -> FirewallPolicySchedule:
    """Build the schedule to save from the current one plus changes.

    The UDM keeps keys a mode doesn't use, so the schedule is built from
    scratch with exactly the keys its mode needs. A setting that isn't changed
    is taken from the current schedule if it uses it; otherwise, like in the
    UniFi Network UI:

    - A time window is 09:00 to 12:00.
    - Choosing One time dates it today, even when it is already One time.
    - A Custom schedule chosen from another mode runs from today to tomorrow.
    - Every week or Custom chosen from a mode without days applies on every
      day, in a time window. Changing between them keeps the days and all day.

    today is the UDM's date, since the schedule runs on its clock. Raises
    ScheduleSettingUnusedError if the new schedule doesn't use a changed
    setting, ScheduleWithoutDaysError if days is empty, and
    ScheduleDatesOutOfOrderError unless a Custom schedule ends after the day
    it starts.
    """
    old = FirewallPolicyScheduleSettings.from_schedule(current)
    new_mode = mode or old.mode
    schedule: FirewallPolicySchedule = {"mode": new_mode.value}
    if new_mode.has_days:
        schedule["repeat_on_days"] = _selected_days(old, days)
        schedule["time_all_day"] = all_day = (
            old.all_day is True if all_day is None else all_day
        )
    elif days is not None or all_day is not None:
        raise ScheduleSettingUnusedError
    has_time_window = new_mode.has_time_window and not all_day
    if (
        (start_date is not None and not new_mode.has_start_date)
        or (end_date is not None and not new_mode.has_end_date)
        or ((start_time, end_time) != (None, None) and not has_time_window)
    ):
        raise ScheduleSettingUnusedError

    if new_mode is FirewallPolicyScheduleMode.ONE_TIME_ONLY:
        # Choosing One time, even again, dates it today.
        kept = old.start_date if mode is None else None
        schedule["date"] = (start_date or kept or today).isoformat()
    elif new_mode is FirewallPolicyScheduleMode.CUSTOM:
        same_mode = old.mode is FirewallPolicyScheduleMode.CUSTOM
        first_day = start_date or (old.start_date if same_mode else None) or today
        last_day = (
            end_date
            or (old.end_date if same_mode else None)
            or today + timedelta(days=1)
        )
        # The UDM rejects a range that starts and ends on the same day.
        if first_day >= last_day:
            raise ScheduleDatesOutOfOrderError
        schedule["date_start"] = first_day.isoformat()
        schedule["date_end"] = last_day.isoformat()
    if has_time_window:
        start_time = start_time or old.start_time or DEFAULT_SCHEDULE_START_TIME
        end_time = end_time or old.end_time or DEFAULT_SCHEDULE_END_TIME
        schedule["time_range_start"] = start_time.strftime("%H:%M")
        schedule["time_range_end"] = end_time.strftime("%H:%M")
    return schedule


def _selected_days(
    old: FirewallPolicyScheduleSettings, days: Collection[str] | None
) -> list[str]:
    """Return the days for a schedule with days, Monday first."""
    if days is None:
        # Days are kept from a mode that has them, or every day is chosen.
        return list(SCHEDULE_WEEKDAYS if old.days is None else old.days)
    if not (selected := [day for day in SCHEDULE_WEEKDAYS if day in days]):
        raise ScheduleWithoutDaysError
    return selected


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

    @property
    def schedule_settings(self) -> FirewallPolicyScheduleSettings:
        """The settings the policy's schedule mode uses."""
        # A policy without a schedule reads as an UNKNOWN mode.
        return FirewallPolicyScheduleSettings.from_schedule(
            self.raw.get("schedule", {})
        )

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
