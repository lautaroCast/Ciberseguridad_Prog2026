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
