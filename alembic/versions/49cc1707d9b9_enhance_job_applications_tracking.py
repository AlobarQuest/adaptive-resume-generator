"""enhance_job_applications_tracking

Revision ID: 49cc1707d9b9
Revises: 271a28236056
Create Date: 2025-11-16 08:14:19.209702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49cc1707d9b9'
down_revision: Union[str, Sequence[str], None] = '271a28236056'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add comprehensive application tracking fields."""
    # Add all columns
    with op.batch_alter_table('job_applications', schema=None) as batch_op:
        # Foreign key columns
        batch_op.add_column(sa.Column('job_posting_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('tailored_resume_id', sa.Integer(), nullable=True))

        # Application tracking fields
        batch_op.add_column(sa.Column('application_method', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('discovered_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('substatus', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.String(length=20), nullable=True))

        # Timeline tracking
        batch_op.add_column(sa.Column('first_response_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('interview_dates', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('offer_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('rejection_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('acceptance_date', sa.Date(), nullable=True))

        # Contact information
        batch_op.add_column(sa.Column('contact_phone', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('recruiter_name', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('recruiter_email', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('last_contact_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('next_followup_date', sa.Date(), nullable=True))

        # Job details
        batch_op.add_column(sa.Column('salary_range', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('location', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('remote_option', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('referral_source', sa.String(length=200), nullable=True))

        # Metrics
        batch_op.add_column(sa.Column('response_time_days', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('interview_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('total_time_to_outcome_days', sa.Integer(), nullable=True))

        # Legacy field
        batch_op.add_column(sa.Column('follow_up_date', sa.Date(), nullable=True))

        # Create indexes
        batch_op.create_index('ix_job_applications_job_posting_id', ['job_posting_id'])

    # Set default values for existing rows
    op.execute("UPDATE job_applications SET priority = 'medium' WHERE priority IS NULL")
    op.execute("UPDATE job_applications SET interview_count = 0 WHERE interview_count IS NULL")

    # Create foreign key constraints separately (SQLite compatibility)
    with op.batch_alter_table('job_applications', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_job_applications_job_posting_id', 'job_postings', ['job_posting_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_job_applications_tailored_resume_id', 'tailored_resumes', ['tailored_resume_id'], ['id'], ondelete='SET NULL')

    # Note: Check constraint modification is skipped for SQLite compatibility
    # The new status values ('discovered', 'interested', 'offer_received') will be validated at the application level


def downgrade() -> None:
    """Downgrade schema - Remove application tracking fields."""
    # Drop foreign keys first
    with op.batch_alter_table('job_applications', schema=None) as batch_op:
        batch_op.drop_constraint('fk_job_applications_tailored_resume_id', type_='foreignkey')
        batch_op.drop_constraint('fk_job_applications_job_posting_id', type_='foreignkey')

    # Drop indexes and columns
    with op.batch_alter_table('job_applications', schema=None) as batch_op:
        batch_op.drop_index('ix_job_applications_job_posting_id')

        # Drop all added columns
        batch_op.drop_column('follow_up_date')
        batch_op.drop_column('total_time_to_outcome_days')
        batch_op.drop_column('interview_count')
        batch_op.drop_column('response_time_days')
        batch_op.drop_column('referral_source')
        batch_op.drop_column('remote_option')
        batch_op.drop_column('location')
        batch_op.drop_column('salary_range')
        batch_op.drop_column('next_followup_date')
        batch_op.drop_column('last_contact_date')
        batch_op.drop_column('recruiter_email')
        batch_op.drop_column('recruiter_name')
        batch_op.drop_column('contact_phone')
        batch_op.drop_column('acceptance_date')
        batch_op.drop_column('rejection_date')
        batch_op.drop_column('offer_date')
        batch_op.drop_column('interview_dates')
        batch_op.drop_column('first_response_date')
        batch_op.drop_column('priority')
        batch_op.drop_column('substatus')
        batch_op.drop_column('discovered_date')
        batch_op.drop_column('application_method')
        batch_op.drop_column('tailored_resume_id')
        batch_op.drop_column('job_posting_id')
