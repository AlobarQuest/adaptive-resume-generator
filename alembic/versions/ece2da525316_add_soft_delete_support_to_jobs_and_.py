"""Add soft delete support to jobs and bullet_points

Revision ID: ece2da525316
Revises: 8482904c82bb
Create Date: 2025-11-15 09:54:50.541216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ece2da525316'
down_revision: Union[str, Sequence[str], None] = '8482904c82bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add deleted_at column to jobs table for soft delete
    op.add_column('jobs', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # Add deleted_at column to bullet_points table for soft delete
    op.add_column('bullet_points', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove deleted_at column from bullet_points table
    op.drop_column('bullet_points', 'deleted_at')

    # Remove deleted_at column from jobs table
    op.drop_column('jobs', 'deleted_at')
