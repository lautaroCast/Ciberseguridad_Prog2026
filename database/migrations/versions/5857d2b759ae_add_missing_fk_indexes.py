"""add missing FK indexes (COD-13)

Revision ID: 5857d2b759ae
Revises: adabb9c55a34
Create Date: 2026-08-15 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5857d2b759ae'
down_revision: Union[str, None] = 'adabb9c55a34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Every other FK in the schema besides these five is already covered by
    # a composite index (ix_scan_tasks_scan_id_tool_name,
    # ix_findings_scan_id_severity) or is itself the indexed column
    # (ix_cve_references_cve_id). These five had no index at all — fine at
    # lab scale, but every list_*_for_* repository query on them would be a
    # full table scan once scan history accumulates.
    op.create_index('ix_scans_target_id', 'scans', ['target_id'], unique=False)
    op.create_index('ix_technologies_scan_id', 'technologies', ['scan_id'], unique=False)
    op.create_index('ix_reports_scan_id', 'reports', ['scan_id'], unique=False)
    op.create_index('ix_findings_scan_task_id', 'findings', ['scan_task_id'], unique=False)
    op.create_index('ix_cve_references_finding_id', 'cve_references', ['finding_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_cve_references_finding_id', table_name='cve_references')
    op.drop_index('ix_findings_scan_task_id', table_name='findings')
    op.drop_index('ix_reports_scan_id', table_name='reports')
    op.drop_index('ix_technologies_scan_id', table_name='technologies')
    op.drop_index('ix_scans_target_id', table_name='scans')
