"""Target: a system registered for scanning within the local lab."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .scan import Scan


class Target(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A host/application registered for analysis.

    `is_lab_target` marks rows seeded as part of the local lab (Juice Shop,
    DVWA, ...). The backend (Módulo 3) enforces that only lab targets can be
    scanned; this column is what that whitelist check reads.
    """

    __tablename__ = "targets"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_lab_target: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    scans: Mapped[list["Scan"]] = relationship(
        back_populates="target", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Target(id={self.id!s}, name={self.name!r}, host={self.host!r})"
