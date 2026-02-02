"""Add draws table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-29 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create draws table
    op.create_table('draws',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('external_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('prize_pool', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('draw_type', sa.String(length=50), nullable=True),
        sa.Column('periodicity', sa.String(length=50), nullable=True),
        sa.Column('numbers_to_pick', sa.Integer(), nullable=False),
        sa.Column('numbers_total', sa.Integer(), nullable=False),
        sa.Column('prize_grid', sa.Text(), nullable=True),
        sa.Column('winning_numbers', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('statistics', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_draws_external_id'), 'draws', ['external_id'], unique=True)
    op.create_index(op.f('ix_draws_status'), 'draws', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove indexes
    op.drop_index(op.f('ix_draws_status'), table_name='draws')
    op.drop_index(op.f('ix_draws_external_id'), table_name='draws')
    
    # Remove table
    op.drop_table('draws')
