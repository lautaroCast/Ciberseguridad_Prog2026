"""unique report per (scan_id, format) (Ronda L, rigorous eval 2026-09-23)

Revision ID: 029e48237524
Revises: e0fd682ed5c0
Create Date: 2026-09-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = '029e48237524'
down_revision: Union[str, None] = 'e0fd682ed5c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Generate Report's own retryOnFail (n8n) can re-send the same
    # POST /scans/{id}/reports after a slow/lost response to a first
    # attempt that already committed - without this, the retry inserts a
    # second Report row for the same (scan, format). Same class of problem,
    # same fix shape, as ix_scan_tasks_scan_id_tool_name.
    #
    # Confirmed live against this project's own dev DB while writing this
    # migration: 3 scans already had duplicate (scan_id, format) rows (2,
    # 4 and 2 copies) from exactly this bug, which makes creating the
    # unique index below fail with a UniqueViolation until they're
    # collapsed first. All duplicates for a given (scan_id, format) point
    # at the same file_path (the Reports Service always writes
    # "{scan_id}.{ext}", overwritten atomically on every render), so
    # keeping the most recently generated row and dropping the rest loses
    # no report data - only the redundant duplicate metadata rows.
    op.execute(
        text(
            """
            DELETE FROM reports
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY scan_id, format
                        ORDER BY generated_at DESC, id DESC
                    ) AS rn
                    FROM reports
                ) ranked
                WHERE ranked.rn > 1
            )
            """
        )
    )
    op.drop_index('ix_reports_scan_id', table_name='reports')
    op.create_index(
        'ix_reports_scan_id_format',
        'reports',
        ['scan_id', 'format'],
        unique=True,
    )


def downgrade() -> None:
    # Does not restore the duplicate rows the upgrade deleted - they were
    # bogus (a bug's byproduct, all pointing at the same file), not data
    # worth recreating.
    op.drop_index('ix_reports_scan_id_format', table_name='reports')
    op.create_index(
        'ix_reports_scan_id',
        'reports',
        ['scan_id'],
        unique=False,
    )
