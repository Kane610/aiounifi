"""Python library to enable integration between Home Assistant and UniFi."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import datetime
from http import HTTPStatus, cookies
import logging
from typing import TYPE_CHECKING, Any, cast

import aiohttp
from aiohttp import client_exceptions
import orjson
import pyotp
from yarl import URL

from ..errors import (
    AiounifiException,
    AuthenticationRateLimitError,
    BadGateway,
    Forbidden,
    LoginRequired,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    TwoFaTokenRequired,
    WebsocketError,
)
from ..models.api import ERRORS
from ..models.configuration import Configuration
from ..network.v1.connectivity import Connectivity as NetworkConnectivity
from ..network.v1.models.info import InfoRequest

if "partitioned" not in cookies.Morsel._reserved:  # type: ignore[attr-defined]
    # See: https://github.com/python/cpython/issues/112713
    cookies.Morsel._reserved["partitioned"] = "partitioned"  # type: ignore[attr-defined]
    cookies.Morsel._flags.add("partitioned")  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from ..models.api import ApiRequest, TypedApiResponse

LOGGER = logging.getLogger(__name__)

HTTP_STATUS_MFA_REQUIRED = 499


class Connectivity:
    """UniFi Network Application connectivity."""

    def __init__(self, config: Configuration) -> None:
        """Initialize the Connectivity instance for UniFi Network Application.

        Args:
            config (Configuration): The configuration object containing connection details.

        """
        self.config = config

        self.is_unifi_os = False
        self.headers: dict[str, str] = {}
        self.can_retry_login = False
        self.ws_message_received: datetime.datetime | None = None

        if config.ssl_context:
            LOGGER.warning("Using SSL context %s", config.ssl_context)

    async def check_unifi_os(self) -> None:
        """Check if the controller is running UniFi OS.

        Sets self.is_unifi_os to True if UniFi OS is detected, otherwise False.
        Clears the cookie jar for the host if UniFi OS is detected.
        """
        self.is_unifi_os = False
        response, _ = await self._request("get", self.config.url, allow_redirects=False)
        if response.status == HTTPStatus.OK:
            self.is_unifi_os = True
            self.config.session.cookie_jar.clear_domain(self.config.host)
        LOGGER.debug("Talking to UniFi OS device: %s", self.is_unifi_os)

    async def login(self) -> None:
        """Log in to the UniFi controller.

        Username/password uses the classic session cookie API. An API key is
        validated against the official Integration API instead; keys are not
        used with classic `/api` endpoints.
        """
        if self.config.api_key and not (self.config.username and self.config.password):
            await self._login_with_api_key()
            return

        if not self.config.username or not self.config.password:
            raise LoginRequired("Username and password or api_key must be provided")

        self.headers.clear()
        url = f"{self.config.url}/api{'/auth/login' if self.is_unifi_os else '/login'}"
        auth: dict[str, Any] = {
            "username": self.config.username,
            "password": self.config.password,
            "rememberMe": True,
        }
        response, bytes_data = await self._request("post", url, json=auth)

        if response.status == HTTP_STATUS_MFA_REQUIRED:
            response, bytes_data = await self._handle_sso_mfa(url, auth, bytes_data)

        if not self._is_json_response(response):
            LOGGER.debug("Login Failed not JSON: '%s'", bytes_data)
            raise RequestError("Login Failed: Host starting up")

        data = self._parse_json(bytes_data)
        if self._is_error_response(data):
            await self._handle_login_error(url, auth, data)
        else:
            self._update_login_headers(response)
            self.can_retry_login = True
            LOGGER.debug("Logged in to UniFi %s", url)

    async def _login_with_api_key(self) -> None:
        """Validate an Integration API key against GET /v1/info.

        Classic controller login is skipped because API keys authenticate the
        official Network Integration API, not `/api/login`.
        """
        LOGGER.debug("Using API key authentication, skipping classic login")
        await NetworkConnectivity(self.config).request(InfoRequest.create())
        self.can_retry_login = False
        LOGGER.debug("Authenticated to UniFi Integration API")
