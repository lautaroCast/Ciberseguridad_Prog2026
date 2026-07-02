"""Tool-agnostic intermediate shapes produced by a normalizer.

A normalizer's only job is: given a tool's already-parsed output (the
`parsed` field of the Scanner Service's `RawScanResult`), produce these
plain dataclasses. `app/services/scan_task_service.py` is the only place
that turns them into `Service` / `Technology` / `Finding` / `CveReference`
ORM rows, which keeps normalizers trivially unit-testable and free of any
DB/session concerns.
"""

from dataclasses import dataclass, field

from models import SeverityLevel


@dataclass
class ServiceData:
    host: str
    port: int
    protocol: str = "tcp"
    service_name: str | None = None
    product: str | None = None
    version: str | None = None


@dataclass
class TechnologyData:
    name: str
    detected_by: str
    version: str | None = None
    category: str | None = None
    confidence: str | None = None


@dataclass
class CveReferenceData:
    cve_id: str
    cvss_score: float | None = None
    cvss_vector: str | None = None
    description: str | None = None
    source_url: str | None = None


@dataclass
class FindingData:
    title: str
    finding_type: str
    severity: SeverityLevel
    description: str | None = None
    evidence: str | None = None
    confidence: str | None = None
    cvss_score: float | None = None
    cvss_vector: str | None = None
    cve_references: list[CveReferenceData] = field(default_factory=list)


@dataclass
class NormalizedData:
    services: list[ServiceData] = field(default_factory=list)
    technologies: list[TechnologyData] = field(default_factory=list)
    findings: list[FindingData] = field(default_factory=list)
