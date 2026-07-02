"""Read-only accessors for `findings` — no business rules beyond scan scoping."""

import uuid

from sqlalchemy.orm import Session

from app.repositories import finding_repository
from app.services.scan_service import get_scan_or_raise
from models import Finding


def list_findings_for_scan(db: Session, scan_id: uuid.UUID) -> list[Finding]:
    get_scan_or_raise(db, scan_id)  # 404s for an unknown scan instead of silently returning []
    return finding_repository.list_findings_for_scan(db, scan_id)
