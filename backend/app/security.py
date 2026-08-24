"""API-key auth for user-facing routers, plus a separate tier for n8n's
own callback routes.

Two shared secrets, not per-user credentials — see `docs/security.md`
for what this does and doesn't protect against. `/health` is deliberately
left unprotected so Docker's healthcheck needs no credential.

`BACKEND_API_KEY` (`verify_api_key`) gates everything the Frontend calls:
target management, scan creation/reads, reports. `N8N_CALLBACK_API_KEY`
(`verify_n8n_callback_key`) gates only the two routes n8n itself calls
back into (`POST /scans/{id}/tasks`, `POST /scans/{id}/complete`) — the
Frontend never needs and is never given this second key, so holding it
doesn't let a Frontend-side caller forge scan-task ingestion or force a
scan to complete. Same two-tier shape the Scanner Service already uses
(`INTERNAL_API_KEY`/`X-Internal-Token`, `scanner/app/security.py`).
"""

import secrets

from fastapi import Header, HTTPException

from app.config import get_settings


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_api_key is None or not secrets.compare_digest(x_api_key, settings.backend_api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def verify_n8n_callback_key(x_n8n_callback_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_n8n_callback_key is None or not secrets.compare_digest(
        x_n8n_callback_key, settings.n8n_callback_api_key
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing n8n callback key.")
