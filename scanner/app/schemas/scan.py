"""Request/response schemas for the scan endpoint.

`RawScanResult`'s field names deliberately mirror the `scan_tasks` table
(database/models/scan_task.py) from Módulo 1: `tool_name` -> `tool`,
`command`, `raw_output`, `status`, `started_at`/`finished_at`,
`error_message`. Módulo 5's normalization layer maps this response almost
1:1 into that table plus a `findings` row per item in `parsed`.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator



# The `options` keys that flow, largely unvalidated until now, straight into
# a subprocess argv token by some adapter's `build_command` (nmap: `ports`,
# nuclei: `severity`/`tags`, nikto: `max_time`, whatweb: `aggression` — see
# each adapter module). Same injection class `target` guards against below:
# a value starting with "-" gets parsed by the underlying tool as a CLI flag
# instead of the value it's supposed to be.
_OPTION_KEYS_TO_GUARD = ("ports", "severity", "tags", "max_time", "aggression")


def _reject_if_looks_like_a_flag(label: str, value: Any) -> None:
    # Shared by both `target` and `options`' guarded keys so the two can't
    # drift apart (e.g. one getting refined to also reject a bare "-" or
    # "--" while the other doesn't).
    if str(value).startswith("-"):
        raise ValueError(f"{label} must not start with '-' (would be interpreted as a CLI flag)")


class ScanRequest(BaseModel):
    target: str = Field(min_length=1, max_length=255, description="Hostname resolvable on lab-network, e.g. 'juice-shop'.")
    port: int = Field(default=80, ge=1, le=65535)

    @field_validator("target")
    @classmethod
    def _target_must_not_look_like_a_flag(cls, value: str) -> str:
        # NmapAdapter appends `target` as a bare, standalone argv token (the
        # other adapters embed it inside a "scheme://target:port" string,
        # where a leading "-" is inert). A target starting with "-" would be
        # parsed by nmap as a CLI flag instead of a hostname — reject it here
        # so every adapter is covered by a single check, not just nmap's own.
        _reject_if_looks_like_a_flag("target", value)
        return value
    scheme: Literal["http", "https"] = "http"
    # Adapter-specific knobs (e.g. nuclei's `severity`, nikto's `max_time`).
    # Each adapter documents which keys it understands; unknown keys are
    # ignored rather than rejected, so callers can pass a shared options
    # dict across tools without per-tool branching.
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("options")
    @classmethod
    def _known_option_values_must_not_look_like_flags(cls, value: dict[str, Any]) -> dict[str, Any]:
        for key in _OPTION_KEYS_TO_GUARD:
            if key in value:
                _reject_if_looks_like_a_flag(f"options.{key}", value[key])
        return value
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
