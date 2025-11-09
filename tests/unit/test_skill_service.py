"""Unit tests for the SkillService."""

import pytest

from adaptive_resume.services.profile_service import ProfileService
from adaptive_resume.services.skill_service import (
    SkillService,
    SkillNotFoundError,
    SkillValidationError,
)


def test_create_list_and_update_skill(session):
    profile_service = ProfileService(session)
    profile = profile_service.create_profile(
        first_name="Sam",
        last_name="Taylor",
        email="sam.taylor@example.com",
    )

    service = SkillService(session)
    skill = service.create_skill(
        profile_id=profile.id,
        skill_name="Python",
        category="Programming Languages",
        proficiency_level="Expert",
        years_experience=7.5,
    )

    assert skill.id is not None
    assert skill.proficiency_level == "Expert"

    skills = service.list_skills_for_profile(profile.id)
    assert len(skills) == 1

    updated = service.update_skill(skill.id, proficiency_level="Advanced", years_experience=8.0)
    assert updated.proficiency_level == "Advanced"
    assert float(updated.years_experience) == 8.0

    service.reorder_skills(profile.id, [skill.id])

    service.delete_skill(skill.id)
    with pytest.raises(SkillNotFoundError):
        service.get_skill_by_id(skill.id)


def test_create_skill_validates_input(session):
    profile_service = ProfileService(session)
    profile = profile_service.create_profile(
        first_name="Sky",
        last_name="Wong",
        email="sky.wong@example.com",
    )

    service = SkillService(session)

    with pytest.raises(SkillValidationError):
        service.create_skill(profile.id, skill_name="", proficiency_level="Expert")

    with pytest.raises(SkillValidationError):
        service.create_skill(profile.id, skill_name="Leadership", proficiency_level="Master")

    with pytest.raises(SkillValidationError):
        service.create_skill(profile.id, skill_name="Leadership", years_experience=-1)
