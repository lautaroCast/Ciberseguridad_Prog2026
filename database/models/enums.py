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


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
