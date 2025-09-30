"""Add branches and stations tables with regions support

Revision ID: 0341e76f5bd0
Revises: 20250122_000001
Create Date: 2025-09-24 15:07:26.686521

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0341e76f5bd0'
down_revision = '20250122_000001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create branches table
    op.create_table('branches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_branches_code'), 'branches', ['code'], unique=False)
    op.create_index(op.f('ix_branches_state'), 'branches', ['state'], unique=False)
    
    # Create stations table
    op.create_table('stations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('branch_id', 'code', name='_branch_station_uc')
    )
    
    # Add columns to campaigns table
    op.add_column('campaigns', sa.Column('branches', sa.ARRAY(sa.String()), nullable=True))
    op.add_column('campaigns', sa.Column('regions', sa.ARRAY(sa.String()), nullable=True))
    
    # Fix users table constraint
    try:
        op.drop_index('ix_users_username', table_name='users')
    except:
        pass  # Index might not exist
    op.create_unique_constraint('uq_users_username', 'users', ['username'])


def downgrade() -> None:
    # Drop unique constraint on users
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    
    # Drop columns from campaigns
    op.drop_column('campaigns', 'regions')
    op.drop_column('campaigns', 'branches')
    
    # Drop stations table
    op.drop_table('stations')
    
    # Drop branches table
    op.drop_index(op.f('ix_branches_state'), table_name='branches')
    op.drop_index(op.f('ix_branches_code'), table_name='branches')
    op.drop_table('branches')