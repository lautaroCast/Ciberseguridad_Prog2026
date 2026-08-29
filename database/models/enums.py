"""Enumerations backed by native PostgreSQL enum types.

Kept separate from free-text columns (e.g. `tool_name`, `finding_type`)
which are intentionally plain strings so new scanners/finding categories
can be introduced without a schema migration. Enums are reserved for
closed, small vocabularies where an invalid value would be a bug.
"""

import enum


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Single source of truth for "does this status mean the scan is done".
# Lives next to the enum it classifies so every caller that needs it
# (scan_service, pipeline_service, target_service) imports the same
# object instead of each defining its own copy that could silently drift.
TERMINAL_SCAN_STATUSES: frozenset[ScanStatus] = frozenset(
    {ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED}
)


class ScanTaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SeverityLevel(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
