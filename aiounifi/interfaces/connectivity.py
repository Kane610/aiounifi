"""Python library to enable integration between Home Assistant and UniFi."""

from collections.abc import Callable, Mapping
from http import HTTPStatus
import logging
from typing import TYPE_CHECKING, Any

import aiohttp
from aiohttp import client_exceptions
import orjson

from ..errors import (
    AiounifiException,
    BadGateway,
    Forbidden,
    LoginRequired,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    WebsocketError,
)
from ..models.api import ERRORS
from ..models.configuration import Configuration

if TYPE_CHECKING:
    from ..models.api import ApiRequest, TypedApiResponse

LOGGER = logging.getLogger(__name__)


class Connectivity:
    """UniFi Network Application connectivity."""

    def __init__(self, config: Configuration) -> None:
        """Session setup."""
        self.config = config

        self.is_unifi_os = False
        self.headers: dict[str, str] = {}
        self.can_retry_login = False

    async def check_unifi_os(self) -> None:
        """Check if controller is running UniFi OS."""
        response, _ = await self._request("get", self.config.url, allow_redirects=False)
        if response.status == HTTPStatus.OK:
            self.is_unifi_os = True
            self.config.session.cookie_jar.clear_domain(self.config.host)
        LOGGER.debug("Talking to UniFi OS device: %s", self.is_unifi_os)

    async def login(self) -> None:
        """Log in to controller."""
        self.headers.clear()
        url = f"{self.config.url}/api{'/auth/login' if self.is_unifi_os else '/login'}"

        auth = {
            "username": self.config.username,
            "password": self.config.password,
            "remember": True,
        }

        response, bytes_data = await self._request("post", url, json=auth)

        if response.content_type == "application/json":
            data: "TypedApiResponse" = orjson.loads(bytes_data)
            if "meta" in data and data["meta"]["rc"] == "error":
                LOGGER.error("Login failed '%s'", data)
                raise ERRORS.get(data["meta"]["msg"], AiounifiException)

        if (
            response.status == HTTPStatus.OK
            and (csrf_token := response.headers.get("x-csrf-token")) is not None
        ):
            self.headers["x-csrf-token"] = csrf_token

        self.can_retry_login = True
        LOGGER.debug("Logged in to UniFi %s", url)

    async def request(self, api_request: "ApiRequest") -> "TypedApiResponse":
        """Make a request to the API, retry login on failure."""
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
        **kwargs: bool,
    ) -> tuple[aiohttp.ClientResponse, bytes]:
        """Make a request to the API."""
        LOGGER.debug("sending (to %s) %s, %s, %s", url, method, json, kwargs)
        bytes_data = b""

        try:
            async with self.config.session.request(
                method,
                url,
                json=json,
                ssl=self.config.ssl_context,
                headers=self.headers,
                **kwargs,
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
        return res, bytes_data

    async def websocket(self, callback: Callable[[bytes], None]) -> None:
        """Run websocket."""
        url = f"wss://{self.config.host}:{self.config.port}"
        url += "/proxy/network" if self.is_unifi_os else ""
        url += f"/wss/s/{self.config.site}/events"

        try:
            async with self.config.session.ws_connect(
                url, ssl=self.config.ssl_context, heartbeat=15
            ) as websocket_connection:
                LOGGER.debug("Connected to UniFi websocket %s", url)

                async for message in websocket_connection:
                    if message.type == aiohttp.WSMsgType.TEXT:
                        LOGGER.debug("Websocket '%s'", message.data)
                        callback(message.data)

                    elif message.type == aiohttp.WSMsgType.CLOSED:
                        LOGGER.warning(
                            "Connection closed to UniFi websocket '%s'", message.data
                        )
                        break

                    elif message.type == aiohttp.WSMsgType.ERROR:
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

        except WebsocketError:
            raise

        except Exception as err:
            LOGGER.exception(err)
            raise WebsocketError from err
