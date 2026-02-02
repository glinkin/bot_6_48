"""Add customer fields to users

Revision ID: a1b2c3d4e5f6
Revises: 58ec28ab042c
Create Date: 2026-01-29 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '58ec28ab042c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to users table
    op.add_column('users', sa.Column('external_id', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('balance', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('users', sa.Column('birthday', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('sex', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('available_tickets', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('additional_fields', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Create indexes
    op.create_index(op.f('ix_users_external_id'), 'users', ['external_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove indexes
    op.drop_index(op.f('ix_users_external_id'), table_name='users')
    
    # Remove columns
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'additional_fields')
    op.drop_column('users', 'available_tickets')
    op.drop_column('users', 'sex')
    op.drop_column('users', 'birthday')
    op.drop_column('users', 'balance')
    op.drop_column('users', 'email')
    op.drop_column('users', 'name')
    op.drop_column('users', 'external_id')
