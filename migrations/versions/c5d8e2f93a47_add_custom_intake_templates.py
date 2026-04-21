"""add_custom_intake_templates

Revision ID: c5d8e2f93a47
Revises: b4e7f1a82c36
Create Date: 2026-04-21 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5d8e2f93a47'
down_revision = 'b4e7f1a82c36'
branch_labels = None
depends_on = None


def upgrade():
    # Create custom_intake_templates table
    op.create_table(
        'custom_intake_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('schema', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['police_users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Add intake_type and custom_template_id to dashboard_sessions
    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('intake_type', sa.String(length=20), nullable=True, server_default='police')
        )
        batch_op.add_column(
            sa.Column('custom_template_id', sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_dashboard_sessions_custom_template_id',
            'custom_intake_templates',
            ['custom_template_id'],
            ['id'],
        )


def downgrade():
    with op.batch_alter_table('dashboard_sessions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_dashboard_sessions_custom_template_id', type_='foreignkey')
        batch_op.drop_column('custom_template_id')
        batch_op.drop_column('intake_type')

    op.drop_table('custom_intake_templates')
