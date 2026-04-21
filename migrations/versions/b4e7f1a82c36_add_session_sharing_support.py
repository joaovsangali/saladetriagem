"""add_session_sharing_support

Revision ID: b4e7f1a82c36
Revises: a3f8c2d91b45
Create Date: 2026-04-20 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4e7f1a82c36'
down_revision = 'a3f8c2d91b45'
branch_labels = None
depends_on = None


def upgrade():
    # Add join_code column to dashboard_sessions
    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('join_code', sa.String(length=6), nullable=True))
        batch_op.create_index(batch_op.f('ix_dashboard_sessions_join_code'), ['join_code'], unique=True)

    # Create session_collaborators table
    op.create_table(
        'session_collaborators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['dashboard_sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['police_users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'user_id', name='uq_session_collaborator'),
    )


def downgrade():
    op.drop_table('session_collaborators')

    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_dashboard_sessions_join_code'))
        batch_op.drop_column('join_code')
