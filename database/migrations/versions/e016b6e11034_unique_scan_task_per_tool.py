"""unique scan_task per (scan_id, tool_name) (9th independent evaluation)

Revision ID: e016b6e11034
Revises: d9eaa982d989
Create Date: 2026-08-28 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e016b6e11034'
down_revision: Union[str, None] = 'd9eaa982d989'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # n8n's Ingest: * nodes retry on transient failures - without this, a
    # lost/delayed response to an ingest that actually succeeded lets the
    # retry insert a second ScanTask and re-run the normalizer, duplicating
    # every Service/Technology/Finding/CveReference that tool run produced.
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
