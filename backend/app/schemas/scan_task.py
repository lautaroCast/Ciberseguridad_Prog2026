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
    command: str
    status: Literal["completed", "failed"]
    started_at: datetime
    finished_at: datetime
    raw_output: str
    parsed: Any | None = None
    error_message: str | None = None


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
