"""ORM schema for VulnScan Platform — single source of truth for the DB.

Import `Base` here (with every model already loaded) whenever Alembic or a
service needs the full mapped schema, e.g.:

    from database.models import Base
    Base.metadata.create_all(engine)  # tests only; production uses Alembic
"""

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .cve_reference import CveReference
from .enums import (
    TERMINAL_SCAN_STATUSES,
    ReportFormat,
    ScanStatus,
    ScanTaskStatus,
    SeverityLevel,
)
from .finding import Finding
from .report import Report
from .scan import Scan
from .scan_task import ScanTask
from .service import Service
from .target import Target
from .technology import Technology

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "CveReference",
    "Finding",
    "Report",
    "Scan",
    "ScanTask",
    "Service",
    "Target",
    "Technology",
    "ScanStatus",
    "ScanTaskStatus",
    "SeverityLevel",
    "ReportFormat",
    "TERMINAL_SCAN_STATUSES",
]
