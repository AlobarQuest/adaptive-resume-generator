"""Unit tests for Resume PDF Generator Service.

Tests cover:
- Service initialization
- Data loading and transformation
- PDF generation
- Preview and save functionality
- Template selection
- Error handling
"""

import pytest
import json
from io import BytesIO
from pathlib import Path
from datetime import datetime

from adaptive_resume.services.resume_pdf_generator import (
    ResumePDFGenerator,
    ResumePDFGeneratorError
)
from adaptive_resume.models.profile import Profile
from adaptive_resume.models.job import Job
from adaptive_resume.models.bullet_point import BulletPoint
from adaptive_resume.models.education import Education
from adaptive_resume.models.skill import Skill
from adaptive_resume.models.certification import Certification
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.models.tailored_resume import TailoredResumeModel
from adaptive_resume.pdf.template_registry import TemplateRegistry


@pytest.fixture
def pdf_generator(session):
    """Create PDF generator with test session."""
    return ResumePDFGenerator(session)


@pytest.fixture
def test_profile(session):
    """Create test profile with all data."""
    profile = Profile(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="(555) 123-4567",
        city="San Francisco",
        state="CA",
        linkedin_url="linkedin.com/in/johndoe",
        portfolio_url="johndoe.com",
        professional_summary="Experienced software engineer with 5+ years in web development."
    )
    session.add(profile)
    session.commit()
    return profile


@pytest.fixture
def test_job(session, test_profile):
    """Create test job."""
    from datetime import date
    job = Job(
        profile_id=test_profile.id,
        company_name="Tech Corp",
        job_title="Senior Software Engineer",
        location="San Francisco, CA",
        start_date=date(2020, 1, 15),
        end_date=date(2023, 12, 31),
        is_current=False
    )
    session.add(job)
    session.commit()
    return job


@pytest.fixture
def test_bullets(session, test_job):
    """Create test bullet points."""
    bullets = [
        BulletPoint(
            job_id=test_job.id,
            content="Developed scalable microservices architecture serving 1M+ users",
            display_order=1
        ),
        BulletPoint(
            job_id=test_job.id,
            content="Led team of 5 engineers in agile development process",
            display_order=2
        ),
        BulletPoint(
            job_id=test_job.id,
            content="Reduced deployment time by 50% through CI/CD automation",
            display_order=3
        )
    ]
    for bullet in bullets:
        session.add(bullet)
    session.commit()
    return bullets


@pytest.fixture
def test_education(session, test_profile):
    """Create test education."""
    from datetime import date
    from decimal import Decimal
    education = Education(
        profile_id=test_profile.id,
        degree="Bachelor of Science in Computer Science",
        field_of_study="Computer Science",
        institution="UC Berkeley",
        end_date=date(2018, 5, 15),
        gpa=Decimal("3.75")
    )
    session.add(education)
    session.commit()
    return education


@pytest.fixture
def test_skills(session, test_profile):
    """Create test skills."""
    skill_names = ["Python", "JavaScript", "React", "AWS", "Docker"]
    skills = []
    for name in skill_names:
        skill = Skill(
            profile_id=test_profile.id,
            skill_name=name,
            category="Technical"
        )
        skills.append(skill)
        session.add(skill)
    session.commit()
    return skills


@pytest.fixture
def test_certification(session, test_profile):
    """Create test certification."""
    from datetime import date
    cert = Certification(
        profile_id=test_profile.id,
        name="AWS Certified Solutions Architect",
        issuing_organization="Amazon Web Services",
        issue_date=date(2022, 3, 15),
        expiration_date=date(2025, 3, 15),
        credential_id="ABC123XYZ"
    )
    session.add(cert)
    session.commit()
    return cert


@pytest.fixture
def test_job_posting(session, test_profile):
    """Create test job posting."""
    job_posting = JobPosting(
        profile_id=test_profile.id,
        company_name="Target Company",
        job_title="Software Engineer",
        raw_text="Software engineer position...",
        requirements_json=json.dumps({
            "skills": ["Python", "AWS"],
            "experience_years": 5
        })
    )
    session.add(job_posting)
    session.commit()
    return job_posting


