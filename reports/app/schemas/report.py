"""Request/response schemas for the report-generation endpoint.

This service is stateless and knows nothing about the Backend's schema or
database — the caller (the Backend, see `report_service.py` there) gathers
everything a report needs and pushes it here in one self-contained
request. Field names deliberately mirror the Backend's `TargetRead` /
`ScanRead` / `FindingRead` schemas so building this payload there is a
close-to-direct `model_dump()`, not a reshaping exercise.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class TargetInfo(BaseModel):
    id: str
    name: str
    host: str
    description: str | None = None


class ScanInfo(BaseModel):
    id: str
    status: str
    triggered_by: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    # 7th independent evaluation: the Backend's ScanRead already carries
    # error_message (which n8n threads a tool_failure_summary into even on
    # an otherwise "completed" scan, since round 6) - but this schema had
    # no matching field, so Pydantic silently dropped it and no template
    # ever rendered it. The pipeline could compute which tool failed, but
    # that information was architecturally incapable of reaching the
    # actual report artifact an operator reads.
    error_message: str | None = None


class CveReferenceInfo(BaseModel):
    cve_id: str
    cvss_score: Decimal | None = None
    cvss_vector: str | None = None
    description: str | None = None
    source_url: str | None = None


class FindingInfo(BaseModel):
    id: str
    title: str
    description: str | None = None
    finding_type: str
    evidence: str | None = None
    confidence: str | None = None
    cvss_score: Decimal | None = None
    cvss_vector: str | None = None
    severity: str
    created_at: datetime
    cve_references: list[CveReferenceInfo] = []


class ReportRequest(BaseModel):
    format: Literal["pdf", "html", "markdown", "json"]
    target: TargetInfo
    scan: ScanInfo
    findings: list[FindingInfo]


class ReportResult(BaseModel):
    format: str
    filename: str
    generated_at: datetime
