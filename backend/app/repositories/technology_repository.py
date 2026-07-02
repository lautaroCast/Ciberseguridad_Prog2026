"""Persistence layer for `Technology` — plain insert, no dedup.

Unlike `services`, `technologies` has no unique constraint to upsert on:
the same technology name detected differently across runs (e.g. a version
string appearing on a later scan) is kept as separate historical rows
rather than overwritten, consistent with `Scan` being an append-only
execution record.
"""

import uuid

from sqlalchemy.orm import Session

from models import Technology


def create_technology(
    db: Session,
    *,
    scan_id: uuid.UUID,
    name: str,
    detected_by: str,
    version: str | None,
    category: str | None,
    confidence: str | None,
) -> Technology:
    technology = Technology(
        scan_id=scan_id,
        name=name,
        detected_by=detected_by,
        version=version,
        category=category,
        confidence=confidence,
    )
    db.add(technology)
    db.flush()
    return technology
