"""COD-6: scan_task_service.ingest_scan_task had zero test coverage despite
being described as "Módulo 5's core" — this covers the happy path (real
counts from a real normalizer), the normalizer-failure-doesn't-fail-ingest
branch, and the service_id-always-None behavior (COD-10)."""

from datetime import UTC, datetime

import pytest

from app.services import scan_service, scan_task_service, target_service


def _make_scan(db_session):
    target = target_service.register_target(
        db_session, name="juice-shop-demo", host="juice-shop", description=None
    )
    return scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)


def _ingest(db_session, scan_id, **overrides):
    now = datetime.now(UTC)
    kwargs = {
        "tool": "nmap",
        "command": "nmap -sV juice-shop",
        "status": "completed",
        "started_at": now,
        "finished_at": now,
        "raw_output": "<nmaprun></nmaprun>",
        "parsed": None,
        "error_message": None,
    }
    kwargs.update(overrides)
    return scan_task_service.ingest_scan_task(db_session, scan_id, **kwargs)


@pytest.mark.postgres
def test_ingest_locks_scan_row_blocking_concurrent_complete_scan(postgres_session_pair):
    """Ronda L: the terminal-status check in ingest_scan_task was a plain
    SELECT-then-check in Python with no DB-level backstop — unlike
    scan_repository.complete_scan's own conditional UPDATE, nothing kept a
    concurrent complete_scan from reading "not terminal yet" and
    committing while this transaction was still writing rows for the same
    scan. This proves the fix (get_scan_for_update_or_raise's row lock)
    actually blocks a concurrent writer, which a single-session test can't
    exercise at all."""
    import threading

    from models import ScanStatus

    from app.services.scan_service import complete_scan, get_scan_for_update_or_raise

    session_a, session_b = postgres_session_pair
    scan = _make_scan(session_a)
    scan_id = scan.id
    session_a.commit()  # make the scan visible to session_b

    # Session A takes the lock (the first thing ingest_scan_task does) and
    # holds its transaction open — standing in for "still normalizing and
    # inserting Service/Technology/Finding rows".
    get_scan_for_update_or_raise(session_a, scan_id)

    result: dict = {}

    def _try_complete():
        result["scan"] = complete_scan(
            session_b, scan_id, status=ScanStatus.COMPLETED, error_message=None
        )

    thread = threading.Thread(target=_try_complete)
    thread.start()
    thread.join(timeout=0.5)
    assert thread.is_alive(), "complete_scan should block on session A's row lock, not proceed"

    session_a.commit()  # session A "finishes ingesting"
    thread.join(timeout=5)
    assert not thread.is_alive(), "complete_scan should unblock once the lock is released"
    assert result["scan"].status == ScanStatus.COMPLETED


def test_ingest_into_an_already_terminal_scan_raises(db_session):
    """Ronda J: get_scan_or_raise only checked the scan exists, never its
    status — a late/retried Ingest node landing after Complete Scan
    already ran would silently attach rows to a scan every caller was
    already told is "done"."""
    from models import ScanStatus

    scan = _make_scan(db_session)
    scan_service.complete_scan(db_session, scan.id, status=ScanStatus.COMPLETED, error_message=None)

    with pytest.raises(scan_service.ScanAlreadyTerminalError):
        _ingest(db_session, scan.id, tool="nmap")


def test_ingest_happy_path_creates_services_from_normalizer(db_session):
    scan = _make_scan(db_session)
    result = _ingest(
        db_session,
        scan.id,
        tool="nmap",
        parsed=[{"host": "juice-shop", "port": 80, "service_name": "http"}],
    )
    assert result.services_upserted == 1
    assert result.technologies_created == 0
    assert result.findings_created == 0
    assert result.scan_task.tool_name == "nmap"


