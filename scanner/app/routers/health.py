"""Liveness endpoint used by docker-compose's healthcheck.

No DB dependency here (unlike the Backend's /health) — the Scanner Service
is stateless, so "alive" just means the process is serving requests.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