@pytest.fixture
def test_tailored_resume(session, test_profile, test_job_posting, test_bullets):
    """Create test tailored resume."""
    # Select first 2 bullets
    selected_ids = [test_bullets[0].id, test_bullets[1].id]

    tailored_resume = TailoredResumeModel(
        profile_id=test_profile.id,
        job_posting_id=test_job_posting.id,
        selected_accomplishment_ids=json.dumps(selected_ids),
        skill_coverage_json=json.dumps({"Python": True, "AWS": True}),
        coverage_percentage=0.85,
        gaps_json=json.dumps(["Docker"]),
        recommendations_json=json.dumps(["Add Docker experience"]),
        match_score=0.88
    )
    session.add(tailored_resume)
    session.commit()
    return tailored_resume


class TestResumePDFGeneratorInit:
    """Test suite for service initialization."""

    def test_init(self, session):
        """Test service initialization."""
        generator = ResumePDFGenerator(session)

        assert generator.session == session

    def test_list_available_templates(self, pdf_generator):
        """Test listing available templates."""
        # Ensure classic template is registered
        if not TemplateRegistry.is_registered("classic"):
            from adaptive_resume.pdf.templates.classic_template import ClassicTemplate, CLASSIC_SPEC
            TemplateRegistry.register("classic", ClassicTemplate, spec=CLASSIC_SPEC)

        templates = pdf_generator.list_available_templates()

        assert isinstance(templates, list)
        assert "classic" in templates


class TestResumePDFGeneratorDataLoading:
    """Test suite for data loading."""

    def test_load_tailored_resume_success(self, pdf_generator, test_tailored_resume):
        """Test loading tailored resume."""
        loaded = pdf_generator._load_tailored_resume(test_tailored_resume.id)

        assert loaded.id == test_tailored_resume.id
        assert loaded.profile is not None
        assert loaded.job_posting is not None

    def test_load_tailored_resume_not_found(self, pdf_generator):
        """Test loading non-existent tailored resume."""
        with pytest.raises(ResumePDFGeneratorError) as exc_info:
            pdf_generator._load_tailored_resume(99999)

        assert "not found" in str(exc_info.value)


