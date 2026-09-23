"""unique scan_task per (scan_id, tool_name) (9th independent evaluation)

Revision ID: e016b6e11034
Revises: d9eaa982d989
Create Date: 2026-08-28 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'e016b6e11034'
down_revision: Union[str, None] = 'd9eaa982d989'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # n8n's Ingest: * nodes retry on transient failures - without this, a
    # lost/delayed response to an ingest that actually succeeded lets the
    # retry insert a second ScanTask and re-run the normalizer, duplicating
    # every Service/Technology/Finding/CveReference that tool run produced.
    #
    # Same class of problem, same fix shape, as
    # 029e48237524_unique_report_per_scan_format.py (10th independent
    # evaluation): purge duplicates before the unique index, so this
    # migration can still be applied from scratch against a pre-2026-08-28
    # backup that accumulated them under the old, unguarded behavior. The
    # deleted rows' Finding/CveReference children cascade away with them
    # (findings.scan_task_id is ON DELETE CASCADE) - but unlike Report,
    # a ScanTask's Service/Technology rows are keyed by scan_id, not
    # scan_task_id, so they don't cascade from here. Any historical
    # Service/Technology duplicates from that same old bug are out of
    # this migration's reach either way - this only makes the index
    # itself creatable again, the same narrow scope 029e48237524 had for
    # Report.
    op.execute(
        text(
            """
            DELETE FROM scan_tasks
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY scan_id, tool_name
                        ORDER BY created_at DESC, id DESC
                    ) AS rn
                    FROM scan_tasks
                ) ranked
                WHERE ranked.rn > 1
            )
            """
        )
    )
    op.drop_index('ix_scan_tasks_scan_id_tool_name', table_name='scan_tasks')
    op.create_index(
        'ix_scan_tasks_scan_id_tool_name',
        'scan_tasks',
        ['scan_id', 'tool_name'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('ix_scan_tasks_scan_id_tool_name', table_name='scan_tasks')
    op.create_index(
        'ix_scan_tasks_scan_id_tool_name',
        'scan_tasks',
        ['scan_id', 'tool_name'],
        unique=False,
    )
