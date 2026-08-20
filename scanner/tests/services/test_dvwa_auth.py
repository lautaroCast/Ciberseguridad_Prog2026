"""Unit tests for the DVWA login + security-level helper (Recomendación #5,
docs/independent-evaluation-report.md), mocking the HTTP layer with
httpx.MockTransport so these run without a real DVWA reachable."""

import httpx
import pytest

from app.services import dvwa_auth

_LOGIN_PAGE = "<form><input type='hidden' name='user_token' value='deadbeef01'></form>"
_SECURITY_PAGE = "<form><input type='hidden' name='user_token' value='cafebabe02'></form>"


def _install_transport(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def _patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", _patched_client)


def test_happy_path_returns_combined_cookie(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        path, method = request.url.path, request.method
        if path == "/login.php" and method == "GET":
            return httpx.Response(200, text=_LOGIN_PAGE)
        if path == "/login.php" and method == "POST":
            assert b"user_token=deadbeef01" in request.content
            assert b"username=admin" in request.content
            return httpx.Response(
                302, headers=[("set-cookie", "PHPSESSID=sess123; Path=/")]
            )
        if path == "/security.php" and method == "GET":
            return httpx.Response(200, text=_SECURITY_PAGE)
        if path == "/security.php" and method == "POST":
            assert b"user_token=cafebabe02" in request.content
            assert b"security=low" in request.content
            return httpx.Response(302, headers=[("set-cookie", "security=low; Path=/")])
        raise AssertionError(f"unexpected request: {method} {path}")

    _install_transport(monkeypatch, handler)

    cookie = dvwa_auth.get_authenticated_cookie("dvwa", port=80, scheme="http")
    assert "PHPSESSID=sess123" in cookie
    assert "security=low" in cookie


def test_missing_token_raises_dvwa_auth_error(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>no token here</html>")

    _install_transport(monkeypatch, handler)

    with pytest.raises(dvwa_auth.DvwaAuthError):
        dvwa_auth.get_authenticated_cookie("dvwa", port=80, scheme="http")


def test_login_failure_status_raises(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/login.php" and request.method == "GET":
            return httpx.Response(200, text=_LOGIN_PAGE)
        if request.url.path == "/login.php" and request.method == "POST":
            return httpx.Response(500)
        raise AssertionError("should not reach security.php after a failed login")

    _install_transport(monkeypatch, handler)

    with pytest.raises(dvwa_auth.DvwaAuthError, match="login failed"):
        dvwa_auth.get_authenticated_cookie("dvwa", port=80, scheme="http")
