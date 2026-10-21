"""Python library to enable integration between Home Assistant and UniFi."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import datetime
from http import HTTPStatus, cookies
import logging
import re
from time import monotonic
from typing import TYPE_CHECKING, Any, NoReturn, cast

import aiohttp
from aiohttp import client_exceptions
import orjson
import pyotp
from yarl import URL

from ..errors import (
    AiounifiException,
    ApplicationNotReady,
    AuthenticationRateLimitError,
    BadGateway,
    EndpointNotFound,
    Forbidden,
    LoginRequired,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    TwoFaTokenRequired,
    Unauthorized,
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
# The standalone Network application serves its pages below /manage/, also
# the status page it answers every path with while it starts. A page without
# the marker is taken for UniFi OS, as before.
STANDALONE_PAGE_MARKER = re.compile(rb"<base\s+href=[\"']/manage/[\"']", re.IGNORECASE)
# Shortest time between two logins that requests make on their own
RELOGIN_INTERVAL = 60
# Wait longer after a login rate limit, which each attempt extends, and after
# a 403, which UniFi OS answers for wrong credentials and temporary failures
RELOGIN_PAUSE = 300
# Name and value of the cookie the SSO MFA challenge hands back
MFA_COOKIE = re.compile(r"([!#$%&'*+\-.^_`|~0-9A-Za-z]+)=([^;\s]+)")


def _error_detail(body: bytes | Mapping[str, Any]) -> str:
    """Return the server's error message as a suffix for an exception message.

    The raw body is left out, a proxy could echo the request with credentials.

    Args:
        body (bytes | Mapping[str, Any]): The response body, raw or parsed.

    Returns:
        str: ": <message>" for a JSON body with an error message, else "".

    """
    data: Any = body
    if isinstance(body, bytes):
        try:
            data = orjson.loads(body)
        except orjson.JSONDecodeError:
            return ""
    if not isinstance(data, Mapping):
        return ""
    for item in (data, data.get("meta"), data.get("error")):
        if not isinstance(item, Mapping):
            continue
        for key in ("message", "msg"):
            msg = item.get(key)
            if isinstance(msg, str) and (msg := " ".join(msg.split())):
                return f": {msg[:100]}"
    return ""


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
        self._last_relogin: float | None = None
        self.ws_message_received: datetime.datetime | None = None

        if config.ssl_context:
            LOGGER.warning("Using SSL context %s", config.ssl_context)

    async def check_unifi_os(self) -> None:
        """Check if the controller is running UniFi OS.

        Sets self.is_unifi_os to True if UniFi OS is detected, otherwise False.
        Clears the cookie jar for the host if UniFi OS is detected.
        """
        response, bytes_data = await self._request(
            "get", self.config.url, allow_redirects=False
        )
        # Assigned only after the response, requests meanwhile keep the known path
        self.is_unifi_os = response.status == HTTPStatus.OK and not (
            STANDALONE_PAGE_MARKER.search(bytes_data)
        )
        if self.is_unifi_os:
            self.config.session.cookie_jar.clear_domain(self._cookie_domain)
        LOGGER.debug("Talking to UniFi OS device: %s", self.is_unifi_os)

    async def login(self) -> None:
        """Log in to the UniFi controller.

        Handles SSO MFA, 2FA, and error responses. Updates headers on success.

        Raises:
            ApplicationNotReady: If the host answers without JSON while starting.
            TwoFaTokenRequired: If MFA is required and cannot be completed.
            ResponseError: If the login fails with an error status.
            RequestError: For network errors or invalid JSON.
            AiounifiException: For other login errors.

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
            self._raise_not_json(url, response, bytes_data)

        data = self._parse_json(bytes_data)
        if self._is_error_response(data):
            await self._handle_login_error(url, auth, data)
        else:
            self._raise_on_error_status(response, data)
            self._logged_in(url, response)

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
            TwoFaTokenRequired: If no TOTP secret is configured.

        """
        if not self.config.totp_secret:
            raise TwoFaTokenRequired("SSO MFA required but no totp_secret configured")
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
        error_cls = self._login_error(data)
        if error_cls is TwoFaTokenRequired and self.config.totp_secret:
            await self._attempt_2fa_retry(url, auth, self.config.totp_secret)
            return
        LOGGER.error("Login failed: %s", data["meta"].get("msg"))
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
            ApplicationNotReady: If the 2FA retry response is not JSON.
            TwoFaTokenRequired: If MFA is still required.
            ResponseError: If the 2FA retry fails with an error status.
            RequestError: If the 2FA retry response is not valid JSON.
            AiounifiException: If the 2FA login fails due to authentication error.

        """
        response, bytes_data = await self._login_local_2fa(url, auth, totp_secret)
        if not self._is_json_response(response):
            self._raise_not_json(url, response, bytes_data)
        data = self._parse_json(bytes_data)
        if self._is_error_response(data):
            LOGGER.error("Login with 2FA failed: %s", data["meta"].get("msg"))
            raise self._login_error(data)
        self._raise_on_error_status(response, data)
        self._logged_in(url, response)

    def _raise_on_error_status(
        self, response: aiohttp.ClientResponse, data: TypedApiResponse
    ) -> None:
        """Raise if a login response without an error envelope failed anyway.

        Args:
            response (aiohttp.ClientResponse): The HTTP response object.
            data (TypedApiResponse): The parsed response data.

        Raises:
            TwoFaTokenRequired: If MFA is still required after the MFA step.
            ResponseError: For other error statuses.

        """
        if response.status == HTTP_STATUS_MFA_REQUIRED:
            raise TwoFaTokenRequired("MFA token was not accepted")
        if response.status >= HTTPStatus.BAD_REQUEST:
            LOGGER.debug("Login failed '%s'", data)
            raise ResponseError(
                f"Login received {response.status}{_error_detail(data)}"
            )

    def _raise_not_json(
        self, url: str, response: aiohttp.ClientResponse, bytes_data: bytes
    ) -> NoReturn:
        """Raise for a response that is not JSON.

        Args:
            url (str): The request URL.
            response (aiohttp.ClientResponse): The HTTP response object.
            bytes_data (bytes): The response body as bytes.

        Raises:
            ResponseError: If the response has an error status.
            ApplicationNotReady: Otherwise, a starting application answers so.

        """
        LOGGER.debug("Response from %s is not JSON: %r", url, bytes_data[:200])
        if response.status >= HTTPStatus.BAD_REQUEST:
            raise ResponseError(
                f"Call {url} received {response.status} {response.content_type}"
            )
        raise ApplicationNotReady(
            f"Call {url} received {response.content_type}, not JSON"
        )

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
            ResponseError: If the data is not a JSON object.

        """
        try:
            data = orjson.loads(bytes_data)
        except orjson.JSONDecodeError as err:
            LOGGER.error("Failed to parse JSON: %s", err)
            raise RequestError("Response is not valid JSON") from err
        if not isinstance(data, dict):
            raise ResponseError("Response is not a JSON object")
        return cast("TypedApiResponse", data)

    def _is_error_response(self, data: TypedApiResponse) -> bool:
        """Check if the response data indicates an error.

        Args:
            data (TypedApiResponse): The parsed response data.

        Returns:
            bool: True if the response is an error, False otherwise.

        """
        meta = data.get("meta")
        return isinstance(meta, dict) and meta.get("rc") == "error"

    def _login_error(self, data: TypedApiResponse) -> type[AiounifiException]:
        """Return the exception class for a login error response.

        Args:
            data (TypedApiResponse): The parsed error response data.

        Returns:
            type[AiounifiException]: The exception class to raise.

        """
        msg = data["meta"].get("msg")
        if not isinstance(msg, str):
            return AiounifiException
        return ERRORS.get(msg, AiounifiException)

    def _logged_in(self, url: str, response: aiohttp.ClientResponse) -> None:
        """Store the session of a successful login.

        Args:
            url (str): The login URL.
            response (aiohttp.ClientResponse): The HTTP response object.

        """
        self._update_login_headers(response)
        self.can_retry_login = True
        LOGGER.debug("Logged in to UniFi %s", url)

    @property
    def _cookie_domain(self) -> str:
        """Return the host as cookie jars store it."""
        return URL(self.config.url).raw_host or self.config.host

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
        data = body.get("data") if isinstance(body, dict) else None
        mfa_cookie_str = data.get("mfaCookie") if isinstance(data, dict) else None

        if not (
            isinstance(mfa_cookie_str, str)
            and mfa_cookie_str.isprintable()
            and (match := MFA_COOKIE.fullmatch(mfa_cookie_str.split(";")[0].strip()))
        ):
            raise RequestError("SSO MFA response missing valid mfaCookie")

        # A stale value in the jar would take precedence over the header
        host = self._cookie_domain
        self.config.session.cookie_jar.clear(
            lambda morsel: (
                morsel.key == match.group(1)
                and (
                    not morsel["domain"]
                    or host == morsel["domain"]
                    or host.endswith(f".{morsel['domain']}")
                )
            )
        )

        token = pyotp.TOTP(totp_secret).now()
        # Sent as a header, a cookie jar may drop cookies for IP address hosts
        return await self._request(
            "post",
            url,
            json={**auth, "token": token},
            headers={"Cookie": match.group(0)},
        )

    async def request(self, api_request: ApiRequest) -> TypedApiResponse:
        """Make a request to the API, logging in again on an expired session.

        Requests log in on their own at most once per RELOGIN_INTERVAL, so an
        API that keeps answering 401 does not cause a login on every request.
        After a login rate limit or a 403 they wait RELOGIN_PAUSE, and after
        rejected credentials they wait for the next successful login.

        Args:
            api_request (ApiRequest): The API request object containing method, path, and data.

        Returns:
            TypedApiResponse: The parsed response data from the API.

        Raises:
            LoginRequired: If the session expired and logging in again is not
                allowed yet, or the request still got 401 after logging in.
            AiounifiException: For the errors of login and the request, see
                login and _api_request.

        """
        try:
            return await self._api_request(api_request)
        except LoginRequired:
            now = monotonic()
            if not self.can_retry_login or (
                self._last_relogin is not None
                and now - self._last_relogin < RELOGIN_INTERVAL
            ):
                raise
            self._last_relogin = now
        # Session likely expired, log in again
        if self.is_unifi_os:
            # A session cookie sent without its CSRF token fails the login
            self.config.session.cookie_jar.clear_domain(self._cookie_domain)
        try:
            await self.login()
        except (AuthenticationRateLimitError, Forbidden):
            self._last_relogin = now + RELOGIN_PAUSE - RELOGIN_INTERVAL
            raise
        except (TwoFaTokenRequired, Unauthorized):
            # Rejected credentials, leave the next login to the caller
            self.can_retry_login = False
            raise
        return await self._api_request(api_request)

    async def _api_request(self, api_request: ApiRequest) -> TypedApiResponse:
        """Make a request to the API.

        Args:
            api_request (ApiRequest): The API request object containing method, path, and data.

        Returns:
            TypedApiResponse: The parsed response data from the API.

        Raises:
            LoginRequired: If the session is not logged in.
            ApplicationNotReady: If a response without an error status is not JSON.
            ResponseError: For error statuses without a known error, or data
                of unexpected shape.
            RequestError: For network or response errors, or invalid JSON.

        """
        url = self.config.url + api_request.full_path(
            self.config.site, self.is_unifi_os
        )
        data: TypedApiResponse = {}
        response, bytes_data = await self._request(
            api_request.method, url, api_request.data
        )

        if bytes_data and not self._is_json_response(response):
            self._raise_not_json(url, response, bytes_data)
        if bytes_data:
            try:
                # Raises the known error of an error envelope
                data = api_request.decode(bytes_data)
            except orjson.JSONDecodeError as err:
                raise RequestError(f"Call {url} received invalid JSON: {err}") from err
            # Envelopes of unexpected shape, also in handler specific decoders
            except (AttributeError, KeyError, TypeError) as err:
                raise ResponseError(
                    f"Call {url} received {response.status} with unexpected "
                    f"data: {err!r}"
                ) from err
        if response.status >= HTTPStatus.BAD_REQUEST:
            raise ResponseError(
                f"Call {url} received {response.status}{_error_detail(bytes_data)}"
            )
        return data

    async def _request(
        self,
        method: str,
        url: str,
        json: Mapping[str, Any] | None = None,
        allow_redirects: bool = True,
        headers: Mapping[str, str] | None = None,
    ) -> tuple[aiohttp.ClientResponse, bytes]:
        """Make a raw HTTP request to the API.

        Args:
            method (str): The HTTP method (e.g., 'get', 'post').
            url (str): The full request URL.
            json (Mapping[str, Any] | None): The JSON payload for the request, if any.
            allow_redirects (bool): Whether to allow redirects.
            headers (Mapping[str, str] | None): Headers to send in addition.

        Returns:
            tuple[aiohttp.ClientResponse, bytes]: The response object and response body as bytes.

        Raises:
            LoginRequired: If the response is 401 Unauthorized.
            Forbidden: If the response is 403 Forbidden.
            ResponseError: For 404, 429, or invalid responses.
            BadGateway: For 502 Bad Gateway.
            ServiceUnavailable: For 503 Service Unavailable.
            RequestError: For other 5xx responses and network or client errors.
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
                headers={**self.headers, **(headers or {})},
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
                    raise EndpointNotFound(f"Call {url} received 404 Not Found")

                if res.status == HTTPStatus.BAD_GATEWAY:
                    raise BadGateway(f"Call {url} received 502 bad gateway")

                if res.status == HTTPStatus.SERVICE_UNAVAILABLE:
                    raise ServiceUnavailable(
                        f"Call {url} received 503 service unavailable"
                    )

                if res.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
                    body = await res.read()
                    LOGGER.debug("data (from %s) %r", url, body[:200])
                    raise RequestError(
                        f"Call {url} received {res.status}{_error_detail(body)}"
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
                    f"Call {url} received 429{_error_detail(bytes_data)}"
                )
            # Fallback to old logic
            raise ResponseError(f"Call {url} received 429{_error_detail(bytes_data)}")

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
