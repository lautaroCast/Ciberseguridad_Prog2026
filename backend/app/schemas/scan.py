"""Pydantic schemas for the `scans` resource."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from models import ScanStatus


class ScanCreate(BaseModel):
    triggered_by: str | None = Field(default=None, max_length=100)


class ScanComplete(BaseModel):
    status: Literal["completed", "failed"]
    error_message: str | None = None
    # Sent by n8n as `$execution.id` (Complete Scan / Mark Scan Failed
    # nodes) — the only point in the pipeline that actually knows its own
    # n8n execution id. Optional so older callers (or a manual complete
    # during local testing) don't need to supply it.
    pipeline_run_id: str | None = Field(default=None, max_length=100)


class ScanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_id: uuid.UUID
    status: ScanStatus
    pipeline_run_id: str | None
    triggered_by: str | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime
