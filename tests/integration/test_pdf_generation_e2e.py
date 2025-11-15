"""End-to-end integration tests for PDF generation workflow.

Tests the complete workflow from TailoredResume creation to PDF generation
with all templates and varying content amounts.
"""

import pytest
import json
import time
from pathlib import Path
from datetime import date
from decimal import Decimal

from adaptive_resume.models.profile import Profile
from adaptive_resume.models.job import Job
from adaptive_resume.models.bullet_point import BulletPoint
from adaptive_resume.models.education import Education
from adaptive_resume.models.skill import Skill
from adaptive_resume.models.certification import Certification
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.models.tailored_resume import TailoredResumeModel
from adaptive_resume.services.resume_pdf_generator import ResumePDFGenerator

# Import templates to trigger registration
from adaptive_resume.pdf.templates import (
    ClassicTemplate,
    ModernTemplate,
    CompactTemplate,
    ATSFriendlyTemplate,
)


@pytest.fixture
def pdf_generator(session):
    """Create PDF generator with test session."""
    return ResumePDFGenerator(session)


@pytest.fixture
def complete_profile(session):
    """Create a profile with complete data."""
    profile = Profile(
        first_name="Sarah",
        last_name="Johnson",
        email="sarah.johnson@email.com",
        phone="(555) 987-6543",
        city="Seattle",
        state="WA",
        linkedin_url="linkedin.com/in/sarahjohnson",
        portfolio_url="sarahjohnson.dev",
        professional_summary=(
            "Senior Software Engineer with 8+ years of experience building scalable "
            "web applications and leading cross-functional teams. Expertise in Python, "
            "React, and cloud infrastructure. Passionate about creating elegant solutions "
            "to complex problems."
        )
    )
    session.add(profile)
    session.commit()
    return profile


@pytest.fixture
def extensive_jobs(session, complete_profile):
    """Create extensive job history (5 jobs)."""
    jobs_data = [
        {
            "company_name": "Tech Giant Inc",
            "job_title": "Senior Software Engineer",
            "location": "Seattle, WA",
            "start_date": date(2020, 1, 1),
            "end_date": None,
            "is_current": True,
            "bullets": [
                "Led development of microservices architecture serving 10M+ users",
                "Reduced API response time by 40% through database optimization",
                "Mentored team of 5 junior engineers in agile development practices",
                "Implemented CI/CD pipeline reducing deployment time by 60%",
                "Designed and deployed Kubernetes-based infrastructure"
            ]
        },
        {
            "company_name": "StartupXYZ",
            "job_title": "Software Engineer",
            "location": "Remote",
            "start_date": date(2018, 6, 1),
            "end_date": date(2019, 12, 31),
            "is_current": False,
            "bullets": [
                "Built real-time analytics dashboard processing 1M+ events/day",
                "Developed REST APIs using Python Flask and PostgreSQL",
                "Integrated third-party payment processing (Stripe, PayPal)",
                "Implemented automated testing suite with 85% code coverage"
            ]
        },
        {
            "company_name": "Enterprise Corp",
            "job_title": "Full Stack Developer",
            "location": "San Francisco, CA",
            "start_date": date(2016, 3, 1),
            "end_date": date(2018, 5, 31),
            "is_current": False,
            "bullets": [
                "Developed customer-facing web portal using React and Node.js",
                "Migrated legacy monolith to microservices architecture",
                "Collaborated with UX team to improve user engagement by 35%",
                "Implemented OAuth2 authentication and role-based access control"
            ]
        },
        {
            "company_name": "Digital Agency",
            "job_title": "Junior Developer",
            "location": "Portland, OR",
            "start_date": date(2015, 1, 1),
            "end_date": date(2016, 2, 28),
            "is_current": False,
            "bullets": [
                "Built responsive websites for 20+ clients using HTML/CSS/JavaScript",
                "Integrated CMS platforms (WordPress, Drupal) with custom themes",
                "Optimized site performance achieving 90+ PageSpeed scores"
            ]
        },
        {
            "company_name": "University of Washington",
            "job_title": "Web Development Intern",
            "location": "Seattle, WA",
            "start_date": date(2014, 6, 1),
            "end_date": date(2014, 12, 31),
            "is_current": False,
            "bullets": [
                "Assisted in maintenance of department websites",
                "Created interactive JavaScript visualizations for research data",
                "Learned version control and collaborative development workflows"
            ]
        }
    ]

    jobs = []
    for job_data in jobs_data:
        bullets = job_data.pop("bullets")
        job = Job(profile_id=complete_profile.id, **job_data)
        session.add(job)
        session.flush()

        for i, bullet_text in enumerate(bullets):
            bullet = BulletPoint(
                job_id=job.id,
                content=bullet_text,
                display_order=i + 1
            )
            session.add(bullet)

        jobs.append(job)

    session.commit()
    return jobs


