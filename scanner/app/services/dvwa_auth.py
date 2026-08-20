"""DVWA authentication: login + set security level to 'low'.

Used to obtain a session cookie for authenticated scans against DVWA
(`options={"authenticated": true}` on `POST /scan/{tool}`) — DVWA requires
a logged-in session for essentially every vulnerable page regardless of
security level, and a fresh session defaults to a security level that
neuters most vulnerabilities even once authenticated. Both steps are
CSRF-protected (a `user_token` scraped from the form itself), the same
mechanism `lab/dvwa-init/entrypoint.sh` already uses for the one-shot
database bootstrap — this reuses the identical "GET for token, POST with
token" pattern, verified by hand against the running lab before writing
this module.

Credentials (admin/password) are DVWA's own fixed, publicly documented lab
defaults, not a real secret — DVWA ships with them baked in specifically
so this kind of automation is possible without extra configuration.
"""

import re

import httpx

_USERNAME = "admin"
_PASSWORD = "password"
_TOKEN_RE = re.compile(r"name=['\"]user_token['\"] value=['\"]([a-f0-9]+)['\"]")


class DvwaAuthError(Exception):
    """Raised when login or setting the security level fails."""


def _extract_token(html: str) -> str:
    match = _TOKEN_RE.search(html)
    if match is None:
        raise DvwaAuthError("could not find a user_token in the DVWA response")
    return match.group(1)


def get_authenticated_cookie(target: str, port: int = 80, scheme: str = "http") -> str:
    """Logs into DVWA and sets its security level to "low".

    Returns the resulting `Cookie` header value (e.g.
    `"security=low; PHPSESSID=..."`), ready to pass to a scanning tool.
    """
    base_url = f"{scheme}://{target}:{port}"
    with httpx.Client(base_url=base_url, timeout=15.0) as client:
        login_page = client.get("/login.php")
        token = _extract_token(login_page.text)

        login_response = client.post(
            "/login.php",
            data={
                "username": _USERNAME,
                "password": _PASSWORD,
                "Login": "Login",
                "user_token": token,
            },
        )
        if login_response.status_code >= 400:
            raise DvwaAuthError(f"login failed with status {login_response.status_code}")

        security_page = client.get("/security.php")
        token = _extract_token(security_page.text)

        security_response = client.post(
            "/security.php",
            data={"security": "low", "seclev_submit": "Submit", "user_token": token},
        )
        if security_response.status_code >= 400:
            raise DvwaAuthError(
                f"setting security level failed with status {security_response.status_code}"
            )

        cookies = dict(client.cookies)
        if not cookies:
            raise DvwaAuthError("no session cookie was set after login")
        return "; ".join(f"{name}={value}" for name, value in cookies.items())
