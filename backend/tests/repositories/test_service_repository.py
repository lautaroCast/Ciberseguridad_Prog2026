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