@pytest.fixture
def extensive_education(session, complete_profile):
    """Create education records."""
    education_data = [
        {
            "degree": "Master of Science in Computer Science",
            "field_of_study": "Computer Science",
            "institution": "University of Washington",
            "end_date": date(2015, 6, 15),
            "gpa": Decimal("3.85")
        },
        {
            "degree": "Bachelor of Science in Computer Engineering",
            "field_of_study": "Computer Engineering",
            "institution": "Oregon State University",
            "end_date": date(2013, 6, 15),
            "gpa": Decimal("3.72")
        }
    ]

    education_records = []
    for edu_data in education_data:
        edu = Education(profile_id=complete_profile.id, **edu_data)
        session.add(edu)
        education_records.append(edu)

    session.commit()
    return education_records


@pytest.fixture
def extensive_skills(session, complete_profile):
    """Create extensive skills list."""
    skill_names = [
        "Python", "JavaScript", "React", "Node.js", "TypeScript",
        "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
        "Redis", "GraphQL", "REST APIs", "Microservices", "CI/CD",
        "Git", "Agile", "Test-Driven Development", "System Design", "Leadership"
    ]

    skills = []
    for skill_name in skill_names:
        skill = Skill(
            profile_id=complete_profile.id,
            skill_name=skill_name,
            category="Technical"
        )
        skills.append(skill)
        session.add(skill)

    session.commit()
    return skills


@pytest.fixture
def certifications(session, complete_profile):
    """Create certifications."""
    certs_data = [
        {
            "name": "AWS Certified Solutions Architect - Professional",
            "issuing_organization": "Amazon Web Services",
            "issue_date": date(2022, 8, 15),
            "expiration_date": date(2025, 8, 15),
            "credential_id": "AWS-PSA-12345"
        },
        {
            "name": "Certified Kubernetes Administrator (CKA)",
            "issuing_organization": "Cloud Native Computing Foundation",
            "issue_date": date(2021, 5, 20),
            "expiration_date": date(2024, 5, 20),
            "credential_id": "CKA-67890"
        }
    ]

    certifications = []
    for cert_data in certs_data:
        cert = Certification(profile_id=complete_profile.id, **cert_data)
        session.add(cert)
        certifications.append(cert)

    session.commit()
    return certifications


@pytest.fixture
def sample_job_posting(session, complete_profile):
    """Create a sample job posting."""
    job_posting = JobPosting(
        profile_id=complete_profile.id,
        company_name="Cloud Solutions Inc",
        job_title="Senior Software Engineer",
        raw_text="We are seeking a Senior Software Engineer...",
        requirements_json=json.dumps({
            "skills": ["Python", "AWS", "Kubernetes", "React", "PostgreSQL"],
            "experience_years": 7
        })
    )
    session.add(job_posting)
    session.commit()
    return job_posting


@pytest.fixture
def tailored_resume_extensive(
    session,
    complete_profile,
    sample_job_posting,
    extensive_jobs
):
    """Create tailored resume with extensive accomplishments."""
    # Get all bullet points from all jobs
    bullets = session.query(BulletPoint).filter(
        BulletPoint.job_id.in_([job.id for job in extensive_jobs])
    ).all()

    # Select top 10 bullets
    selected_ids = [bullet.id for bullet in bullets[:10]]

    tailored_resume = TailoredResumeModel(
        profile_id=complete_profile.id,
        job_posting_id=sample_job_posting.id,
        selected_accomplishment_ids=json.dumps(selected_ids),
        skill_coverage_json=json.dumps({
            "Python": True,
            "AWS": True,
            "Kubernetes": True,
            "React": True,
            "PostgreSQL": True
        }),
        coverage_percentage=1.0,
        gaps_json=json.dumps([]),
        recommendations_json=json.dumps([
            "Strong match! Highlight your AWS and Kubernetes expertise."
        ]),
        match_score=0.92
    )
    session.add(tailored_resume)
    session.commit()
    return tailored_resume


