"""enforce_single_profile_design

This migration enforces the single-profile design for the desktop application:
1. Keeps the first profile (lowest id)
2. Deletes all other profiles (CASCADE handles related data)
3. Normalizes the kept profile to id=1 if needed

Revision ID: 1912d441f4d7
Revises: 49cc1707d9b9
Create Date: 2025-11-16 12:42:39.408878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '1912d441f4d7'
down_revision: Union[str, Sequence[str], None] = '49cc1707d9b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enforce single-profile design by:
    1. Finding the first profile (lowest id)
    2. Deleting all other profiles (CASCADE handles related data)
    3. Normalizing the kept profile to id=1 if needed
    """
    connection = op.get_bind()

    # Get all profile IDs, sorted
    result = connection.execute(text("SELECT id FROM profiles ORDER BY id ASC"))
    profile_ids = [row[0] for row in result.fetchall()]

    if not profile_ids:
        # No profiles exist - nothing to do
        return

    first_profile_id = profile_ids[0]

    # Delete all profiles except the first one (CASCADE will handle related data)
    if len(profile_ids) > 1:
        for profile_id in profile_ids[1:]:
            connection.execute(
                text("DELETE FROM profiles WHERE id = :profile_id"),
                {"profile_id": profile_id}
            )

    # If the first profile is not id=1, normalize it
    if first_profile_id != 1:
        # Tables with profile_id foreign keys that need updating
        tables_with_profile_fk = [
            'jobs',
            'skills',
            'education',
            'certifications',
            'job_applications',
            'job_postings',
            'tailored_resumes',
            'cover_letters',
            'cover_letter_sections'
        ]

        # Update all foreign key references
        for table in tables_with_profile_fk:
            connection.execute(
                text(f"UPDATE {table} SET profile_id = 1 WHERE profile_id = :old_id"),
                {"old_id": first_profile_id}
            )

        # Update the profile id itself
        connection.execute(
            text("UPDATE profiles SET id = 1 WHERE id = :old_id"),
            {"old_id": first_profile_id}
        )

        # Reset SQLite autoincrement sequence
        connection.execute(text("DELETE FROM sqlite_sequence WHERE name = 'profiles'"))
        connection.execute(text("INSERT INTO sqlite_sequence (name, seq) VALUES ('profiles', 1)"))


def downgrade() -> None:
    """
    Downgrade is not supported for this migration.

    Once profiles are consolidated, we cannot restore the deleted profiles
    as their data has been permanently removed.
    """
    raise NotImplementedError(
        "Downgrade not supported: deleted profile data cannot be restored. "
        "Restore from backup if you need to revert this migration."
    )
