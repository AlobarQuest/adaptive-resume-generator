"""add_job_posting_metadata_fields

Revision ID: 7511b5df92b2
Revises: 1912d441f4d7
Create Date: 2025-11-17 12:55:04.958010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7511b5df92b2'
down_revision: Union[str, Sequence[str], None] = '1912d441f4d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new metadata fields to job_postings table
    with op.batch_alter_table('job_postings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location', sa.String(200), nullable=True))
        batch_op.add_column(sa.Column('salary_range', sa.String(200), nullable=True))
        batch_op.add_column(sa.Column('application_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('source', sa.String(50), nullable=True))  # 'paste', 'upload', 'import'
        batch_op.add_column(sa.Column('notes', sa.Text, nullable=True))  # User notes about the posting


def downgrade() -> None:
    """Downgrade schema."""
    # Remove metadata fields from job_postings table
    with op.batch_alter_table('job_postings', schema=None) as batch_op:
        batch_op.drop_column('notes')
        batch_op.drop_column('source')
        batch_op.drop_column('application_url')
        batch_op.drop_column('salary_range')
        batch_op.drop_column('location')
