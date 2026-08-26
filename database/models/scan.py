"""Scan: a single pipeline execution against a target."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, text
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
    __table_args__ = (
        Index("ix_scans_target_id", "target_id"),
        # 8th independent evaluation: create_scan/trigger_pipeline only
        # checked Target.is_active, never whether the target already had a
        # non-terminal scan - two concurrent triggers could run two scans at
        # once against the same host, and against dvwa specifically
        # scanner/app/services/dvwa_auth.py's get_authenticated_cookie
        # mutates shared server-side session state a second concurrent scan
        # would also be mutating mid-run. Same idiom already used for
        # targets.name (a DB-level uniqueness guard, with the Python-level
        # check in the service layer as an optimistic fast path only) -
        # here the uniqueness is conditional on status, hence a partial
        # index rather than a plain unique constraint.
        Index(
            "ix_scans_one_active_per_target",
            "target_id",
            unique=True,
            # No explicit ::scan_status cast on the literals: Postgres
            # infers the enum type from the column context and implicitly
            # casts a bare string literal to it, which is what makes this
            # portable across postgres_session's per-test isolated schema
            # (schema_translate_map) - an explicit `'COMPLETED'::scan_status`
            # instead resolves the type name via search_path, which binds
            # to the wrong schema's copy of the enum there. Casting the
            # column to text (`status::text NOT IN (...)`) was tried too
            # and rejected outright: Postgres' enum->text cast isn't marked
            # IMMUTABLE, which index predicates require.
            # Both dialects store the Python member *name* (uppercase -
            # "COMPLETED"), not ScanStatus.COMPLETED.value ("completed") -
            # confirmed against a real Postgres via \dT+ scan_status.
            postgresql_where=text("status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')"),
            sqlite_where=text("status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')"),
        ),
    )

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
