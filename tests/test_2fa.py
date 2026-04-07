"""Test 2FA authentication flows.

pytest --cov-report term-missing --cov=aiounifi.interfaces.connectivity tests/test_2fa.py
"""

from unittest.mock import Mock, patch

import aiohttp
from aioresponses import aioresponses
from yarl import URL
import pytest

from aiounifi.controller import Controller
from aiounifi.errors import RequestError, TwoFaTokenRequired, Unauthorized
from aiounifi.models.configuration import Configuration

from .fixtures import LOGIN_UNIFIOS_JSON_RESPONSE

TOTP_SECRET = "JBSWY3DPEHPK3PXP"

LOCAL_2FA_ERROR_RESPONSE = {
    "meta": {"msg": "api.err.Ubic2faTokenRequired", "rc": "error"},
    "data": [],
}

SSO_MFA_RESPONSE = {
    "data": {"mfaCookie": "UBIC_2FA=abc123def456"},
    "meta": {"msg": "", "rc": "ok"},
}


@pytest.fixture(name="mock_aioresponse")
def aioresponse_fixture() -> aioresponses:
    """AIOHTTP fixture."""
    with aioresponses() as mock:
        yield mock


@pytest.fixture(name="totp_secret")
def totp_secret_fixture() -> str | None:
    """TOTP secret for 2FA."""
    return TOTP_SECRET


@pytest.fixture(name="unifi_controller_2fa")
async def unifi_controller_2fa_fixture(totp_secret: str | None) -> Controller:
    """Provide a test-ready UniFi controller with 2FA configured."""
    session = aiohttp.ClientSession()
    config = Configuration(
        session,
        "host",
        username="user",
        password="pass",
        totp_secret=totp_secret,
    )
    controller = Controller(config)
    controller.ws_state_callback = Mock()
    yield controller
    await session.close()


