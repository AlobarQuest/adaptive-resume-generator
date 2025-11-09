"""Unit tests for the EducationService."""

from datetime import date

import pytest

from adaptive_resume.services.education_service import (
    EducationService,
    EducationNotFoundError,
    EducationValidationError,
)
from adaptive_resume.services.profile_service import ProfileService


def test_create_list_and_update_education(session):
    profile_service = ProfileService(session)
    profile = profile_service.create_profile(
        first_name="Jamie",
        last_name="Reed",
        email="jamie.reed@example.com",
    )

    service = EducationService(session)
    education = service.create_education(
        profile_id=profile.id,
        institution="Georgia Tech",
        degree="BS Computer Science",
        start_date=date(2010, 8, 1),
        end_date=date(2014, 5, 1),
        gpa=3.9,
    )

    assert education.id is not None
    assert education.institution == "Georgia Tech"

    entries = service.list_education_for_profile(profile.id)
    assert len(entries) == 1

    updated = service.update_education(education.id, honors="Magna Cum Laude", gpa=3.95)
    assert updated.honors == "Magna Cum Laude"
    assert float(updated.gpa) == 3.95

    service.reorder_education(profile.id, [education.id])

    service.delete_education(education.id)
    with pytest.raises(EducationNotFoundError):
        service.get_education_by_id(education.id)


def test_create_education_validates_input(session):
    profile_service = ProfileService(session)
    profile = profile_service.create_profile(
        first_name="Morgan",
        last_name="Lee",
        email="morgan.lee@example.com",
    )

    service = EducationService(session)

    with pytest.raises(EducationValidationError):
        service.create_education(profile.id, institution="", degree="BBA")

    with pytest.raises(EducationValidationError):
        service.create_education(
            profile.id,
            institution="State University",
            degree="MBA",
            start_date=date(2020, 1, 1),
            end_date=date(2019, 1, 1),
        )

    with pytest.raises(EducationValidationError):
        service.update_education(
            service.create_education(
                profile.id,
                institution="State University",
                degree="MBA",
            ).id,
            gpa=4.5,
        )
