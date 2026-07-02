"""Service: a network service (host:port/protocol) discovered during a Scan."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .finding import Finding
    from .scan import Scan


class Service(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A host:port/protocol tuple discovered by reconnaissance (Nmap)."""

    __tablename__ = "services"
    __table_args__ = (
        UniqueConstraint("scan_id", "host", "port", "protocol", name="uq_services_scan_endpoint"),
    )

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[str] = mapped_column(String(10), nullable=False, default="tcp")
    service_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    banner: Mapped[str | None] = mapped_column(Text, nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="services")
    findings: Mapped[list["Finding"]] = relationship(back_populates="service")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Service(id={self.id!s}, host={self.host!r}, port={self.port!r})"
