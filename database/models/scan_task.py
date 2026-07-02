"""ScanTask: execution of a single tool (Nmap, Nuclei, ...) within a Scan."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .enums import ScanTaskStatus

if TYPE_CHECKING:
    from .finding import Finding
    from .scan import Scan


class ScanTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One tool invocation (e.g. `nmap`, `nuclei`) belonging to a `Scan`.

    `tool_name` is a plain string, not an enum: the Scanner Service
    (Módulo 4) adds new adapters as plugins, and requiring a migration to
    register a new tool name would violate the "extensible without
    redesign" principle from the architecture doc.
    """

    __tablename__ = "scan_tasks"
    __table_args__ = (Index("ix_scan_tasks_scan_id_tool_name", "scan_id", "tool_name"),)

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[ScanTaskStatus] = mapped_column(
        Enum(ScanTaskStatus, name="scan_task_status", native_enum=True),
        nullable=False,
        default=ScanTaskStatus.PENDING,
    )
    command: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_output_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="scan_tasks")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="scan_task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"ScanTask(id={self.id!s}, tool_name={self.tool_name!r}, status={self.status!s})"
