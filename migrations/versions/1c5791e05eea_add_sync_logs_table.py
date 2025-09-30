"""add_sync_logs_table

Revision ID: 1c5791e05eea
Revises: 7706a43078a4
Create Date: 2025-09-26 19:44:15.757239

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1c5791e05eea'
down_revision = '7706a43078a4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sync_logs table
    op.create_table('sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('records_processed', sa.Integer(), nullable=True, default=0),
        sa.Column('records_created', sa.Integer(), nullable=True, default=0),
        sa.Column('records_updated', sa.Integer(), nullable=True, default=0),
        sa.Column('records_failed', sa.Integer(), nullable=True, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('triggered_by', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sync_logs_id', 'sync_logs', ['id'], unique=False)
    op.create_index('ix_sync_logs_sync_type', 'sync_logs', ['sync_type'], unique=False)
    op.create_index('ix_sync_logs_status', 'sync_logs', ['status'], unique=False)


def downgrade() -> None:
    # Drop sync_logs table
    op.drop_index('ix_sync_logs_status', table_name='sync_logs')
    op.drop_index('ix_sync_logs_sync_type', table_name='sync_logs')
    op.drop_index('ix_sync_logs_id', table_name='sync_logs')
    op.drop_table('sync_logs')