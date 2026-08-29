"""Persistence layer for `Target` — plain SQLAlchemy queries, no business rules.

Whitelist enforcement and other invariants live in
app/services/target_service.py; this module only knows how to talk to the
database.
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models import TERMINAL_SCAN_STATUSES, Scan, Target


def list_targets(
    db: Session, *, is_active: bool | None = None, limit: int | None = None, offset: int = 0
) -> list[Target]:
    stmt = select(Target).order_by(Target.created_at.desc())
    if is_active is not None:
        stmt = stmt.where(Target.is_active == is_active)
    stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
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
    # db.refresh() re-hydrates the object that db.commit() just expired
    # (SQLAlchemy's default expire_on_commit=True). Without it, the
    # response_model serialization in the router — which reads target.id /
    # target.created_at after get_db()'s session may already be closing —
    # would either hit a surprise extra SELECT or a DetachedInstanceError.
    # Looks redundant but isn't, given the current session lifecycle.
    db.refresh(target)
    return target


def update_target(db: Session, target: Target, updates: dict) -> Target:
    # `updates` is expected to come from TargetUpdate.model_dump(exclude_unset=True)
    # (see app/routers/targets.py), so its keys are already constrained to
    # that schema's fields — this trusts that boundary rather than
    # re-validating field names here.
    if not updates:
        return target
    for field, value in updates.items():
        setattr(target, field, value)
    db.commit()
    db.refresh(target)
    return target


def delete_target(db: Session, target_id: uuid.UUID) -> bool:
    """Atomically deletes a target only if it has no non-terminal scan.

    7th independent evaluation: this used to take the already-fetched ORM
    `Target` and unconditionally `db.delete()` it, with the "does it have
    an active scan" check done in Python by the caller
    (app/services/target_service.py) beforehand — not atomic with this
    delete, so a scan created in the gap between that check and this call
    would still get destroyed by the cascade. Same "let a single
    conditional statement be the source of truth" idea already used for
    `scan_repository.complete_scan`'s conditional UPDATE, adapted to a
    DELETE: the condition here is a NOT EXISTS subquery (targets has no
    column of its own that reflects "has an active scan") instead of a
    WHERE on the row's own columns.

    Returns False if no row matched — the target doesn't exist, or it has
    a non-terminal scan — so the caller can tell those apart from its own
    prior GET-based existence check and raise the correct domain error
    either way.
    """
    has_active_scan = (
        select(Scan.id)
        .where(Scan.target_id == target_id, Scan.status.not_in(TERMINAL_SCAN_STATUSES))
        .exists()
    )
    stmt = delete(Target).where(Target.id == target_id, ~has_active_scan)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount > 0
