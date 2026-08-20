"""Persistence layer for `Service`.

`get_or_create_service` upserts on the table's own unique constraint
(`scan_id`, `host`, `port`, `protocol` — see database/models/service.py)
instead of blindly inserting: Nmap can be re-run within the same scan
(e.g. a targeted re-scan of specific ports after the initial sweep), and
each run should refine the existing row rather than duplicate it.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Service

# Tool-derived strings (Nmap's own service/product/version guesses) have no
# length guarantee, but these three columns are all String(100)
# (database/models/service.py) — truncate here, once, rather than trusting
# every caller (currently only nmap_normalizer.py) to do it themselves.
_MAX_LENGTH = 100


def _truncate(value: str | None) -> str | None:
    return value[:_MAX_LENGTH] if value is not None else None


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
        existing.service_name = service_name or existing.service_name
        existing.product = product or existing.product
        existing.version = version or existing.version
        db.flush()
        return existing

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
    return service
