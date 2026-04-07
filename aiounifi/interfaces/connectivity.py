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

        Handles SSO MFA, 2FA, and error responses. Updates headers on success.
        Raises RequestError or other custom exceptions on failure.
        """
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

    async def _handle_sso_mfa(
        self, url: str, auth: dict[str, Any], mfa_response_data: bytes
    ) -> tuple[aiohttp.ClientResponse, bytes]:
        """Handle SSO MFA challenge for UniFi OS accounts.

        Args:
            url (str): The login URL.
            auth (dict): The authentication payload.
            mfa_response_data (bytes): The response data from the initial login attempt.

        Returns:
            tuple[aiohttp.ClientResponse, bytes]: The response and data after completing SSO MFA.

        Raises:
            RequestError: If no TOTP secret is configured.

        """
        if not self.config.totp_secret:
            raise RequestError("SSO MFA required but no totp_secret configured")
        return await self._login_sso_2fa(
            url, auth, mfa_response_data, self.config.totp_secret
        )

    async def _handle_login_error(
        self,
        url: str,
        auth: dict[str, Any],
        data: TypedApiResponse,
    ) -> None:
        """Handle error responses during login, routing to 2FA retry if applicable.

        Args:
            url (str): The login URL.
            auth (dict): The authentication payload.
            data (TypedApiResponse): The parsed response data.

        Raises:
            AiounifiException: For known error responses.

        """
        error_msg = data["meta"]["msg"]
        error_cls = ERRORS.get(error_msg, AiounifiException)
        if error_cls is TwoFaTokenRequired and self.config.totp_secret:
            await self._attempt_2fa_retry(url, auth, self.config.totp_secret)
            return
        LOGGER.error("Login failed '%s'", data)
        raise error_cls

    async def _attempt_2fa_retry(
        self, url: str, auth: dict[str, Any], totp_secret: str
    ) -> None:
        """Attempt login retry with local 2FA TOTP token.

        Args:
            url (str): The login URL.
            auth (dict): The authentication payload.
            totp_secret (str): The TOTP secret, already confirmed non-None by the caller.

        Raises:
            RequestError: If the 2FA retry response is not valid JSON.
            AiounifiException: If the 2FA login fails due to authentication error.

        """
        response, bytes_data = await self._login_local_2fa(url, auth, totp_secret)
        if not self._is_json_response(response):
            LOGGER.debug("Login 2FA retry not JSON: '%s'", bytes_data)
            raise RequestError("Login Failed: Host starting up")
        data = self._parse_json(bytes_data)
        if self._is_error_response(data):
            LOGGER.error("Login with 2FA failed '%s'", data)
            raise ERRORS.get(data["meta"]["msg"], AiounifiException)
        self._update_login_headers(response)
        self.can_retry_login = True
        LOGGER.debug("Logged in to UniFi %s", url)

    def _is_json_response(self, response: aiohttp.ClientResponse) -> bool:
        """Check if the response has a JSON content type.

        Args:
            response (aiohttp.ClientResponse): The HTTP response object.

        Returns:
            bool: True if the response is JSON, False otherwise.

        """
        return response.content_type == "application/json"

    def _parse_json(self, bytes_data: bytes) -> TypedApiResponse:
        """Parse bytes data as JSON and cast to TypedApiResponse.

        Args:
            bytes_data (bytes): The response body as bytes.

        Returns:
            TypedApiResponse: The parsed and typed response data.

        Raises:
            RequestError: If the data is not valid JSON.

        """
        try:
            return cast("TypedApiResponse", orjson.loads(bytes_data))
        except orjson.JSONDecodeError as err:
            LOGGER.error("Failed to parse JSON: %s", err)
            raise RequestError("Response is not valid JSON") from err

    def _is_error_response(self, data: TypedApiResponse) -> bool:
        """Check if the response data indicates an error.

        Args:
            data (TypedApiResponse): The parsed response data.

        Returns:
            bool: True if the response is an error, False otherwise.

        """
        return data.get("meta", {}).get("rc") == "error"

    def _update_login_headers(self, response: aiohttp.ClientResponse) -> None:
        """Update login headers from the response after successful authentication.

        Args:
            response (aiohttp.ClientResponse): The HTTP response object.

        """
        if (csrf_token := response.headers.get("x-csrf-token")) is not None:
            self.headers["x-csrf-token"] = csrf_token
        if (cookie := response.headers.get("Set-Cookie")) is not None:
            self.headers["Cookie"] = cookie

    async def _login_local_2fa(
        self,
        url: str,
        auth: dict[str, Any],
        totp_secret: str,
    ) -> tuple[aiohttp.ClientResponse, bytes]:
        """Retry login with local 2FA TOTP token for local accounts.

        Args:
            url (str): The login URL.
            auth (dict): The authentication payload.
            totp_secret (str): The TOTP secret for generating the token.

        Returns:
            tuple[aiohttp.ClientResponse, bytes]: The response and data after retrying with 2FA.

        """
        LOGGER.debug("Local 2FA required, retrying with TOTP token")
        token = pyotp.TOTP(totp_secret).now()
        return await self._request("post", url, json={**auth, "ubic_2fa_token": token})

    async def _login_sso_2fa(
        self,
        url: str,
        auth: dict[str, Any],
        mfa_response_data: bytes,
        totp_secret: str,
    ) -> tuple[aiohttp.ClientResponse, bytes]:
        """Complete SSO two-step MFA login for UniFi OS accounts.

        Args:
            url (str): The login URL.
            auth (dict): The authentication payload.
            mfa_response_data (bytes): The response data from the initial login attempt.
            totp_secret (str): The TOTP secret for generating the token.

        Returns:
            tuple[aiohttp.ClientResponse, bytes]: The response and data after completing SSO MFA.

        Raises:
            RequestError: If the response is not valid JSON or missing required fields.

        """
        LOGGER.debug("SSO MFA challenge received, performing two-step auth")

        try:
            body = orjson.loads(mfa_response_data)
        except orjson.JSONDecodeError as err:
            raise RequestError(f"SSO MFA response is not valid JSON: {err}") from err
        mfa_cookie_str: str = body.get("data", {}).get("mfaCookie", "")

        if not mfa_cookie_str or "=" not in mfa_cookie_str:
            raise RequestError("SSO MFA response missing valid mfaCookie")

        cookie_name, cookie_val = mfa_cookie_str.split("=", 1)
        self.config.session.cookie_jar.update_cookies({cookie_name: cookie_val}, url)

        token = pyotp.TOTP(totp_secret).now()
        return await self._request("post", url, json={**auth, "token": token})

    async def request(self, api_request: ApiRequest) -> TypedApiResponse:
        """Make a request to the API, retrying login on failure.

        Args:
            api_request (ApiRequest): The API request object containing method, path, and data.

        Returns:
            TypedApiResponse: The parsed response data from the API.

        Raises:
            LoginRequired: If login is required and cannot be retried.
            RequestError: For network or response errors.

        """
        url = self.config.url + api_request.full_path(
            self.config.site, self.is_unifi_os
        )
        data: TypedApiResponse = {}

        try:
            response, bytes_data = await self._request(
                api_request.method, url, api_request.data
            )

            if response.content_type == "application/json":
                data = api_request.decode(bytes_data)

        except LoginRequired:
            if not self.can_retry_login:
                raise
            # Session likely expired, try again
            self.can_retry_login = False
            await self.login()
            return await self.request(api_request)

        return data

    async def _request(
        self,
        method: str,
        url: str,
        json: Mapping[str, Any] | None = None,
        allow_redirects: bool = True,
    ) -> tuple[aiohttp.ClientResponse, bytes]:
        """Make a raw HTTP request to the API.

        Args:
            method (str): The HTTP method (e.g., 'get', 'post').
            url (str): The full request URL.
            json (Mapping[str, Any] | None): The JSON payload for the request, if any.
            allow_redirects (bool): Whether to allow redirects.

        Returns:
            tuple[aiohttp.ClientResponse, bytes]: The response object and response body as bytes.

        Raises:
            LoginRequired: If the response is 401 Unauthorized.
            Forbidden: If the response is 403 Forbidden.
            ResponseError: For 404, 429, or invalid responses.
            BadGateway: For 502 Bad Gateway.
            ServiceUnavailable: For 503 Service Unavailable.
            RequestError: For network or client errors.
            AuthenticationRateLimitError: For 429 rate limit errors with specific code.

        """
        LOGGER.debug("sending (to %s) %s, %s, %s", url, method, json, allow_redirects)
        bytes_data = b""

        try:
            async with self.config.session.request(
                method,
                url,
                json=json,
                ssl=self.config.ssl_context,
                headers=self.headers,
                allow_redirects=allow_redirects,
            ) as res:
                LOGGER.debug(
                    "received (from %s) %s %s %s",
                    url,
                    res.status,
                    res.content_type,
                    res,
                )

                if res.status == HTTPStatus.UNAUTHORIZED:
                    raise LoginRequired(f"Call {url} received 401 Unauthorized")

                if res.status == HTTPStatus.FORBIDDEN:
                    raise Forbidden(f"Call {url} received 403 Forbidden")

                if res.status == HTTPStatus.NOT_FOUND:
                    raise ResponseError(f"Call {url} received 404 Not Found")

                if res.status == HTTPStatus.BAD_GATEWAY:
                    raise BadGateway(f"Call {url} received 502 bad gateway")

                if res.status == HTTPStatus.SERVICE_UNAVAILABLE:
                    raise ServiceUnavailable(
                        f"Call {url} received 503 service unavailable"
                    )

                bytes_data = await res.read()

        except client_exceptions.ClientError as err:
            raise RequestError(f"Error requesting data from {url}: {err}") from None

        LOGGER.debug("data (from %s) %s", url, bytes_data)

        if res.status == HTTPStatus.TOO_MANY_REQUESTS:
            # Try to parse the response for specific rate limit error
            try:
                data = orjson.loads(bytes_data)
            except orjson.JSONDecodeError:
                data = None
            if (
                isinstance(data, dict)
                and data.get("code") == "AUTHENTICATION_FAILED_LIMIT_REACHED"
            ):
                raise AuthenticationRateLimitError(
                    f"Call {url} received 429: {data.get('message', bytes_data)!r}"
                )
            # Fallback to old logic
            raise ResponseError(f"Call {url} received 429: {bytes_data!r}")

        return res, bytes_data

    async def websocket(self, callback: Callable[[str], None]) -> None:
        """Run the UniFi websocket connection and dispatch messages to a callback.

        Args:
            callback (Callable[[str], None]): Function to call with each received text message.

        Raises:
            aiohttp.ClientConnectorError: If the websocket connection cannot be established.
            aiohttp.WSServerHandshakeError: If the websocket handshake fails.
            WebsocketError: For websocket protocol errors or unexpected exceptions.

        Notes:
            - Only TEXT, CLOSED, and ERROR message types are handled explicitly. Others are logged as warnings.
            - The callback should be non-blocking and fast; slow callbacks may delay message processing.
            - Reconnection logic is not handled here and should be implemented by the consumer.
            - On disconnect or error, an exception is raised for the consumer to handle.

        """
        url = f"wss://{self.config.host}:{self.config.port}"
        url += "/proxy/network" if self.is_unifi_os else ""
        url += f"/wss/s/{self.config.site}/events"

        try:
            async with self.config.session.ws_connect(
                url,
                headers=self.headers,
                ssl=self.config.ssl_context,
                heartbeat=15,
                compress=12,
            ) as websocket_connection:
                LOGGER.debug(
                    "Connected to UniFi websocket %s, headers: %s, cookiejar: %s",
                    url,
                    self.headers,
                    self.config.session.cookie_jar._cookies,  # type: ignore[attr-defined]
                )

                async for message in websocket_connection:
                    self.ws_message_received = datetime.datetime.now(datetime.UTC)

                    if message.type is aiohttp.WSMsgType.TEXT:
                        LOGGER.debug("Websocket '%s'", message.data)
                        callback(message.data)

                    elif message.type is aiohttp.WSMsgType.CLOSED:
                        LOGGER.warning(
                            "Connection closed to UniFi websocket '%s'", message.data
                        )
                        break

                    elif message.type is aiohttp.WSMsgType.ERROR:
                        LOGGER.error("UniFi websocket error: '%s'", message.data)
                        raise WebsocketError(message.data)

                    else:
                        LOGGER.warning(
                            "Unexpected websocket message type '%s' with data '%s'",
                            message.type,
                            message.data,
                        )

        except aiohttp.ClientConnectorError as err:
            LOGGER.error("Error connecting to UniFi websocket: '%s'", err)
            err.add_note("Error connecting to UniFi websocket")
            raise

        except aiohttp.WSServerHandshakeError as err:
            LOGGER.error(
                "Server handshake error connecting to UniFi websocket: '%s'", err
            )
            err.add_note("Server handshake error connecting to UniFi websocket")
            raise

        except WebsocketError:
            raise

        except Exception as err:
            LOGGER.exception(err)
            raise WebsocketError from err
