"""Shared declarative base and mixins for all ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base shared by every model in the schema."""


class UUIDPrimaryKeyMixin:
    """Adds a server-generated UUID primary key.

    UUIDs (vs. serial ints) avoid leaking row counts through the API and
    let scan-producing services generate/reference IDs before the row is
    committed.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """Adds a `created_at` column populated by the database on insert."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
