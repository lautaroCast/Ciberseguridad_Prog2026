"""drop unused users table/user_role enum (2026-09-08 correction round)

Revision ID: e0fd682ed5c0
Revises: 146a9472271c
Create Date: 2026-09-08 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e0fd682ed5c0'
down_revision: Union[str, None] = '146a9472271c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The User/UserRole model (a placeholder never consumed by any route
    # or service) was removed from the codebase in commit 45a186e - but
    # that commit edited the *already-applied* adabb9c55a34_initial_schema
    # migration in place to stop creating the table, instead of adding a
    # new migration to drop it. Alembic's contract is append-only: a
    # database whose alembic_version was already past adabb9c55a34 when
    # that edit landed never re-ran it, so its `users` table and
    # `user_role` enum type were silently orphaned - confirmed against
    # this project's own real dev database (2026-09-08), which still has
    # both. adabb9c55a34 itself has been restored to its original,
    # historically-accurate content in this same correction round; this
    # migration is the real drop step that content always implied but
    # never had.
    # op.drop_table() has no `if_exists` in this project's pinned Alembic
    # (1.13.2 - checked DropTableOp.__init__'s real signature) - it would
    # hard-fail with UndefinedTable on any database that was bootstrapped
    # during the ~10-day window the bad edit above stood, where `users`
    # was never created in the first place. Same defensive technique
    # already used one line below for the enum: build the SQLAlchemy
    # object directly and drop it with checkfirst=True.
    sa.Table('users', sa.MetaData()).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.create_table('users',
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=True),
    sa.Column('role', sa.Enum('ADMIN', 'ANALYST', name='user_role'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
