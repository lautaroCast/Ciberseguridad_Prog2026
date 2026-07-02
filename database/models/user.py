"""User: placeholder schema for a future multi-user authentication layer.

Not consumed by any service yet (the platform currently runs unauthenticated,
single-operator, local-only). Modeled now so the pipeline's "Notificación"
stage and a future auth module can be added without another migration
touching unrelated tables.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Enum, String

from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .enums import UserRole


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        nullable=False,
        default=UserRole.ANALYST,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"User(id={self.id!s}, email={self.email!r}, role={self.role!s})"
