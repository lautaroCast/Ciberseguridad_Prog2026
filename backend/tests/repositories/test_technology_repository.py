"""create_technology truncates tool-derived strings before insert — same
pattern service_repository.py/finding_repository.py apply, which this
repository had been missing entirely until now."""

import pytest

from app.repositories import technology_repository
from app.services import scan_service, target_service


def _make_scan(db_session):
    target = target_service.register_target(
        db_session, name="juice-shop-demo", host="juice-shop", description=None
    )
    return scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)


def test_create_technology_truncates_oversized_fields(db_session):
    scan = _make_scan(db_session)

    technology = technology_repository.create_technology(
        db_session,
        scan_id=scan.id,
        name="n" * 150,
        detected_by="d" * 80,
        version="v" * 150,
        category="c" * 150,
        confidence="f" * 40,
    )

    assert len(technology.name) == 100
    assert len(technology.detected_by) == 50
    assert len(technology.version) == 100
    assert len(technology.category) == 100
    assert len(technology.confidence) == 20


@pytest.mark.postgres
def test_create_technology_truncates_oversized_fields_against_real_postgres(postgres_session):
    # 6th independent evaluation: the SQLite-backed version above can't
    # actually prove the fix works, since SQLite never enforced
    # VARCHAR(100) in the first place - same reasoning as the existing
    # postgres-marked test for service_repository/scan_task_service, now
    # generalized to this repository too.
    scan = _make_scan(postgres_session)

    technology = technology_repository.create_technology(
        postgres_session,
        scan_id=scan.id,
        name="n" * 150,
        detected_by="d" * 80,
        version="v" * 150,
        category="c" * 150,
        confidence="f" * 40,
    )

    assert len(technology.name) == 100
    assert len(technology.detected_by) == 50


def test_create_technology_allows_none_optional_fields(db_session):
    scan = _make_scan(db_session)

    technology = technology_repository.create_technology(
        db_session,
        scan_id=scan.id,
        name="nginx",
        detected_by="whatweb",
        version=None,
        category=None,
        confidence=None,
    )

    assert technology.version is None
    assert technology.category is None
    assert technology.confidence is None
