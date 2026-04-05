"""Connectivity for official UniFi API calls."""

from __future__ import annotations

from http import HTTPStatus
import logging
from typing import TYPE_CHECKING

from aiohttp import client_exceptions

from ..errors import (
    BadGateway,
    Forbidden,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    Unauthorized,
)

if TYPE_CHECKING:
    from ..models.configuration import Configuration
    from .models.api import OfficialApiRequest, OfficialApiResponse

LOGGER = logging.getLogger(__name__)


class OfficialConnectivity:
    """Manage HTTP requests against the official UniFi API."""

    def __init__(self, config: Configuration) -> None:
        """Initialize official API connectivity."""
        self.config = config

    async def request(self, api_request: OfficialApiRequest) -> OfficialApiResponse:
        """Perform one request to the official API and decode the response."""
        if not self.config.official_api_key:
            raise RequestError("official_api_key is required for official API requests")

        url = self._build_url(api_request.path)
        params = api_request.params
        headers = {
            "Accept": "application/json",
            "X-API-Key": self.config.official_api_key,
        }

        LOGGER.debug(
            "sending official request %s %s params=%s", api_request.method, url, params
        )

        try:
            async with self.config.session.request(
                api_request.method,
                url,
                params=params,
                ssl=self.config.ssl_context,
                headers=headers,
            ) as response:
                body = await response.read()
        except client_exceptions.ClientError as err:
            raise RequestError(f"Error requesting data from {url}: {err}") from None

        if response.status == HTTPStatus.UNAUTHORIZED:
            raise Unauthorized(f"Call {url} received 401 Unauthorized")
        if response.status == HTTPStatus.FORBIDDEN:
            raise Forbidden(f"Call {url} received 403 Forbidden")
        if response.status == HTTPStatus.NOT_FOUND:
            raise ResponseError(f"Call {url} received 404 Not Found")
        if response.status == HTTPStatus.TOO_MANY_REQUESTS:
            raise ResponseError(f"Call {url} received 429 Too Many Requests")
        if response.status == HTTPStatus.BAD_GATEWAY:
            raise BadGateway(f"Call {url} received 502 bad gateway")
        if response.status == HTTPStatus.SERVICE_UNAVAILABLE:
            raise ServiceUnavailable(f"Call {url} received 503 service unavailable")
        if response.status >= HTTPStatus.BAD_REQUEST:
            raise ResponseError(
                f"Call {url} received unexpected status {response.status}"
            )

        return api_request.decode(body)

    def _build_url(self, path: str) -> str:
        """Build direct official API URL for a path."""
        return f"{self.config.official_api_url.rstrip('/')}{path}"
