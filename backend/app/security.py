"""API-key auth for user-facing routers.

A single shared secret (`BACKEND_API_KEY`), not per-user credentials — see
`docs/security.md` for what this does and doesn't protect against. `/health`
is deliberately left unprotected so Docker's healthcheck needs no
credential.
"""

import secrets

from fastapi import Header, HTTPException

from app.config import get_settings


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_api_key is None or not secrets.compare_digest(x_api_key, settings.backend_api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
