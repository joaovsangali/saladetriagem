"""add_session_collaborators

Revision ID: b1e2f3a4c5d6
Revises: a3f8c2d91b45
Create Date: 2026-04-19 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1e2f3a4c5d6'
down_revision = 'a3f8c2d91b45'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'session_collaborators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dashboard_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('invited_by', sa.Integer(), nullable=False),
        sa.Column('invited_at', sa.DateTime(), nullable=True),
        sa.Column('access_level', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboard_sessions.id'], ),
        sa.ForeignKeyConstraint(['invited_by'], ['police_users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['police_users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dashboard_id', 'user_id', name='uq_session_collaborator'),
    )

    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('share_code', sa.String(length=8), nullable=True))
        batch_op.add_column(sa.Column('share_code_expires_at', sa.DateTime(), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_dashboard_sessions_share_code'),
            ['share_code'],
            unique=True,
        )


def downgrade():
    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_dashboard_sessions_share_code'))
        batch_op.drop_column('share_code_expires_at')
        batch_op.drop_column('share_code')

    op.drop_table('session_collaborators')
