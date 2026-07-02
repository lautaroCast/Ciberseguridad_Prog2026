"""Persistence layer for `Target` — plain SQLAlchemy queries, no business rules.

Whitelist enforcement and other invariants live in
app/services/target_service.py; this module only knows how to talk to the
database.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Target


def list_targets(db: Session, *, is_active: bool | None = None) -> list[Target]:
    stmt = select(Target).order_by(Target.created_at.desc())
    if is_active is not None:
        stmt = stmt.where(Target.is_active == is_active)
    return list(db.execute(stmt).scalars().all())


def get_target(db: Session, target_id: uuid.UUID) -> Target | None:
    return db.get(Target, target_id)


def get_target_by_name(db: Session, name: str) -> Target | None:
    stmt = select(Target).where(Target.name == name)
    return db.execute(stmt).scalar_one_or_none()


def create_target(db: Session, *, name: str, host: str, description: str | None) -> Target:
    target = Target(name=name, host=host, description=description, is_lab_target=True)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def update_target(
    db: Session, target: Target, *, description: str | None, is_active: bool | None
) -> Target:
    if description is not None:
        target.description = description
    if is_active is not None:
        target.is_active = is_active
    db.commit()
    db.refresh(target)
    return target


def delete_target(db: Session, target: Target) -> None:
    db.delete(target)
    db.commit()