class TestResumePDFGeneratorDataTransformation:
    """Test suite for data transformation."""

    def test_transform_profile(self, pdf_generator, test_profile):
        """Test profile transformation."""
        profile_data = pdf_generator._transform_profile(test_profile)

        assert profile_data['name'] == "John Doe"
        assert profile_data['email'] == "john.doe@example.com"
        assert profile_data['phone'] == "(555) 123-4567"
        assert profile_data['city'] == "San Francisco"
        assert profile_data['state'] == "CA"
        assert profile_data['linkedin_url'] == "linkedin.com/in/johndoe"
        assert profile_data['website_url'] == "johndoe.com"

    def test_transform_accomplishments(
        self,
        pdf_generator,
        test_tailored_resume,
        test_bullets
    ):
        """Test accomplishments transformation."""
        accomplishments = pdf_generator._transform_accomplishments(test_tailored_resume)

        assert len(accomplishments) == 2  # Only 2 selected
        assert accomplishments[0]['text'] in [b.content for b in test_bullets[:2]]
        assert accomplishments[0]['company_name'] == "Tech Corp"
        assert accomplishments[0]['job_title'] == "Senior Software Engineer"

    def test_transform_accomplishments_empty(self, pdf_generator, session, test_profile):
        """Test transformation with no selected accomplishments."""
        # Create tailored resume with no selections
        job_posting = JobPosting(
            profile_id=test_profile.id,
            company_name="Test",
            job_title="Engineer",
            raw_text="Test"
        )
        session.add(job_posting)
        session.commit()

        tailored_resume = TailoredResumeModel(
            profile_id=test_profile.id,
            job_posting_id=job_posting.id,
            selected_accomplishment_ids=json.dumps([])
        )
        session.add(tailored_resume)
        session.commit()

        accomplishments = pdf_generator._transform_accomplishments(tailored_resume)

        assert accomplishments == []

    def test_transform_education(self, pdf_generator, test_profile, test_education):
        """Test education transformation."""
        education_data = pdf_generator._transform_education(test_profile)

        assert len(education_data) == 1
        assert education_data[0]['degree'] == "Bachelor of Science in Computer Science"
        assert education_data[0]['institution'] == "UC Berkeley"
        assert education_data[0]['gpa'] == 3.75
        assert education_data[0]['city'] is None  # Education model doesn't have location
        assert education_data[0]['state'] is None

    def test_transform_skills(self, pdf_generator, test_profile, test_skills):
        """Test skills transformation."""
        skills_data = pdf_generator._transform_skills(test_profile)

        assert len(skills_data) == 5
        assert "Python" in skills_data
        assert "JavaScript" in skills_data
        assert "AWS" in skills_data

    def test_transform_certifications(
        self,
        pdf_generator,
        test_profile,
        test_certification
    ):
        """Test certifications transformation."""
        certs_data = pdf_generator._transform_certifications(test_profile)

        assert len(certs_data) == 1
        assert certs_data[0]['name'] == "AWS Certified Solutions Architect"
        assert certs_data[0]['issuing_organization'] == "Amazon Web Services"
        assert certs_data[0]['credential_id'] == "ABC123XYZ"