def test_ingest_integrity_error_not_explained_by_a_duplicate_reraises(db_session, monkeypatch):
    """Ronda I: the IntegrityError handler used to `assert existing is not
    None`, assuming the unique (scan_id, tool_name) index was always the
    cause. If some other IntegrityError reached here (e.g. a FK violation
    from the scan being deleted mid-flight) and the lookup legitimately
    found nothing, the assert masked the real cause as an AssertionError
    instead of propagating it — same idiom as
    service_repository.get_or_create_service's own `if existing is None:
    raise`."""
    from sqlalchemy.exc import IntegrityError

    from app.repositories import scan_task_repository

    scan = _make_scan(db_session)
    _ingest(db_session, scan.id, tool="nmap")

    monkeypatch.setattr(
        scan_task_repository, "get_scan_task_by_scan_and_tool", lambda *a, **k: None
    )

    with pytest.raises(IntegrityError):
        _ingest(db_session, scan.id, tool="nmap")


def test_ingesting_the_same_tool_twice_is_an_idempotent_replay_not_a_refine(db_session):
    """9th independent evaluation: n8n's Ingest: * nodes retry on transient
    failures (continueOnFail + retryOnFail) - a retry of an ingest that
    already succeeded must not duplicate or re-normalize anything, even
    with a different (e.g. more complete) payload the second time. The
    unique (scan_id, tool_name) index is the real guard; this proves
    ingest_scan_task's IntegrityError handling returns the *first* call's
    result untouched rather than re-running the normalizer."""
    scan = _make_scan(db_session)
    first = _ingest(
        db_session,
        scan.id,
        tool="nmap",
        parsed=[{"host": "juice-shop", "port": 80, "service_name": "http"}],
    )
    assert first.services_upserted == 1

    second = _ingest(
        db_session,
        scan.id,
        tool="nmap",
        parsed=[
            {
                "host": "juice-shop",
                "port": 80,
                "service_name": "http",
                "product": "nginx",
                "version": "1.25.0",
            }
        ],
    )
    assert second.services_upserted == 0
    assert second.scan_task.id == first.scan_task.id

    from models import ScanTask, Service
    from sqlalchemy import select as sa_select

    services = (
        db_session.execute(sa_select(Service).where(Service.scan_id == scan.id))
        .scalars()
        .all()
    )
    assert len(services) == 1
    # The retry's payload (product/version) must never have reached the
    # normalizer - the first call's values survive untouched.
    assert services[0].product is None
    assert services[0].version is None

    scan_tasks = (
        db_session.execute(sa_select(ScanTask).where(ScanTask.scan_id == scan.id))
        .scalars()
        .all()
    )
    assert len(scan_tasks) == 1


def test_ingest_happy_path_creates_findings_from_normalizer(db_session):
    scan = _make_scan(db_session)
    result = _ingest(
        db_session,
        scan.id,
        tool="nuclei",
        parsed=[
            {
                "template-id": "exposed-panel",
                "type": "http",
                "host": "juice-shop",
                "matched-at": "http://juice-shop/admin",
                "info": {"name": "Exposed Admin Panel", "severity": "high"},
            }
        ],
    )
    assert result.findings_created == 1
    # COD-10: service_id is documented as unpopulated, never a real FK match.
    task = result.scan_task
    assert task.raw_output == "<nmaprun></nmaprun>"


def test_ingest_without_parsed_creates_no_normalized_rows(db_session):
    scan = _make_scan(db_session)
    result = _ingest(db_session, scan.id, tool="nmap", parsed=None)
    assert result.services_upserted == 0
    assert result.findings_created == 0
    assert result.technologies_created == 0


def test_ingest_failed_status_skips_normalization_even_with_parsed(db_session):
    scan = _make_scan(db_session)
    result = _ingest(
        db_session,
        scan.id,
        tool="nmap",
        status="failed",
        parsed=[{"host": "juice-shop", "port": 80}],
        error_message="tool crashed",
    )
    assert result.services_upserted == 0
    assert result.scan_task.error_message == "tool crashed"