class TestLocal2fa:
    """Test local account 2FA authentication."""

    async def test_local_2fa_login_success(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test login with local 2FA succeeds when totp_secret is configured."""
        # First request returns 2FA required error
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload=LOCAL_2FA_ERROR_RESPONSE,
            content_type="application/json",
        )
        # Second request with ubic_2fa_token succeeds
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload={"meta": {"rc": "ok"}, "data": []},
            content_type="application/json",
        )

        await unifi_controller_2fa.connectivity.login()
        assert unifi_controller_2fa.connectivity.can_retry_login

        # Verify the second request included ubic_2fa_token
        requests = list(mock_aioresponse.requests.values())
        assert len(requests) == 1  # Both POSTs to same URL
        calls = requests[0]
        assert len(calls) == 2

        second_call_json = calls[1][1]["json"]
        assert "ubic_2fa_token" in second_call_json
        assert second_call_json["username"] == "user"
        assert second_call_json["password"] == "pass"
        assert second_call_json["rememberMe"] is True

    async def test_local_2fa_raises_without_totp_secret(self, mock_aioresponse):
        """Test local 2FA raises TwoFaTokenRequired when no totp_secret."""
        session = aiohttp.ClientSession()
        config = Configuration(
            session,
            "host",
            username="user",
            password="pass",
        )
        controller = Controller(config)

        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload=LOCAL_2FA_ERROR_RESPONSE,
            content_type="application/json",
        )

        with pytest.raises(TwoFaTokenRequired):
            await controller.connectivity.login()

        await session.close()

    async def test_local_2fa_login_retry_fails(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test login when 2FA retry also fails."""
        # First request returns 2FA required error
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload=LOCAL_2FA_ERROR_RESPONSE,
            content_type="application/json",
        )
        # Second request with token also fails
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload={
                "meta": {"msg": "api.err.Invalid", "rc": "error"},
                "data": [],
            },
            content_type="application/json",
        )

        with pytest.raises(Unauthorized):
            await unifi_controller_2fa.connectivity.login()

    async def test_local_2fa_generates_valid_totp(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test that a valid TOTP code is generated from the secret."""
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload=LOCAL_2FA_ERROR_RESPONSE,
            content_type="application/json",
        )
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload={"meta": {"rc": "ok"}, "data": []},
            content_type="application/json",
        )

        with patch("pyotp.TOTP.now", return_value="123456") as mock_totp:
            await unifi_controller_2fa.connectivity.login()
            mock_totp.assert_called_once()

        requests = list(mock_aioresponse.requests.values())
        calls = requests[0]
        assert calls[1][1]["json"]["ubic_2fa_token"] == "123456"

    async def test_local_2fa_non_unifi_os_path(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test non-UniFi OS controller uses /api/login path for local 2FA."""
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload=LOCAL_2FA_ERROR_RESPONSE,
            content_type="application/json",
        )
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload={"meta": {"rc": "ok"}, "data": []},
            content_type="application/json",
        )

        await unifi_controller_2fa.connectivity.login()
        assert unifi_controller_2fa.connectivity.can_retry_login

    async def test_local_2fa_retry_non_json_response(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test local 2FA retry raises RequestError when response is not JSON."""
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload=LOCAL_2FA_ERROR_RESPONSE,
            content_type="application/json",
        )
        mock_aioresponse.post(
            "https://host:8443/api/login",
            body="<html>Error</html>",
            content_type="text/html",
        )

        with pytest.raises(RequestError, match="Host starting up"):
            await unifi_controller_2fa.connectivity.login()


class TestSso2fa:
    """Test SSO two-step 2FA authentication."""

    async def test_sso_2fa_login_success(self, mock_aioresponse, unifi_controller_2fa):
        """Test SSO 2FA login completes the two-step flow."""
        unifi_controller_2fa.connectivity.is_unifi_os = True

        # First request returns HTTP 499 with MFA cookie
        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=SSO_MFA_RESPONSE,
            status=499,
            content_type="application/json",
        )
        # Second request with token succeeds
        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=LOGIN_UNIFIOS_JSON_RESPONSE,
            headers={"x-csrf-token": "123"},
            content_type="application/json",
        )

        await unifi_controller_2fa.connectivity.login()
        assert unifi_controller_2fa.connectivity.can_retry_login
        assert unifi_controller_2fa.connectivity.headers["x-csrf-token"] == "123"

        # Verify second request included token field
        requests = list(mock_aioresponse.requests.values())
        calls = requests[0]
        assert len(calls) == 2

        second_call_json = calls[1][1]["json"]
        assert "token" in second_call_json
        assert second_call_json["username"] == "user"
        assert second_call_json["password"] == "pass"

    async def test_sso_2fa_raises_without_totp_secret(self, mock_aioresponse):
        """Test SSO MFA raises RequestError when no totp_secret configured."""
        session = aiohttp.ClientSession()
        config = Configuration(
            session,
            "host",
            username="user",
            password="pass",
        )
        controller = Controller(config)
        controller.connectivity.is_unifi_os = True

        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=SSO_MFA_RESPONSE,
            status=499,
            content_type="application/json",
        )

        with pytest.raises(RequestError, match="SSO MFA required"):
            await controller.connectivity.login()

        await session.close()

    async def test_sso_2fa_missing_mfa_cookie(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test SSO 2FA raises when mfaCookie is missing from response."""
        unifi_controller_2fa.connectivity.is_unifi_os = True

        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload={"data": {}, "meta": {"msg": "", "rc": "ok"}},
            status=499,
            content_type="application/json",
        )

        with pytest.raises(RequestError, match="missing valid mfaCookie"):
            await unifi_controller_2fa.connectivity.login()

    async def test_sso_2fa_invalid_mfa_cookie_format(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test SSO 2FA raises when mfaCookie has invalid format."""
        unifi_controller_2fa.connectivity.is_unifi_os = True

        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload={
                "data": {"mfaCookie": "invalid_no_equals"},
                "meta": {"msg": "", "rc": "ok"},
            },
            status=499,
            content_type="application/json",
        )

        with pytest.raises(RequestError, match="missing valid mfaCookie"):
            await unifi_controller_2fa.connectivity.login()

    async def test_sso_2fa_non_json_mfa_response(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test SSO 2FA raises RequestError when 499 response body is not valid JSON."""
        unifi_controller_2fa.connectivity.is_unifi_os = True

        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            body=b"<html>not json</html>",
            status=499,
            content_type="text/html",
        )

        with pytest.raises(RequestError, match="not valid JSON"):
            await unifi_controller_2fa.connectivity.login()

    async def test_sso_2fa_sets_cookie_on_session(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test SSO 2FA correctly sets the MFA cookie on the session."""
        unifi_controller_2fa.connectivity.is_unifi_os = True

        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=SSO_MFA_RESPONSE,
            status=499,
            content_type="application/json",
        )
        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=LOGIN_UNIFIOS_JSON_RESPONSE,
            headers={"x-csrf-token": "123"},
            content_type="application/json",
        )

        session = unifi_controller_2fa.connectivity.config.session
        with patch.object(
            session.cookie_jar,
            "update_cookies",
            wraps=session.cookie_jar.update_cookies,
        ) as mock_update:
            await unifi_controller_2fa.connectivity.login()
            mock_update.assert_called_once_with(
                {"UBIC_2FA": "abc123def456"}, URL("https://host:8443/api/auth/login")
            )

    async def test_sso_2fa_generates_valid_totp(
        self, mock_aioresponse, unifi_controller_2fa
    ):
        """Test that SSO 2FA generates a valid TOTP code."""
        unifi_controller_2fa.connectivity.is_unifi_os = True

        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=SSO_MFA_RESPONSE,
            status=499,
            content_type="application/json",
        )
        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=LOGIN_UNIFIOS_JSON_RESPONSE,
            headers={"x-csrf-token": "123"},
            content_type="application/json",
        )

        with patch("pyotp.TOTP.now", return_value="654321") as mock_totp:
            await unifi_controller_2fa.connectivity.login()
            mock_totp.assert_called_once()

        requests = list(mock_aioresponse.requests.values())
        calls = requests[0]
        assert calls[1][1]["json"]["token"] == "654321"


class TestConfigurationTotpSecret:
    """Test Configuration dataclass with totp_secret."""

    async def test_configuration_default_totp_secret(self):
        """Test Configuration has None as default totp_secret."""
        session = aiohttp.ClientSession()
        config = Configuration(session, "host", username="user", password="pass")
        assert config.totp_secret is None
        await session.close()

    async def test_configuration_with_totp_secret(self):
        """Test Configuration accepts totp_secret."""
        session = aiohttp.ClientSession()
        config = Configuration(
            session, "host", username="user", password="pass", totp_secret=TOTP_SECRET
        )
        assert config.totp_secret == TOTP_SECRET
        await session.close()


class TestBackwardCompatibility:
    """Test that existing behavior is preserved when totp_secret is not set."""

    async def test_normal_login_unchanged(self, mock_aioresponse):
        """Test normal login without 2FA works as before."""
        session = aiohttp.ClientSession()
        config = Configuration(
            session,
            "host",
            username="user",
            password="pass",
        )
        controller = Controller(config)

        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload={"meta": {"rc": "ok"}, "data": []},
            content_type="application/json",
        )

        await controller.connectivity.login()
        assert controller.connectivity.can_retry_login

        await session.close()

    async def test_unifios_login_unchanged(self, mock_aioresponse):
        """Test UniFi OS login without 2FA works as before."""
        session = aiohttp.ClientSession()
        config = Configuration(
            session,
            "host",
            username="user",
            password="pass",
        )
        controller = Controller(config)
        controller.connectivity.is_unifi_os = True

        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=LOGIN_UNIFIOS_JSON_RESPONSE,
            headers={"x-csrf-token": "123", "Set-Cookie": "456"},
            content_type="application/json",
        )

        await controller.connectivity.login()
        assert controller.connectivity.can_retry_login
        assert controller.connectivity.headers["x-csrf-token"] == "123"
        assert controller.connectivity.headers["Cookie"] == "456"

        await session.close()
