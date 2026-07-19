"""Shared pytest fixtures for the Backend test suite.

`app.config.Settings` reads several required env vars at *import* time
(via the `@lru_cache`d `get_settings()`, called both by `app.database` and
`app.main` at module scope) — so these must be set before any `app.*`
module is imported anywhere in the test session, which is why they're set
here, at conftest module scope, before the fixtures below ever import
`app.main`/`app.database`.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("BACKEND_ALLOWED_LAB_HOSTS", "juice-shop,dvwa")
os.environ.setdefault("N8N_WEBHOOK_BASE_URL", "http://n8n:5678")
os.environ.setdefault("REPORTS_BASE_URL", "http://reports:8200")

import uuid  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import create_engine, event, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402


def _make_gen_random_uuid_sqlite_compatible() -> None:
    """Rewrite the `id` columns' server_default text for SQLite's DDL grammar.

    `models.base.UUIDPrimaryKeyMixin` uses
    `server_default=text("gen_random_uuid()")`. Postgres accepts a bare
    function call there, but SQLite's `CREATE TABLE ... DEFAULT <expr>`
    grammar requires a non-literal expression to be wrapped in parens
    (`DEFAULT (gen_random_uuid())`) — without it, `Base.metadata.create_all()`
    itself fails with `OperationalError: near "(": syntax error` before any
    row is ever inserted. This only rewrites the DDL text used for the
    in-memory SQLite schema (matched by the exact original text, so it's a
    no-op on repeat calls); it never touches `database/models/base.py`, and
    the corresponding `gen_random_uuid` SQLite function registered on
    connect (below) is what actually makes the wrapped call resolve.
    """
    from models import Base

    for table in Base.metadata.tables.values():
        for column in table.columns:
            default = column.server_default
            arg = getattr(default, "arg", None)
            if getattr(arg, "text", None) == "gen_random_uuid()":
                default.arg = text("(gen_random_uuid())")


_uuid_pk_listener_registered = False


def _assign_uuid_pk_before_insert() -> None:
    """Populate `id` client-side before flush, once, for every mapped model.

    Even with `gen_random_uuid()` made syntactically valid for SQLite's DDL
    (see above) and registered as a real SQLite function, SQLAlchemy's
    SQLite dialect doesn't reliably fetch a server-generated default back
    into the ORM object after INSERT the way it does for Postgres (which
    always uses `INSERT ... RETURNING`) — `Session.refresh()` right after
    `create_target()`'s `db.commit()` then fails with "Could not refresh
    instance" because the object's `id` was never populated locally. Setting
    `id` in Python before the row is even flushed sidesteps that gap
    entirely: the INSERT includes a concrete id, so nothing needs to be
    fetched back afterward. Registered once on the shared declarative
    `Base` (with `propagate=True`) rather than per-fixture-call, since
    mapper event listeners aren't meant to be repeatedly added/removed.
    """
    global _uuid_pk_listener_registered
    if _uuid_pk_listener_registered:
        return

    from models import Base

    @event.listens_for(Base, "before_insert", propagate=True)
    def _set_id(mapper, connection, target):
        if getattr(target, "id", None) is None:
            target.id = uuid.uuid4()

    _uuid_pk_listener_registered = True


@pytest.fixture
def sqlite_engine():
    """An in-memory SQLite engine with the full ORM schema created.

    Repositories (e.g. `target_repository.create_target`) never pass an
    explicit `id=` on insert, relying entirely on the `id` column's
    `server_default` to generate one. Registering a Python-backed
    `gen_random_uuid` SQLite function on connect makes that same
    server_default resolve correctly at the SQL level; the before_insert
    listener above additionally covers SQLAlchemy's own inability to fetch
    that generated value back into the ORM object under SQLite. Neither
    changes any production model/repository code.
    """
    from models import Base

    _make_gen_random_uuid_sqlite_compatible()
    _assign_uuid_pk_before_insert()

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_connection, connection_record):
        dbapi_connection.create_function("gen_random_uuid", 0, lambda: str(uuid.uuid4()))

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(sqlite_engine) -> Session:
    session = sessionmaker(bind=sqlite_engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    from app.database import get_db
    from app.main import app
    from fastapi.testclient import TestClient

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
