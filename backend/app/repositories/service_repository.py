"""Persistence layer for `Service`.

`get_or_create_service` upserts on the table's own unique constraint
(`scan_id`, `host`, `port`, `protocol` — see database/models/service.py)
instead of blindly inserting: Nmap can be re-run within the same scan
(e.g. a targeted re-scan of specific ports after the initial sweep), and
each run should refine the existing row rather than duplicate it.

Optimistic-SELECT fast path, insert-first fallback: the initial SELECT is
not the source of truth (it's a plain check-then-act, same caveat
`target_service.py::register_target` documents for its own pre-check) —
it exists only to skip the SAVEPOINT+INSERT round trip entirely for the
common case where the row already exists (e.g. re-running a tool within
the same scan, or a duplicate host/port reported twice in one sweep).
When the SELECT misses, the INSERT attempt is wrapped in its own SAVEPOINT
(`db.begin_nested()`) so a conflict only unwinds this one insert, not
whatever outer transaction the caller (`scan_task_service.ingest_scan_task`)
already has open, and the table's own unique constraint on
(scan_id, host, port, protocol) — not this function — remains the actual
source of truth for "does this row already exist."
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Service

# Tool-derived strings (Nmap's own service/product/version guesses) have no
# length guarantee, but these three columns are all String(100)
# (database/models/service.py) — truncate here, once, rather than trusting
# every caller (currently only nmap_normalizer.py) to do it themselves.
_MAX_LENGTH = 100


def _truncate(value: str | None) -> str | None:
    return value[:_MAX_LENGTH] if value is not None else None


def _refine(
    existing: Service, *, service_name: str | None, product: str | None, version: str | None
) -> Service:
    """Merge newer field values into an already-persisted row.

    Shared by the fast SELECT-hit path and the insert-conflict fallback below
    so the two can't quietly drift apart on what "refine" means.
    """
    existing.service_name = service_name or existing.service_name
    existing.product = product or existing.product
    existing.version = version or existing.version
    return existing


def get_or_create_service(
    db: Session,
    *,
    scan_id: uuid.UUID,
    host: str,
    port: int,
    protocol: str,
    service_name: str | None,
    product: str | None,
    version: str | None,
) -> Service:
    service_name = _truncate(service_name)
    product = _truncate(product)
    version = _truncate(version)

    stmt = select(Service).where(
        Service.scan_id == scan_id,
        Service.host == host,
        Service.port == port,
        Service.protocol == protocol,
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing is not None:
        _refine(existing, service_name=service_name, product=product, version=version)
        db.flush()
        return existing

    try:
        with db.begin_nested():
            service = Service(
                scan_id=scan_id,
                host=host,
                port=port,
                protocol=protocol,
                service_name=service_name,
                product=product,
                version=version,
            )
            db.add(service)
            db.flush()
    except IntegrityError:
        # Someone else (or an earlier tool run within the same scan) won
        # the race — the SAVEPOINT above already rolled back our attempted
        # insert, the outer transaction is untouched. Fall back to the
        # update path.
        existing = db.execute(stmt).scalar_one_or_none()
        if existing is None:
            # Not actually the (scan_id, host, port, protocol) race after
            # all — e.g. scan_id's own FK is gone because the scan/target
            # was deleted mid-flight. Let the real IntegrityError surface
            # instead of masking it behind an unrelated NoResultFound from
            # a SELECT that was never going to find anything.
            raise
        _refine(existing, service_name=service_name, product=product, version=version)
        db.flush()
        return existing

    return service
