"""
Unit tests for ResumeImporter service.

Tests cover:
- Profile creation and update
- Job import with bullet points
- Education import with date parsing
- Skill import with deduplication
- Certification import
- Date parsing and normalization
- GPA parsing
- Location parsing
- Error handling and transaction rollback
- Integration workflows
"""

import pytest
from datetime import date
from decimal import Decimal

from adaptive_resume.models import Profile, Job, BulletPoint, Education, Skill, Certification
from adaptive_resume.services.resume_importer import ResumeImporter, ResumeImportError
from adaptive_resume.services.resume_extractor import (
    ExtractedResume, ExtractedJob, ExtractedEducation, ExtractedCertification
)


class TestResumeImporterInit:
    """Test suite for ResumeImporter initialization."""

    def test_init_requires_session(self, session):
        """Test initialization with session."""
        importer = ResumeImporter(session)
        assert importer.session == session


class TestProfileCreation:
    """Test suite for profile creation."""

    def test_create_profile_basic(self, session):
        """Test creating a basic profile."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.email == "john.doe@example.com"
        assert profile.id is not None

    def test_create_profile_with_all_fields(self, session):
        """Test creating profile with all contact fields."""
        extracted = ExtractedResume(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="(555) 123-4567",
            location="San Francisco, CA",
            linkedin_url="https://linkedin.com/in/janesmith",
            github_url="https://github.com/janesmith"
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        assert profile.first_name == "Jane"
        assert profile.last_name == "Smith"
        assert profile.email == "jane.smith@example.com"
        assert profile.phone == "(555) 123-4567"
        assert profile.city == "San Francisco"
        assert profile.state == "CA"
        assert profile.linkedin_url == "https://linkedin.com/in/janesmith"
        assert profile.portfolio_url == "https://github.com/janesmith"

    def test_create_profile_missing_required_fields(self, session):
        """Test creating profile with missing required fields."""
        extracted = ExtractedResume(
            first_name="John",
            # Missing last_name
            email="john@example.com"
        )

        importer = ResumeImporter(session)

        with pytest.raises(ResumeImportError) as exc_info:
            importer.import_resume(extracted)

        assert "First name and last name are required" in str(exc_info.value)

    def test_create_profile_missing_email(self, session):
        """Test creating profile without email."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe"
            # Missing email
        )

        importer = ResumeImporter(session)

        with pytest.raises(ResumeImportError) as exc_info:
            importer.import_resume(extracted)

        assert "Email is required" in str(exc_info.value)


