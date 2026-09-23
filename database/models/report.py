"""Report: metadata for a generated report artifact."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin
from .enums import ReportFormat

if TYPE_CHECKING:
    from .scan import Scan


class Report(UUIDPrimaryKeyMixin, Base):
    """A generated report artifact (PDF/HTML/Markdown/JSON) for a `Scan`.

    Stores only the file path and metadata; the actual bytes live on the
    `reports-data` volume, written by the Reports Service (Módulo 7).
    """

    __tablename__ = "reports"
    # Unique (not just indexed) as of the Ronda L migration
    # (unique_report_per_scan_format): Generate Report's own retryOnFail
    # (n8n) can re-send the same POST /scans/{id}/reports after a slow/
    # lost response from a first attempt that already committed - without
    # this, the retry duplicates a Report row for the same (scan, format).
    # report_service.generate_report catches the resulting IntegrityError
    # and returns the existing row, same idiom as
    # ix_scan_tasks_scan_id_tool_name for the identical class of problem.
    __table_args__ = (Index("ix_reports_scan_id_format", "scan_id", "format", unique=True),)

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, name="report_format", native_enum=True), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    generated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="reports")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Report(id={self.id!s}, scan_id={self.scan_id!s}, format={self.format!s})"