class TestResumePDFGeneratorGeneration:
    """Test suite for PDF generation."""

    def setup_method(self):
        """Ensure classic template is registered."""
        if not TemplateRegistry.is_registered("classic"):
            from adaptive_resume.pdf.templates.classic_template import ClassicTemplate, CLASSIC_SPEC
            TemplateRegistry.register("classic", ClassicTemplate, spec=CLASSIC_SPEC)

    def test_generate_pdf_basic(
        self,
        pdf_generator,
        test_tailored_resume,
        test_profile,
        test_bullets,
        test_education,
        test_skills,
        test_certification
    ):
        """Test basic PDF generation."""
        pdf_bytes = pdf_generator.generate_pdf(
            tailored_resume_id=test_tailored_resume.id,
            template_name="classic"
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert b'PDF' in pdf_bytes  # PDF signature

    def test_generate_pdf_with_summary(
        self,
        pdf_generator,
        test_tailored_resume,
        test_profile,
        test_bullets,
        test_education,
        test_skills,
        test_certification
    ):
        """Test PDF generation with custom summary."""
        custom_summary = "Custom professional summary for this role."

        pdf_bytes = pdf_generator.generate_pdf(
            tailored_resume_id=test_tailored_resume.id,
            template_name="classic",
            include_summary=True,
            summary_text=custom_summary
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_without_summary(
        self,
        pdf_generator,
        test_tailored_resume,
        test_profile,
        test_bullets,
        test_education,
        test_skills,
        test_certification
    ):
        """Test PDF generation without summary."""
        pdf_bytes = pdf_generator.generate_pdf(
            tailored_resume_id=test_tailored_resume.id,
            template_name="classic",
            include_summary=False
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_invalid_template(
        self,
        pdf_generator,
        test_tailored_resume
    ):
        """Test PDF generation with invalid template."""
        from adaptive_resume.pdf.template_registry import TemplateRegistryError

        with pytest.raises(TemplateRegistryError):
            pdf_generator.generate_pdf(
                tailored_resume_id=test_tailored_resume.id,
                template_name="nonexistent"
            )

    def test_generate_pdf_invalid_resume_id(self, pdf_generator):
        """Test PDF generation with invalid resume ID."""
        with pytest.raises(ResumePDFGeneratorError) as exc_info:
            pdf_generator.generate_pdf(
                tailored_resume_id=99999,
                template_name="classic"
            )

        assert "not found" in str(exc_info.value)


class TestResumePDFGeneratorPreview:
    """Test suite for preview functionality."""

    def setup_method(self):
        """Ensure classic template is registered."""
        if not TemplateRegistry.is_registered("classic"):
            from adaptive_resume.pdf.templates.classic_template import ClassicTemplate, CLASSIC_SPEC
            TemplateRegistry.register("classic", ClassicTemplate, spec=CLASSIC_SPEC)

    def test_preview_pdf(
        self,
        pdf_generator,
        test_tailored_resume,
        test_profile,
        test_bullets,
        test_education,
        test_skills,
        test_certification
    ):
        """Test PDF preview generation."""
        buffer = pdf_generator.preview_pdf(
            tailored_resume_id=test_tailored_resume.id,
            template_name="classic"
        )

        assert isinstance(buffer, BytesIO)
        pdf_bytes = buffer.getvalue()
        assert len(pdf_bytes) > 0
        assert b'PDF' in pdf_bytes


class TestResumePDFGeneratorSave:
    """Test suite for save functionality."""

    def setup_method(self):
        """Ensure classic template is registered."""
        if not TemplateRegistry.is_registered("classic"):
            from adaptive_resume.pdf.templates.classic_template import ClassicTemplate, CLASSIC_SPEC
            TemplateRegistry.register("classic", ClassicTemplate, spec=CLASSIC_SPEC)

    def test_save_pdf(
        self,
        pdf_generator,
        test_tailored_resume,
        test_profile,
        test_bullets,
        test_education,
        test_skills,
        test_certification,
        tmp_path
    ):
        """Test saving PDF to file."""
        output_path = tmp_path / "test_resume.pdf"

        result_path = pdf_generator.save_pdf(
            tailored_resume_id=test_tailored_resume.id,
            output_path=str(output_path),
            template_name="classic"
        )

        assert result_path == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify it's a valid PDF
        with open(output_path, 'rb') as f:
            content = f.read()
            assert b'PDF' in content

    def test_save_pdf_creates_directories(
        self,
        pdf_generator,
        test_tailored_resume,
        test_profile,
        test_bullets,
        test_education,
        test_skills,
        test_certification,
        tmp_path
    ):
        """Test saving PDF creates parent directories."""
        output_path = tmp_path / "nested" / "dir" / "test_resume.pdf"

        result_path = pdf_generator.save_pdf(
            tailored_resume_id=test_tailored_resume.id,
            output_path=str(output_path),
            template_name="classic"
        )

        assert result_path == output_path
        assert output_path.exists()
        assert output_path.parent.exists()


class TestResumePDFGeneratorPrivateMethods:
    """Test suite for private helper methods."""

    def setup_method(self):
        """Ensure classic template is registered."""
        if not TemplateRegistry.is_registered("classic"):
            from adaptive_resume.pdf.templates.classic_template import ClassicTemplate, CLASSIC_SPEC
            TemplateRegistry.register("classic", ClassicTemplate, spec=CLASSIC_SPEC)

    def test_generate_pdf_with_template(self, pdf_generator):
        """Test low-level PDF generation with template."""
        profile_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': None,
            'city': None,
            'state': None,
            'linkedin_url': None,
            'github_url': None,
            'website_url': None
        }

        pdf_bytes = pdf_generator._generate_pdf_with_template(
            template_name="classic",
            profile=profile_data,
            accomplishments=[],
            education=[],
            skills=[],
            certifications=[],
            options=None
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert b'PDF' in pdf_bytes

    def test_save_to_file(self, pdf_generator, tmp_path):
        """Test saving bytes to file."""
        test_bytes = b"test content"
        output_path = tmp_path / "test_file.txt"

        pdf_generator._save_to_file(test_bytes, str(output_path))

        assert output_path.exists()
        with open(output_path, 'rb') as f:
            assert f.read() == test_bytes
