"""Unit tests for the CertificationService."""

from datetime import date

import pytest

from adaptive_resume.services.certification_service import (
    CertificationService,
    CertificationNotFoundError,
    CertificationValidationError,
)
from adaptive_resume.services.profile_service import ProfileService


def test_create_list_and_update_certification(session):
    profile_service = ProfileService(session)
    profile = profile_service.create_profile(
        first_name="Alex",
        last_name="Jones",
        email="alex.jones@example.com",
    )

    service = CertificationService(session)
    certification = service.create_certification(
        profile_id=profile.id,
        name="AWS Solutions Architect",
        issuing_organization="Amazon",
        issue_date=date(2022, 1, 1),
        expiration_date=date(2025, 1, 1),
        credential_id="AWS-123",
    )

    assert certification.id is not None
    assert certification.name == "AWS Solutions Architect"

    certifications = service.list_certifications_for_profile(profile.id)
    assert len(certifications) == 1

    updated = service.update_certification(certification.id, credential_url="https://aws.amazon.com")
    assert updated.credential_url == "https://aws.amazon.com"

    service.reorder_certifications(profile.id, [certification.id])

    service.delete_certification(certification.id)
    with pytest.raises(CertificationNotFoundError):
        service.get_certification_by_id(certification.id)


def test_create_certification_validates_input(session):
    profile_service = ProfileService(session)
    profile = profile_service.create_profile(
        first_name="Riley",
        last_name="Nguyen",
        email="riley.nguyen@example.com",
    )

    service = CertificationService(session)

    with pytest.raises(CertificationValidationError):
        service.create_certification(profile.id, name="", issuing_organization="AWS")

    with pytest.raises(CertificationValidationError):
        service.create_certification(
            profile.id,
            name="Azure Architect",
            issuing_organization="Microsoft",
            issue_date=date(2021, 5, 1),
            expiration_date=date(2020, 5, 1),
        )
