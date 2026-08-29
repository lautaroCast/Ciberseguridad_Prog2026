"""Pydantic schemas for the `reports` resource."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models import ReportFormat


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scan_id: uuid.UUID
    format: ReportFormat
    file_path: str
    generated_at: datetime
    generated_by: str | None
