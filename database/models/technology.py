"""Technology: a piece of tech stack fingerprinted during a Scan."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .scan import Scan


class Technology(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A detected technology (framework, CMS, server, library, ...).

    Feeds the pipeline's "selección inteligente de herramientas" stage:
    the tool-selection step (Módulo 6) reads these rows to decide which
    scanners are worth running against the target.
    """

    __tablename__ = "technologies"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detected_by: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="technologies")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Technology(id={self.id!s}, name={self.name!r}, version={self.version!r})"
