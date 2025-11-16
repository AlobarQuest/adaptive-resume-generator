"""add_resume_variant_support

Revision ID: 271a28236056
Revises: 30646f248885
Create Date: 2025-11-16 07:38:00.540608

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '271a28236056'
down_revision: Union[str, Sequence[str], None] = '30646f248885'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add resume variant support."""
    # Add variant-related columns to tailored_resumes table
    with op.batch_alter_table('tailored_resumes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('variant_name', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('variant_number', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('parent_variant_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('performance_metrics', sa.Text(), nullable=True))

        # Add foreign key for parent_variant_id (self-referential)
        batch_op.create_foreign_key(
            'fk_tailored_resumes_parent_variant',
            'tailored_resumes',
            ['parent_variant_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add index for faster variant queries
        batch_op.create_index(
            'ix_tailored_resumes_job_posting_variant',
            ['job_posting_id', 'variant_number'],
            unique=False
        )


def downgrade() -> None:
    """Downgrade schema - Remove resume variant support."""
    with op.batch_alter_table('tailored_resumes', schema=None) as batch_op:
        # Drop index
        batch_op.drop_index('ix_tailored_resumes_job_posting_variant')

        # Drop foreign key
        batch_op.drop_constraint('fk_tailored_resumes_parent_variant', type_='foreignkey')

        # Drop columns
        batch_op.drop_column('performance_metrics')
        batch_op.drop_column('notes')
        batch_op.drop_column('is_primary')
        batch_op.drop_column('parent_variant_id')
        batch_op.drop_column('variant_number')
        batch_op.drop_column('variant_name')