class TestPDFGenerationE2E:
    """End-to-end tests for PDF generation."""

    def test_generate_pdf_all_templates_extensive_data(
        self,
        pdf_generator,
        tailored_resume_extensive,
        complete_profile,
        extensive_education,
        extensive_skills,
        certifications,
        tmp_path
    ):
        """Test PDF generation with all templates using extensive data."""
        templates = ["classic", "modern", "compact", "ats-friendly"]

        for template_name in templates:
            # Generate PDF
            start_time = time.time()
            pdf_bytes = pdf_generator.generate_pdf(
                tailored_resume_id=tailored_resume_extensive.id,
                template_name=template_name,
                include_summary=True
            )
            generation_time = time.time() - start_time

            # Verify PDF was generated
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            assert b'PDF' in pdf_bytes  # PDF signature

            # Verify file size is reasonable (not too large)
            file_size_kb = len(pdf_bytes) / 1024
            assert file_size_kb < 500, f"{template_name} PDF too large: {file_size_kb:.1f}KB"

            # Verify generation time is acceptable
            assert generation_time < 5.0, f"{template_name} took too long: {generation_time:.2f}s"

            # Save to file for manual inspection
            output_path = tmp_path / f"extensive_{template_name}.pdf"
            saved_path = pdf_generator.save_pdf(
                tailored_resume_id=tailored_resume_extensive.id,
                output_path=str(output_path),
                template_name=template_name
            )

            assert saved_path.exists()
            assert saved_path.stat().st_size > 0

            print(f"[OK] {template_name.upper()}: {file_size_kb:.1f}KB, {generation_time:.3f}s")

    def test_generate_pdf_minimal_data(self, session, pdf_generator, tmp_path):
        """Test PDF generation with minimal data."""
        # Create minimal profile
        profile = Profile(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        session.add(profile)
        session.commit()

        # Create minimal job
        job = Job(
            profile_id=profile.id,
            company_name="Company",
            job_title="Developer",
            location="City, ST",
            start_date=date(2023, 1, 1),
            is_current=True
        )
        session.add(job)
        session.flush()

        # Create one bullet
        bullet = BulletPoint(
            job_id=job.id,
            content="Developed software",
            display_order=1
        )
        session.add(bullet)
        session.commit()

        # Create job posting
        job_posting = JobPosting(
            profile_id=profile.id,
            company_name="Target",
            job_title="Engineer",
            raw_text="Job description"
        )
        session.add(job_posting)
        session.commit()

        # Create tailored resume
        tailored_resume = TailoredResumeModel(
            profile_id=profile.id,
            job_posting_id=job_posting.id,
            selected_accomplishment_ids=json.dumps([bullet.id])
        )
        session.add(tailored_resume)
        session.commit()

        # Test all templates with minimal data
        for template_name in ["classic", "modern", "compact", "ats-friendly"]:
            pdf_bytes = pdf_generator.generate_pdf(
                tailored_resume_id=tailored_resume.id,
                template_name=template_name,
                include_summary=False
            )

            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            assert b'PDF' in pdf_bytes

            # Save for inspection
            output_path = tmp_path / f"minimal_{template_name}.pdf"
            pdf_generator.save_pdf(
                tailored_resume_id=tailored_resume.id,
                output_path=str(output_path),
                template_name=template_name,
                include_summary=False
            )

            assert output_path.exists()

    def test_generate_pdf_with_custom_summary(
        self,
        pdf_generator,
        tailored_resume_extensive,
        tmp_path
    ):
        """Test PDF generation with custom summary text."""
        custom_summary = (
            "Passionate software engineer with proven track record of delivering "
            "high-impact solutions. Seeking to leverage my expertise in cloud "
            "architecture and team leadership to drive innovation."
        )

        pdf_bytes = pdf_generator.generate_pdf(
            tailored_resume_id=tailored_resume_extensive.id,
            template_name="classic",
            include_summary=True,
            summary_text=custom_summary
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

        # Save for inspection
        output_path = tmp_path / "custom_summary.pdf"
        pdf_generator.save_pdf(
            tailored_resume_id=tailored_resume_extensive.id,
            output_path=str(output_path),
            template_name="classic",
            include_summary=True,
            summary_text=custom_summary
        )

        assert output_path.exists()

    def test_pdf_performance_benchmark(
        self,
        pdf_generator,
        tailored_resume_extensive
    ):
        """Benchmark PDF generation performance."""
        iterations = 5
        templates = ["classic", "modern", "compact", "ats-friendly"]

        for template_name in templates:
            times = []
            for _ in range(iterations):
                start = time.time()
                pdf_bytes = pdf_generator.generate_pdf(
                    tailored_resume_id=tailored_resume_extensive.id,
                    template_name=template_name,
                    include_summary=True
                )
                elapsed = time.time() - start
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            # All generation should be under 2 seconds
            assert avg_time < 2.0, f"{template_name} average too slow: {avg_time:.2f}s"

            print(f"{template_name}: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")


__all__ = ["TestPDFGenerationE2E"]
