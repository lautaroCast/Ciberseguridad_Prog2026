"""Request/response schemas for the scan endpoint.

`RawScanResult`'s field names deliberately mirror the `scan_tasks` table
(database/models/scan_task.py) from Módulo 1: `tool_name` -> `tool`,
`command`, `raw_output`, `status`, `started_at`/`finished_at`,
`error_message`. Módulo 5's normalization layer maps this response almost
1:1 into that table plus a `findings` row per item in `parsed`.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    target: str = Field(min_length=1, max_length=255, description="Hostname resolvable on lab-network, e.g. 'juice-shop'.")
    port: int = Field(default=80, ge=1, le=65535)
    scheme: Literal["http", "https"] = "http"
    # Adapter-specific knobs (e.g. nuclei's `severity`, nikto's `max_time`).
    # Each adapter documents which keys it understands; unknown keys are
    # ignored rather than rejected, so callers can pass a shared options
    # dict across tools without per-tool branching.
    options: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int | None = Field(
        default=None, ge=1, description="Capped at SCANNER_MAX_TIMEOUT_SECONDS regardless of what's requested here."
    )


class RawScanResult(BaseModel):
    tool: str
    target: str
    command: str
    status: Literal["completed", "failed"]
    started_at: datetime
    finished_at: datetime
    raw_output: str
    parsed: Any | None = None
    error_message: str | None = None
