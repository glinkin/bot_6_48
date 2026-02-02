"""Update tickets table with API fields

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-29 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Delete old tickets data (old format incompatible with new API structure)
    op.execute("DELETE FROM tickets")
    
    # Add new columns to tickets table
    op.add_column('tickets', sa.Column('external_id', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('customer_id', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('is_winner', sa.Boolean(), nullable=True))
    op.add_column('tickets', sa.Column('matched_count', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('prize_amount', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('tickets', sa.Column('filled_at', sa.DateTime(), nullable=True))
    op.add_column('tickets', sa.Column('filled_by', sa.String(length=50), nullable=True))
    op.add_column('tickets', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Change draw_id from String to Integer
    op.alter_column('tickets', 'draw_id',
                    existing_type=sa.String(20),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='CAST(draw_id AS INTEGER)')
    
    # Create index on external_id
    op.create_index(op.f('ix_tickets_external_id'), 'tickets', ['external_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove index
    op.drop_index(op.f('ix_tickets_external_id'), table_name='tickets')
    
    # Revert draw_id to String
    op.alter_column('tickets', 'draw_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(20),
                    existing_nullable=False)
    
    # Remove columns
    op.drop_column('tickets', 'updated_at')
    op.drop_column('tickets', 'filled_by')
    op.drop_column('tickets', 'filled_at')
    op.drop_column('tickets', 'prize_amount')
    op.drop_column('tickets', 'matched_count')
    op.drop_column('tickets', 'is_winner')
    op.drop_column('tickets', 'customer_id')
    op.drop_column('tickets', 'external_id')
