"""Service-to-service auth — only the Backend calls this router.

Distinct header/secret from the Backend's user-facing X-API-Key (see
`docs/security.md`): this one never leaves `app-network`, and the port
this service listens on is no longer published to the host (Módulo 9).
`/health` is deliberately left unprotected so Docker's healthcheck needs no
credential.
"""

import secrets

from fastapi import Header, HTTPException

from app.config import get_settings


def verify_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_internal_token is None or not secrets.compare_digest(
        x_internal_token, settings.internal_api_key
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing internal token.")