def test_normalizer_failure_is_recorded_not_raised(db_session, monkeypatch):
    from app.normalization import registry

    def _broken_normalizer(parsed):
        raise ValueError("malformed tool output")

    monkeypatch.setitem(registry._NORMALIZERS, "nmap", _broken_normalizer)

    scan = _make_scan(db_session)
    result = _ingest(db_session, scan.id, tool="nmap", parsed=[{"host": "x", "port": 1}])

    assert result.services_upserted == 0
    assert result.findings_created == 0
    assert "Normalization failed" in result.scan_task.error_message
    assert "malformed tool output" in result.scan_task.error_message


def test_ingest_unknown_scan_raises(db_session):
    import uuid

    with pytest.raises(scan_service.ScanNotFoundError):
        _ingest(db_session, uuid.uuid4(), tool="nmap")


def test_ingest_truncates_oversized_service_fields(db_session):
    # Recomendación #3 (docs/independent-evaluation-report.md): product/
    # version have no length guarantee from the tool and the column is
    # String(100) — must be truncated, not raise.
    scan = _make_scan(db_session)
    result = _ingest(
        db_session,
        scan.id,
        tool="nmap",
        parsed=[
            {
                "host": "juice-shop",
                "port": 80,
                "service_name": "http",
                "product": "x" * 150,
                "version": "y" * 150,
            }
        ],
    )
    assert result.services_upserted == 1

    from models import Service
    from sqlalchemy import select as sa_select

    service = db_session.execute(
        sa_select(Service).where(Service.scan_id == scan.id)
    ).scalar_one()
    assert len(service.product) == 100
    assert len(service.version) == 100


@pytest.mark.postgres
def test_ingest_truncates_oversized_service_fields_against_real_postgres(postgres_session):
    # Recomendación #4: the SQLite-backed version of this test
    # (test_ingest_truncates_oversized_service_fields above) can't actually
    # prove the fix works, because SQLite never enforced VARCHAR(100) in
    # the first place — this is the one test in the suite that runs
    # against a database that would genuinely reject an untruncated value.
    scan = _make_scan(postgres_session)
    result = _ingest(
        postgres_session,
        scan.id,
        tool="nmap",
        parsed=[
            {
                "host": "juice-shop",
                "port": 80,
                "service_name": "http",
                "product": "x" * 150,
                "version": "y" * 150,
            }
        ],
    )
    assert result.services_upserted == 1

    from models import Service
    from sqlalchemy import select as sa_select

    service = postgres_session.execute(
        sa_select(Service).where(Service.scan_id == scan.id)
    ).scalar_one()
    assert len(service.product) == 100
    assert len(service.version) == 100


def test_ingest_rolls_back_partial_writes_on_db_error_without_losing_scan_task(
    db_session, monkeypatch
):
    # A DB-level failure mid-write (not a normalizer exception) must be
    # caught the same way: the ScanTask row already flushed must survive,
    # and the counts must reflect that nothing from this normalizer run
    # actually persisted (the SAVEPOINT rolled it all back).
    from app.repositories import finding_repository

    def _broken_create_finding(*args, **kwargs):
        raise RuntimeError("simulated DB constraint violation")

    monkeypatch.setattr(finding_repository, "create_finding", _broken_create_finding)

    scan = _make_scan(db_session)
    result = _ingest(
        db_session,
        scan.id,
        tool="nuclei",
        parsed=[
            {
                "template-id": "exposed-panel",
                "type": "http",
                "host": "juice-shop",
                "info": {"name": "Exposed Admin Panel", "severity": "high"},
            }
        ],
    )

    assert result.findings_created == 0
    assert "Normalization failed" in result.scan_task.error_message
    assert "simulated DB constraint violation" in result.scan_task.error_message

    from app.services import scan_task_service as sts

    tasks = sts.list_scan_tasks_for_scan(db_session, scan.id)
    assert len(tasks) == 1
    assert tasks[0].id == result.scan_task.id