class TestProfileUpdate:
    """Test suite for profile updating."""

    def test_update_existing_profile(self, session):
        """Test updating an existing profile."""
        # Create initial profile
        profile = Profile(
            first_name="Old",
            last_name="Name",
            email="old@example.com"
        )
        session.add(profile)
        session.commit()

        # Update with extracted data
        extracted = ExtractedResume(
            first_name="New",
            last_name="Name",
            email="new@example.com",
            phone="123-456-7890"
        )

        importer = ResumeImporter(session)
        updated_profile, stats = importer.import_resume(extracted, profile_id=profile.id)

        assert updated_profile.id == profile.id
        assert updated_profile.first_name == "New"
        assert updated_profile.last_name == "Name"
        assert updated_profile.email == "new@example.com"
        assert updated_profile.phone == "123-456-7890"

    def test_update_profile_partial_fields(self, session):
        """Test updating profile with only some fields."""
        # Create initial profile
        profile = Profile(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="111-111-1111"
        )
        session.add(profile)
        session.commit()

        # Update with partial data (no phone)
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
            # No phone
        )

        importer = ResumeImporter(session)
        updated_profile, stats = importer.import_resume(extracted, profile_id=profile.id)

        # Phone should remain unchanged
        assert updated_profile.phone == "111-111-1111"

    def test_update_nonexistent_profile(self, session):
        """Test updating a profile that doesn't exist."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )

        importer = ResumeImporter(session)

        with pytest.raises(ResumeImportError) as exc_info:
            importer.import_resume(extracted, profile_id=9999)

        assert "not found" in str(exc_info.value)


class TestJobImport:
    """Test suite for job import."""

    def test_import_single_job(self, session):
        """Test importing a single job."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            jobs=[
                ExtractedJob(
                    company_name="Tech Corp",
                    job_title="Software Engineer",
                    location="San Francisco, CA",
                    start_date="Jan 2020",
                    end_date="Dec 2022",
                    is_current=False,
                    bullet_points=[
                        "Developed web applications",
                        "Led team of 5 engineers"
                    ]
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        assert stats['jobs_created'] == 1
        assert stats['bullet_points_created'] == 2
        assert len(profile.jobs) == 1

        job = profile.jobs[0]
        assert job.company_name == "Tech Corp"
        assert job.job_title == "Software Engineer"
        assert job.location == "San Francisco, CA"
        assert job.start_date == date(2020, 1, 1)
        assert job.end_date == date(2022, 12, 1)
        assert job.is_current is False
        assert len(job.bullet_points) == 2

    def test_import_multiple_jobs(self, session):
        """Test importing multiple jobs."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            jobs=[
                ExtractedJob(
                    company_name="Company A",
                    job_title="Engineer",
                    start_date="2020",
                    is_current=False
                ),
                ExtractedJob(
                    company_name="Company B",
                    job_title="Senior Engineer",
                    start_date="2022",
                    is_current=True
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        assert stats['jobs_created'] == 2
        assert len(profile.jobs) == 2
        assert profile.jobs[0].display_order == 0
        assert profile.jobs[1].display_order == 1

    def test_import_current_job(self, session):
        """Test importing a current job (no end date)."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            jobs=[
                ExtractedJob(
                    company_name="Current Corp",
                    job_title="Lead Engineer",
                    start_date="2023-06",
                    end_date="Present",
                    is_current=True
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        job = profile.jobs[0]
        assert job.is_current is True
        assert job.end_date is None
        assert job.start_date == date(2023, 6, 1)

    def test_import_job_missing_required_fields(self, session):
        """Test importing job with missing required fields."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            jobs=[
                ExtractedJob(
                    company_name="",  # Missing
                    job_title="Engineer",
                    start_date="2020"
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        # Should skip invalid job
        assert stats['jobs_created'] == 0
        assert len(stats['errors']) > 0
        assert "Missing company name" in stats['errors'][0]


class TestEducationImport:
    """Test suite for education import."""

    def test_import_single_education(self, session):
        """Test importing a single education entry."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            education=[
                ExtractedEducation(
                    school_name="UC Berkeley",
                    degree_type="Bachelor of Science",
                    major="Computer Science",
                    graduation_date="2019",
                    gpa="3.75"
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        assert stats['education_created'] == 1
        assert len(profile.education) == 1

        edu = profile.education[0]
        assert edu.institution == "UC Berkeley"
        assert edu.degree == "Bachelor of Science"
        assert edu.field_of_study == "Computer Science"
        assert edu.end_date == date(2019, 1, 1)
        assert edu.gpa == Decimal("3.75")

    def test_import_multiple_education(self, session):
        """Test importing multiple education entries."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            education=[
                ExtractedEducation(
                    school_name="Harvard",
                    degree_type="MBA",
                    graduation_date="2022"
                ),
                ExtractedEducation(
                    school_name="MIT",
                    degree_type="BS",
                    major="Engineering",
                    graduation_date="2018"
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        assert stats['education_created'] == 2
        assert len(profile.education) == 2

    def test_import_education_missing_school_name(self, session):
        """Test importing education without school name."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            education=[
                ExtractedEducation(
                    school_name="",  # Missing
                    degree_type="BS"
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        # Should skip invalid education
        assert stats['education_created'] == 0
        assert len(stats['errors']) > 0


class TestSkillImport:
    """Test suite for skill import with deduplication."""

    def test_import_skills(self, session):
        """Test importing skills."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            skills=["Python", "JavaScript", "React", "SQL"]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        assert stats['skills_created'] == 4
        assert len(profile.skills) == 4

        skill_names = [s.skill_name for s in profile.skills]
        assert "Python" in skill_names
        assert "JavaScript" in skill_names
        assert "React" in skill_names
        assert "SQL" in skill_names

    def test_import_skills_deduplication(self, session):
        """Test that duplicate skills are not created."""
        # Create profile with existing skills
        profile = Profile(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        session.add(profile)
        session.flush()

        skill1 = Skill(profile_id=profile.id, skill_name="Python")
        skill2 = Skill(profile_id=profile.id, skill_name="JavaScript")
        session.add_all([skill1, skill2])
        session.commit()

        # Try to import overlapping skills
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            skills=["Python", "React", "JavaScript", "SQL"]  # Python and JavaScript already exist
        )

        importer = ResumeImporter(session)
        updated_profile, stats = importer.import_resume(extracted, profile_id=profile.id)

        # Should only create React and SQL (Python and JavaScript already exist)
        assert stats['skills_created'] == 2

        skill_names = [s.skill_name for s in updated_profile.skills]
        assert len(skill_names) == 4  # Total: 2 existing + 2 new

    def test_import_skills_case_insensitive_deduplication(self, session):
        """Test that skill deduplication is case-insensitive."""
        # Create profile with existing skills
        profile = Profile(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        session.add(profile)
        session.flush()

        skill = Skill(profile_id=profile.id, skill_name="Python")
        session.add(skill)
        session.commit()

        # Try to import "python" (lowercase)
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            skills=["python", "JavaScript"]  # "python" should be skipped
        )

        importer = ResumeImporter(session)
        updated_profile, stats = importer.import_resume(extracted, profile_id=profile.id)

        # Should only create JavaScript
        assert stats['skills_created'] == 1

        skill_names = [s.skill_name for s in updated_profile.skills]
        assert len(skill_names) == 2


class TestCertificationImport:
    """Test suite for certification import."""

    def test_import_single_certification(self, session):
        """Test importing a single certification."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            certifications=[
                ExtractedCertification(
                    name="AWS Certified Solutions Architect",
                    issuing_organization="Amazon Web Services",
                    issue_date="2022-06",
                    expiration_date="2025-06"
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        assert stats['certifications_created'] == 1
        assert len(profile.certifications) == 1

        cert = profile.certifications[0]
        assert cert.name == "AWS Certified Solutions Architect"
        assert cert.issuing_organization == "Amazon Web Services"
        assert cert.issue_date == date(2022, 6, 1)
        assert cert.expiration_date == date(2025, 6, 1)

    def test_import_multiple_certifications(self, session):
        """Test importing multiple certifications."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            certifications=[
                ExtractedCertification(
                    name="PMP",
                    issuing_organization="PMI"
                ),
                ExtractedCertification(
                    name="CISSP",
                    issuing_organization="ISC2"
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        assert stats['certifications_created'] == 2
        assert len(profile.certifications) == 2

    def test_import_certification_missing_name(self, session):
        """Test importing certification without name."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            certifications=[
                ExtractedCertification(
                    name="",  # Missing
                    issuing_organization="Some Org"
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        # Should skip invalid certification
        assert stats['certifications_created'] == 0
        assert len(stats['errors']) > 0


class TestDateParsing:
    """Test suite for date parsing."""

    def test_parse_date_various_formats(self, session):
        """Test parsing various date formats."""
        importer = ResumeImporter(session)

        # Year only
        assert importer._parse_date("2020") == date(2020, 1, 1)

        # Month and year
        assert importer._parse_date("Jan 2020") == date(2020, 1, 1)
        assert importer._parse_date("January 2020") == date(2020, 1, 1)
        assert importer._parse_date("Dec 2022") == date(2022, 12, 1)

        # ISO format
        assert importer._parse_date("2020-06") == date(2020, 6, 1)
        assert importer._parse_date("2020-06-15") == date(2020, 6, 15)

        # Slash format
        assert importer._parse_date("06/2020") == date(2020, 6, 1)
        assert importer._parse_date("06/15/2020") == date(2020, 6, 15)

    def test_parse_date_present(self, session):
        """Test parsing 'Present' and similar keywords."""
        importer = ResumeImporter(session)

        assert importer._parse_date("Present") is None
        assert importer._parse_date("present") is None
        assert importer._parse_date("Current") is None
        assert importer._parse_date("Now") is None

    def test_parse_date_invalid(self, session):
        """Test parsing invalid dates."""
        importer = ResumeImporter(session)

        # Should extract year if possible
        assert importer._parse_date("Graduated in 2020") == date(2020, 1, 1)

        # Should return None for unparseable dates
        assert importer._parse_date("Invalid") is None
        assert importer._parse_date("") is None
        assert importer._parse_date(None) is None


class TestLocationParsing:
    """Test suite for location parsing."""

    def test_parse_location_city_state(self, session):
        """Test parsing 'City, State' format."""
        importer = ResumeImporter(session)

        city, state = importer._parse_location("San Francisco, CA")
        assert city == "San Francisco"
        assert state == "CA"

        city, state = importer._parse_location("New York, NY")
        assert city == "New York"
        assert state == "NY"

    def test_parse_location_city_only(self, session):
        """Test parsing city-only location."""
        importer = ResumeImporter(session)

        city, state = importer._parse_location("Seattle")
        assert city == "Seattle"
        assert state is None

    def test_parse_location_empty(self, session):
        """Test parsing empty location."""
        importer = ResumeImporter(session)

        city, state = importer._parse_location("")
        assert city is None
        assert state is None

        city, state = importer._parse_location(None)
        assert city is None
        assert state is None


class TestGPAParsing:
    """Test suite for GPA parsing."""

    def test_parse_gpa_decimal(self, session):
        """Test parsing decimal GPA."""
        importer = ResumeImporter(session)

        assert importer._parse_gpa("3.75") == Decimal("3.75")
        assert importer._parse_gpa("4.0") == Decimal("4.0")
        assert importer._parse_gpa("2.5") == Decimal("2.5")

    def test_parse_gpa_with_scale(self, session):
        """Test parsing GPA with scale (e.g., '3.75/4.0')."""
        importer = ResumeImporter(session)

        assert importer._parse_gpa("3.75/4.0") == Decimal("3.75")
        assert importer._parse_gpa("3.5 / 4.0") == Decimal("3.5")

    def test_parse_gpa_out_of_range(self, session):
        """Test parsing GPA out of range."""
        importer = ResumeImporter(session)

        # Should reject values outside 0.0-4.0
        assert importer._parse_gpa("5.0") is None
        assert importer._parse_gpa("-1.0") is None

    def test_parse_gpa_invalid(self, session):
        """Test parsing invalid GPA."""
        importer = ResumeImporter(session)

        assert importer._parse_gpa("invalid") is None
        assert importer._parse_gpa("") is None
        assert importer._parse_gpa(None) is None


class TestTransactionHandling:
    """Test suite for transaction handling and error recovery."""

    def test_rollback_on_error(self, session):
        """Test that transaction is rolled back on error."""
        # This would require a more complex scenario to truly test rollback
        # For now, we test that invalid data doesn't create partial records

        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            jobs=[
                ExtractedJob(
                    company_name="Valid Company",
                    job_title="Engineer",
                    start_date="2020"  # Valid
                ),
                ExtractedJob(
                    company_name="",  # Invalid - missing name
                    job_title="Manager",
                    start_date="2021"
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        # Valid job should be created, invalid should be skipped
        assert stats['jobs_created'] == 1
        assert len(stats['errors']) > 0


class TestIntegrationWorkflow:
    """Integration tests for complete resume import workflow."""

    def test_full_resume_import(self, session):
        """Test importing a complete resume with all sections."""
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="(555) 123-4567",
            location="San Francisco, CA",
            linkedin_url="https://linkedin.com/in/johndoe",
            github_url="https://github.com/johndoe",
            jobs=[
                ExtractedJob(
                    company_name="Tech Corp",
                    job_title="Senior Software Engineer",
                    location="San Francisco, CA",
                    start_date="Jan 2020",
                    end_date="Present",
                    is_current=True,
                    bullet_points=[
                        "Led development of microservices architecture",
                        "Improved system performance by 40%"
                    ]
                ),
                ExtractedJob(
                    company_name="StartupXYZ",
                    job_title="Software Engineer",
                    start_date="2018",
                    end_date="2019",
                    is_current=False,
                    bullet_points=[
                        "Built REST APIs"
                    ]
                )
            ],
            education=[
                ExtractedEducation(
                    school_name="UC Berkeley",
                    degree_type="BS",
                    major="Computer Science",
                    graduation_date="2018",
                    gpa="3.75"
                )
            ],
            skills=["Python", "JavaScript", "React", "Docker", "AWS"],
            certifications=[
                ExtractedCertification(
                    name="AWS Certified Developer",
                    issuing_organization="Amazon Web Services",
                    issue_date="2021",
                    expiration_date="2024"
                )
            ]
        )

        importer = ResumeImporter(session)
        profile, stats = importer.import_resume(extracted)

        # Verify profile
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.email == "john.doe@example.com"
        assert profile.city == "San Francisco"
        assert profile.state == "CA"

        # Verify stats
        assert stats['jobs_created'] == 2
        assert stats['bullet_points_created'] == 3
        assert stats['education_created'] == 1
        assert stats['skills_created'] == 5
        assert stats['certifications_created'] == 1

        # Verify relationships
        assert len(profile.jobs) == 2
        assert len(profile.education) == 1
        assert len(profile.skills) == 5
        assert len(profile.certifications) == 1

        # Verify job details
        current_job = [j for j in profile.jobs if j.is_current][0]
        assert current_job.company_name == "Tech Corp"
        assert len(current_job.bullet_points) == 2

    def test_update_existing_profile_with_new_data(self, session):
        """Test updating an existing profile with new resume data."""
        # Create initial profile
        profile = Profile(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        session.add(profile)
        session.commit()

        # Import resume with additional data
        extracted = ExtractedResume(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="123-456-7890",
            jobs=[
                ExtractedJob(
                    company_name="New Company",
                    job_title="Engineer",
                    start_date="2023"
                )
            ],
            skills=["Python", "Java"]
        )

        importer = ResumeImporter(session)
        updated_profile, stats = importer.import_resume(extracted, profile_id=profile.id)

        # Profile should be updated
        assert updated_profile.id == profile.id
        assert updated_profile.phone == "123-456-7890"
        assert stats['jobs_created'] == 1
        assert stats['skills_created'] == 2
