"""Helpers for Network Integration API v1 tests."""

from __future__ import annotations

from typing import Any

from aioresponses import aioresponses


def request_kwargs(
    mock_aioresponse: aioresponses, method: str, path_suffix: str
) -> dict[str, Any]:
    """Return kwargs for the first matching mocked request."""
    for req, call_list in mock_aioresponse.requests.items():
        if req[0].lower() != method.lower():
            continue
        if str(req[1].path).endswith(path_suffix):
            return dict(call_list[0][1])
    raise AssertionError(f"No {method} request ending with {path_suffix} was made")
