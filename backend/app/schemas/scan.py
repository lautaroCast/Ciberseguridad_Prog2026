"""Pydantic schemas for the `scans` resource."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ScanCreate(BaseModel):
    triggered_by: str | None = Field(default=None, max_length=100)


class ScanComplete(BaseModel):
    status: Literal["completed", "failed"]
    error_message: str | None = None


class ScanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_id: uuid.UUID
    status: str
    pipeline_run_id: str | None
    triggered_by: str | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime
