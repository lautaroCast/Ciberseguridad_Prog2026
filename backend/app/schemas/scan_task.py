"""Pydantic schemas for the `scan_tasks` resource and its ingest endpoint.

`ScanTaskIngest`'s fields mirror the Scanner Service's `RawScanResult`
(scanner/app/schemas/scan.py) on purpose: n8n (Módulo 6) forwards that
response's body here almost unchanged once the pipeline decides a
scan_task is done, so there is no reshaping step between the two services.
"""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ScanTaskIngest(BaseModel):
    tool: str = Field(min_length=1, max_length=50)
    command: str = Field(max_length=2000)
    status: Literal["completed", "failed"]
    started_at: datetime
    finished_at: datetime
    # `command`/`error_message` map to unbounded `Text` columns DB-side, so
    # these caps aren't mirroring a column width like every other
    # `max_length` in this file does (see module docstring) — they're a
    # deliberate, otherwise-arbitrary ceiling against storage exhaustion
    # via this endpoint (COD-16), since nothing else in front of it
    # (no rate limiting — see docs/security.md) bounds request volume.
    # Kept generous (50MB, not e.g. 5MB) on purpose: `Ingest: *` nodes in
    # the n8n pipeline all run with `continueOnFail: true`, so a 422 here
    # doesn't surface as a visible pipeline error — it just silently ships
    # a report with that tool's findings missing. A tight cap trades a
    # DoS mitigation for a much more likely silent-data-loss footgun on a
    # legitimately verbose scan (e.g. ZAP against a target with many
    # alert instances); 50MB is chosen to make that collision practically
    # unreachable for real tool output while still bounding pathological
    # input.
    raw_output: str = Field(max_length=50_000_000)
    parsed: Any | None = None
    error_message: str | None = Field(default=None, max_length=5000)


class ScanTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scan_id: uuid.UUID
    tool_name: str
    status: str
    command: str | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime


class ScanTaskIngestResult(BaseModel):
    """Response for `POST /scans/{scan_id}/tasks`.

    Separate from `ScanTaskRead` because the ingest endpoint's caller
    (n8n, eventually) needs to know how much normalization actually
    happened — e.g. to decide whether a scan_task with zero findings was
    genuinely clean or silently failed to normalize.
    """

    scan_task: ScanTaskRead
    services_upserted: int
    technologies_created: int
    findings_created: int
