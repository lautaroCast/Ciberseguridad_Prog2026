"""CveReference: a CVE linked to a Finding (0..N per finding)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .finding import Finding


class CveReference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A CVE identifier associated with a `Finding`.

    Split out of `Finding` (rather than a single `cve_id` column) because
    tools like Nuclei/ZAP can report more than one CVE for a single
    finding, and because CVE metadata (score, vector, description) is
    naturally reusable/lookup-able independent of the finding that
    surfaced it.
    """

    __tablename__ = "cve_references"
    __table_args__ = (Index("ix_cve_references_cve_id", "cve_id"),)

    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False
    )
    cve_id: Mapped[str] = mapped_column(String(20), nullable=False)
    cvss_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    cvss_vector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    finding: Mapped["Finding"] = relationship(back_populates="cve_references")

    def __repr__(self) -> str:  # pragma: no cover
        return f"CveReference(id={self.id!s}, cve_id={self.cve_id!r})"
