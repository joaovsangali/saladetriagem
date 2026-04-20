"""add_shared_session_access

Revision ID: b1c2d3e4f5a6
Revises: a3f8c2d91b45
Create Date: 2026-04-20 00:00:00.000000

"""
import secrets
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = 'a3f8c2d91b45'
branch_labels = None
depends_on = None


def upgrade():
    # Add share_code column to dashboard_sessions
    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('share_code', sa.String(length=16), nullable=True))
        batch_op.create_index(batch_op.f('ix_dashboard_sessions_share_code'), ['share_code'], unique=True)

    # Populate share_code for existing sessions
    conn = op.get_bind()
    sessions = conn.execute(sa.text("SELECT id FROM dashboard_sessions")).fetchall()
    for row in sessions:
        code = secrets.token_urlsafe(8)
        conn.execute(
            sa.text("UPDATE dashboard_sessions SET share_code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )

    # Create shared_session_access table
    op.create_table(
        'shared_session_access',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['dashboard_sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['police_users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'user_id', name='uq_shared_session_user'),
    )

    # Populate admin access for existing sessions
    conn.execute(
        sa.text(
            "INSERT INTO shared_session_access (session_id, user_id, role, is_active) "
            "SELECT id, user_id, 'admin', 1 FROM dashboard_sessions"
        )
    )


def downgrade():
    op.drop_table('shared_session_access')

    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_dashboard_sessions_share_code'))
        batch_op.drop_column('share_code')
