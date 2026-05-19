"""Shared request assertion helpers for test suites."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

import orjson


def path_matches(path: str, matcher: str | re.Pattern[str]) -> bool:
    """Return True when request path matches the provided matcher."""
    if isinstance(matcher, str):
        return path.endswith(matcher)
    return bool(matcher.search(path))


def iter_matching_calls(
    mock_aioresponse: Any,
    method: str,
    path: str | re.Pattern[str],
) -> list[tuple[Any, Any]]:
    """Collect all recorded calls matching method and path matcher."""
    matches: list[tuple[Any, Any]] = []
    for request_key, call_list in mock_aioresponse.requests.items():
        request_method, request_url = request_key
        if request_method != method:
            continue
        if not path_matches(request_url.path, path):
            continue
        matches.extend((request_key, call) for call in call_list)
    return matches


def request_called_with(
    mock_aioresponse: Any,
    method: str,
    path: str | re.Pattern[str],
    **kwargs: Any,
) -> bool:
    """Legacy-compatible bool matcher for request existence and kwargs.

    This keeps the same behavior as the existing unifi_called_with fixture:
    - method must match exactly
    - path must match (suffix for str, regex for Pattern)
    - all expected kwargs must match exactly
    - any additional truthy kwargs in recorded call fail the match
      except allow_redirects
    """
    for _request_key, call in iter_matching_calls(mock_aioresponse, method, path):
        call_kwargs = call[1]
        successful_match = True

        for key, value in kwargs.items():
            if key not in call_kwargs or call_kwargs[key] != value:
                successful_match = False

        for key, value in call_kwargs.items():
            if key == "allow_redirects":
                continue
            if value and key not in kwargs:
                successful_match = False

        if successful_match:
            return True

    return False


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
    """Assert at least one matching request has the expected params and JSON subset."""
    matches = iter_matching_calls(mock_aioresponse, method, path)
    if not matches:
        raise AssertionError(
            f"No requests matched method={method!r}, path={path!r}; "
            f"recorded={list(mock_aioresponse.requests.keys())!r}"
        )

    last_error: AssertionError | None = None
    for request_key, call in matches:
        call_kwargs = call[1]
        try:
            if params is not None:
                call_params = call_kwargs.get("params")
                if not isinstance(call_params, Mapping):
                    raise AssertionError(
                        f"Expected params mapping for request {request_key!r}, got {call_params!r}"
                    )
                _assert_mapping_subset(call_params, params, context="params")

            if json_body is not None:
                direct_json = call_kwargs.get("json")
                if isinstance(direct_json, Mapping):
                    _assert_mapping_subset(direct_json, json_body, context="json body")
                else:
                    raw_data = call_kwargs.get("data")
                    if not isinstance(raw_data, (bytes, bytearray)):
                        raise AssertionError(
                            f"Expected JSON body in 'json' mapping or 'data' bytes for request {request_key!r}, "
                            f"got json={direct_json!r}, data={raw_data!r}"
                        )
                    decoded = orjson.loads(raw_data)
                    if not isinstance(decoded, dict):
                        raise AssertionError(
                            f"Expected JSON object body for request {request_key!r}, got {decoded!r}"
                        )
                    _assert_mapping_subset(decoded, json_body, context="json body")

            return
        except AssertionError as err:
            last_error = err

    raise AssertionError(
        f"No matching request had expected params/json for method={method!r}, path={path!r}. "
        f"Last mismatch: {last_error}"
    )
