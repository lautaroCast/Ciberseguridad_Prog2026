"""Finding: a single normalized vulnerability/misconfiguration record."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .enums import SeverityLevel

if TYPE_CHECKING:
    from .cve_reference import CveReference
    from .scan import Scan
    from .scan_task import ScanTask
    from .service import Service


class Finding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A normalized hallazgo produced from a `ScanTask`'s raw output.

    Every adapter in the Scanner Service (Nmap, Nuclei, Nikto, WhatWeb,
    ZAP) outputs tool-specific data; the normalization layer (Módulo 5)
    maps all of it into this single shape so severity, reporting and the
    dashboard never need to know which tool produced a finding.

    `finding_type` is a free string (not an enum) for the same
    extensibility reason as `ScanTask.tool_name`: new categories should
    not require a migration.
    """

    __tablename__ = "findings"
    __table_args__ = (
        Index("ix_findings_scan_id_severity", "scan_id", "severity"),
    )

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    scan_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scan_tasks.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding_type: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)

    cvss_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    cvss_vector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[SeverityLevel] = mapped_column(
        Enum(SeverityLevel, name="severity_level", native_enum=True),
        nullable=False,
        default=SeverityLevel.INFO,
    )

    scan: Mapped["Scan"] = relationship(back_populates="findings")
    scan_task: Mapped["ScanTask"] = relationship(back_populates="findings")
    service: Mapped["Service | None"] = relationship(back_populates="findings")
    cve_references: Mapped[list["CveReference"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Finding(id={self.id!s}, title={self.title!r}, severity={self.severity!s})"
