"""denormalize scans.host, re-key one-active-scan index to it (2026-09-06 correction round)

Revision ID: 146a9472271c
Revises: e016b6e11034
Create Date: 2026-09-06 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = '146a9472271c'
down_revision: Union[str, None] = 'e016b6e11034'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ix_scans_one_active_per_target (see the 8th independent evaluation's
    # migration, d9eaa982d989) is keyed on target_id. Nothing stops two
    # Target rows pointing at the same physical host under different
    # names, so that index never noticed two concurrently-running scans
    # against the same host via two different targets - a real risk for
    # authenticated scans (scanner/app/services/dvwa_auth.py mutates
    # shared server-side session state per host). Postgres can't express a
    # partial unique index over a join to `targets`, so `host` is
    # denormalized onto `scans` (copied from the owning Target at scan
    # creation time - see scan_repository.create_scan) purely to give the
    # index a same-table column to key on.
    op.add_column('scans', sa.Column('host', sa.String(length=255), nullable=True))
    op.execute(
        "UPDATE scans SET host = targets.host "
        "FROM targets WHERE targets.id = scans.target_id"
    )
    op.alter_column('scans', 'host', nullable=False)

    op.drop_index('ix_scans_one_active_per_target', table_name='scans')
    op.create_index(
        'ix_scans_one_active_per_host',
        'scans',
        ['host'],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')"),
        sqlite_where=sa.text("status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')"),
    )


def downgrade() -> None:
    op.drop_index('ix_scans_one_active_per_host', table_name='scans')
    op.create_index(
        'ix_scans_one_active_per_target',
        'scans',
        ['target_id'],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')"),
        sqlite_where=sa.text("status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')"),
    )
    op.drop_column('scans', 'host')
