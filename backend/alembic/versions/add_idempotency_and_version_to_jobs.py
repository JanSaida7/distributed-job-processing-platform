"""add_idempotency_and_version_to_jobs

Revision ID: add_idempotency_and_version
Revises: fde935203ddc_add_foreign_key_user_id_to_jobs
Create Date: 2026-09-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_idempotency_and_version'
down_revision = 'fde935203ddc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add idempotency_key column
    op.add_column('jobs', sa.Column('idempotency_key', sa.String(255), nullable=True))
    op.create_index('ix_jobs_idempotency_key', 'jobs', ['idempotency_key'])
    
    # Add version column with default value of 1
    op.add_column('jobs', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_index('ix_jobs_idempotency_key', table_name='jobs')
    op.drop_column('jobs', 'idempotency_key')
    op.drop_column('jobs', 'version')
