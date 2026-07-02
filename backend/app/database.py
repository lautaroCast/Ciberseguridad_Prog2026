"""SQLAlchemy engine/session wiring.

Models are not redefined here: `models/` is the same package the
`database/` migration image uses (Módulo 1), copied verbatim into this
image's build context so the Backend — the schema's owner per the
architecture doc — never drifts from what Alembic actually applied.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
