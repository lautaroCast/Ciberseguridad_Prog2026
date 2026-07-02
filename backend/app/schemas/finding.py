"""Pydantic schemas for reading normalized `findings` (+ their CVEs)."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CveReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cve_id: str
    cvss_score: Decimal | None
    cvss_vector: str | None
    description: str | None
    source_url: str | None


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scan_id: uuid.UUID
    scan_task_id: uuid.UUID
    service_id: uuid.UUID | None
    title: str
    description: str | None
    finding_type: str
    evidence: str | None
    confidence: str | None
    cvss_score: Decimal | None
    cvss_vector: str | None
    severity: str
    created_at: datetime
    cve_references: list[CveReferenceRead] = []
