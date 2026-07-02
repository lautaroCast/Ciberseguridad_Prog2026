"""Scan: a single pipeline execution against a target."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .enums import ScanStatus

if TYPE_CHECKING:
    from .finding import Finding
    from .report import Report
    from .scan_task import ScanTask
    from .service import Service
    from .target import Target
    from .technology import Technology


class Scan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One run of the 12-stage n8n pipeline against a `Target`.

    `pipeline_run_id` correlates this row with the n8n execution that
    drives it (Módulo 6), so the workflow can be traced back from the DB
    and vice versa.
    """

    __tablename__ = "scans"

    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, name="scan_status", native_enum=True),
        nullable=False,
        default=ScanStatus.PENDING,
    )
    pipeline_run_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    target: Mapped["Target"] = relationship(back_populates="scans")
    scan_tasks: Mapped[list["ScanTask"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )
    services: Mapped[list["Service"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )
    technologies: Mapped[list["Technology"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Scan(id={self.id!s}, target_id={self.target_id!s}, status={self.status!s})"
