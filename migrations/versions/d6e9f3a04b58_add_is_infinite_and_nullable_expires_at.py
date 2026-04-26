"""add_is_infinite_and_nullable_expires_at

Revision ID: d6e9f3a04b58
Revises: c5d8e2f93a47
Create Date: 2026-04-26 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd6e9f3a04b58'
down_revision = 'c5d8e2f93a47'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        # Add is_infinite flag (nullable initially for safety, then set default)
        batch_op.add_column(
            sa.Column('is_infinite', sa.Boolean(), nullable=True, server_default='false')
        )
        # Make expires_at nullable to support infinite sessions
        batch_op.alter_column(
            'expires_at',
            existing_type=sa.DateTime(),
            nullable=True,
        )

    # Ensure all existing rows have is_infinite = false
    op.execute("UPDATE dashboard_sessions SET is_infinite = false WHERE is_infinite IS NULL")


def downgrade():
    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        # Restore expires_at to non-nullable
        # First fill any NULLs to avoid constraint violation
        op.execute(
            "UPDATE dashboard_sessions SET expires_at = created_at + INTERVAL '12 hours' WHERE expires_at IS NULL"
        )
        batch_op.alter_column(
            'expires_at',
            existing_type=sa.DateTime(),
            nullable=False,
        )
        batch_op.drop_column('is_infinite')
