"""one active scan per target (8th independent evaluation)

Revision ID: d9eaa982d989
Revises: 5857d2b759ae
Create Date: 2026-08-26 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd9eaa982d989'
down_revision: Union[str, None] = '5857d2b759ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create_scan/trigger_pipeline only checked Target.is_active, never
    # whether the target already had a non-terminal scan - a partial unique
    # index makes "at most one active scan per target" a real DB-enforced
    # invariant instead of an unenforced assumption, same idea as the
    # unique constraint already backing targets.name.
    #
    # No explicit ::scan_status cast on the literals - Postgres infers the
    # enum type from the column context and implicitly casts a bare string
    # literal to it (an explicit cast instead resolves the type name via
    # search_path, which breaks under the test suite's per-schema
    # isolation - see database/models/scan.py's matching Index for the
    # full reasoning; this predicate must stay identical to that one).
    # SQLAlchemy's Enum type stores the Python member *name* (uppercase -
    # "COMPLETED"), not ScanStatus.COMPLETED.value ("completed") -
    # confirmed via \\dT+ scan_status against the real DB.
    op.create_index(
        'ix_scans_one_active_per_target',
        'scans',
        ['target_id'],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')"),
    )


def downgrade() -> None:
    op.drop_index('ix_scans_one_active_per_target', table_name='scans')
