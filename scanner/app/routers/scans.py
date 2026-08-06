"""Generic scan endpoint — dispatches to whichever adapter `tool_name` names.

Deliberately one route for every tool instead of one route per tool: adding
a new adapter to the registry makes it reachable here automatically, no
router change required.
"""

from app.adapters.registry import get_adapter, list_tools
from app.config import get_settings
from app.schemas.scan import RawScanResult, ScanRequest
from app.services import scan_runner
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["scans"])


@router.get("/tools")
def get_tools() -> list[str]:
    """Tool names currently registered — lets callers (e.g. the n8n
    tool-selection stage in Módulo 6) discover what's scannable without
    hardcoding a tool list."""
    return list_tools()


@router.post("/scan/{tool_name}", response_model=RawScanResult)
def run_scan(tool_name: str, payload: ScanRequest) -> RawScanResult:
    adapter = get_adapter(tool_name)
    settings = get_settings()
    # Second, independent enforcement point for the lab whitelist (the first
    # is the Backend, at target registration time). This is the one that
    # actually matters: the Scanner is the only component with a network
    # route to lab-network, so a check only in the Backend is not real
    # defense in depth — see docs/security.md.
    if payload.target not in settings.allowed_lab_hosts:
        raise HTTPException(status_code=422, detail="target is not an allowed lab host")
    requested_timeout = payload.timeout_seconds or settings.scanner_max_timeout_seconds
    timeout = min(requested_timeout, settings.scanner_max_timeout_seconds)
    return scan_runner.execute(
        adapter,
        target=payload.target,
        port=payload.port,
        scheme=payload.scheme,
        options=payload.options,
        timeout=timeout,
    )
