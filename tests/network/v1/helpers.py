"""Assertion helpers for Network API v1 tests."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

import orjson


def _path_matches(path: str, matcher: str | re.Pattern[str]) -> bool:
    """Return True when a request path matches the provided matcher."""
    if isinstance(matcher, str):
        return path.endswith(matcher)
    return bool(matcher.search(path))


def _iter_matching_calls(
    mock_aioresponse: Any,
    method: str,
    path: str | re.Pattern[str],
) -> list[tuple[Any, Any]]:
    """Collect recorded mock calls matching method and request path."""
    matches: list[tuple[Any, Any]] = []
    for request_key, call_list in mock_aioresponse.requests.items():
        request_method, request_url = request_key
        if request_method != method:
            continue
        if not _path_matches(request_url.path, path):
            continue
        matches.extend((request_key, call) for call in call_list)
    return matches


def _assert_mapping_subset(
    actual: Mapping[str, Any],
    expected: Mapping[str, Any],
    *,
    context: str,
) -> None:
    """Assert all expected key/value pairs exist in actual mapping."""
    missing: list[str] = []
    mismatched: list[str] = []
    for key, expected_value in expected.items():
        if key not in actual:
            missing.append(key)
            continue
        if actual[key] != expected_value:
            mismatched.append(
                f"{key}: expected {expected_value!r}, got {actual[key]!r}"
            )

    if missing or mismatched:
        parts: list[str] = []
        if missing:
            parts.append(f"missing keys={missing!r}")
        if mismatched:
            parts.append("mismatched={" + ", ".join(mismatched) + "}")
        details = "; ".join(parts)
        raise AssertionError(
            f"{context} assertion failed: {details}; actual={dict(actual)!r}"
        )


def assert_request_called_with(
    mock_aioresponse: Any,
    method: str,
    path: str | re.Pattern[str],
    *,
    params: Mapping[str, Any] | None = None,
    json_body: Mapping[str, Any] | None = None,
) -> None:
    """Assert at least one recorded request matches method/path and payload expectations."""
    matches = _iter_matching_calls(mock_aioresponse, method, path)
    if not matches:
        raise AssertionError(
            f"No requests matched method={method!r}, path={path!r}; "
            f"recorded={list(mock_aioresponse.requests.keys())!r}"
        )

    request_key, call = matches[0]
    call_kwargs = call[1]

    if params is not None:
        call_params = call_kwargs.get("params")
        if not isinstance(call_params, Mapping):
            raise AssertionError(
                f"Expected params mapping for request {request_key!r}, got {call_params!r}"
            )
        _assert_mapping_subset(call_params, params, context="params")

    if json_body is not None:
        raw_data = call_kwargs.get("data")
        if not isinstance(raw_data, (bytes, bytearray)):
            raise AssertionError(
                f"Expected JSON body bytes in 'data' for request {request_key!r}, got {raw_data!r}"
            )
        decoded = orjson.loads(raw_data)
        if not isinstance(decoded, dict):
            raise AssertionError(
                f"Expected JSON object body for request {request_key!r}, got {decoded!r}"
            )
        _assert_mapping_subset(decoded, json_body, context="json body")
