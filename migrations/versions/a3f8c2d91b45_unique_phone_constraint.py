"""Add unique constraint to police_users phone

Revision ID: a3f8c2d91b45
Revises: 265f95c93217
Create Date: 2026-04-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3f8c2d91b45'
down_revision = '265f95c93217'
branch_labels = None
depends_on = None


def upgrade():
    # Remove duplicate phones, keeping the oldest account per phone
    op.execute("""
        DELETE FROM police_users
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM police_users
            GROUP BY phone
        ) AND phone IS NOT NULL AND phone != ''
    """)

    with op.batch_alter_table('police_users', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_police_users_phone'),
            ['phone'],
            unique=True,
        )


def downgrade():
    with op.batch_alter_table('police_users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_police_users_phone'))
