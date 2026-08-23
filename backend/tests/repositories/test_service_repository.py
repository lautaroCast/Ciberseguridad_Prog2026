"""service_repository.get_or_create_service: the fast SELECT path is
covered indirectly via test_scan_task_service.py's
test_ingest_twice_refines_existing_service_row_instead_of_duplicating.
This file covers the insert-then-IntegrityError fallback directly,
including the case /code-review found: a conflict that is *not* the
(scan_id, host, port, protocol) unique-constraint race must not be
swallowed into a confusing NoResultFound.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories import service_repository


def test_get_or_create_service_truncates_host_and_protocol(db_session):
    # SQLite (this fixture) doesn't enforce the scans.id FK, so a bogus
    # scan_id is fine here — only host/protocol truncation is under test.
    scan_id = uuid.uuid4()
    long_host = "h" * 300
    long_protocol = "p" * 20

    service = service_repository.get_or_create_service(
        db_session,
        scan_id=scan_id,
        host=long_host,
        port=80,
        protocol=long_protocol,
        service_name=None,
        product=None,
        version=None,
    )

    assert service.host == long_host[:255]
    assert service.protocol == long_protocol[:10]


def test_get_or_create_service_refines_existing_row_when_host_was_already_truncated(db_session):
    scan_id = uuid.uuid4()
    long_host = "h" * 300

    first = service_repository.get_or_create_service(
        db_session,
        scan_id=scan_id,
        host=long_host,
        port=80,
        protocol="tcp",
        service_name=None,
        product=None,
        version=None,
    )

    # A second run reporting the same (untruncated) long host must match
    # the already-truncated row rather than failing to find it (which
    # would happen if truncation only applied at insert time, not before
    # the lookup SELECT).
    second = service_repository.get_or_create_service(
        db_session,
        scan_id=scan_id,
        host=long_host,
        port=80,
        protocol="tcp",
        service_name="http",
        product=None,
        version=None,
    )

    assert second.id == first.id
    assert second.service_name == "http"


@pytest.mark.postgres
def test_get_or_create_service_reraises_integrity_error_when_not_the_expected_race(
    postgres_session,
):
    # No scan (and therefore no target) exists for this scan_id — SQLite's
    # in-memory tests don't enforce foreign keys at all, so this specific
    # failure mode (a real Postgres FK violation, not the unique-constraint
    # race the except block is written to expect) is invisible to them;
    # only a real Postgres connection can reproduce it.
    bogus_scan_id = uuid.uuid4()

    with pytest.raises(IntegrityError):
        service_repository.get_or_create_service(
            postgres_session,
            scan_id=bogus_scan_id,
            host="dvwa",
            port=80,
            protocol="tcp",
            service_name="http",
            product=None,
            version=None,
        )
