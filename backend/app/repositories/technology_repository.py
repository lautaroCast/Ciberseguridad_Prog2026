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

# Tool-derived strings have no length guarantee; these columns are bounded
# (database/models/technology.py) — truncate here, once, same pattern as
# service_repository.py/finding_repository.py use for their own tool-derived
# fields, rather than leaving this the one repository that doesn't.
_NAME_MAX = 100
_DETECTED_BY_MAX = 50
_VERSION_MAX = 100
_CATEGORY_MAX = 100
_CONFIDENCE_MAX = 20


def _truncate(value: str | None, max_length: int) -> str | None:
    return value[:max_length] if value is not None else None


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
        name=name[:_NAME_MAX],
        detected_by=detected_by[:_DETECTED_BY_MAX],
        version=_truncate(version, _VERSION_MAX),
        category=_truncate(category, _CATEGORY_MAX),
        confidence=_truncate(confidence, _CONFIDENCE_MAX),
    )
    db.add(technology)
    db.flush()
    return technology
