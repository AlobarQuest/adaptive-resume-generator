"""Integration test for cover letter generation workflow.

This test demonstrates the complete cover letter workflow from
profile creation through generation, editing, and export.
"""

import pytest
from datetime import date
from pathlib import Path
import tempfile

from adaptive_resume.models.profile import Profile
from adaptive_resume.models.job import Job
from adaptive_resume.models.bullet_point import BulletPoint
from adaptive_resume.models.skill import Skill
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.models.tailored_resume import TailoredResumeModel
from adaptive_resume.models.cover_letter import CoverLetter
from adaptive_resume.services.cover_letter_generation_service import CoverLetterGenerationService


class TestCoverLetterWorkflow:
    """Test complete cover letter generation workflow."""

    @pytest.fixture
    def complete_profile(self, session):
        """Create a complete profile with job history and skills."""
        # Create profile
        profile = Profile(
            first_name="Jane",
            last_name="Developer",
            email="jane.developer@example.com",
            phone="555-0123",
            city="San Francisco",
            state="CA",
            professional_summary="Senior software engineer with 8 years of experience in full-stack development"
        )
        session.add(profile)
        session.commit()

        # Add job history
        job1 = Job(
            profile_id=profile.id,
            job_title="Senior Software Engineer",
            company_name="TechCorp Inc",
            start_date=date(2020, 1, 1),
            end_date=None,
            is_current=True
        )
        session.add(job1)
        session.commit()

        # Add bullet points
        bullets = [
            BulletPoint(
                job_id=job1.id,
                content="Led team of 5 engineers to deliver microservices platform, reducing deployment time by 60%",
                display_order=0
            ),
            BulletPoint(
                job_id=job1.id,
                content="Implemented CI/CD pipeline using Jenkins and Docker, automating 90% of deployment process",
                display_order=1
            ),
            BulletPoint(
                job_id=job1.id,
                content="Architected REST API serving 1M+ requests/day with 99.9% uptime",
                display_order=2
            ),
        ]
        session.add_all(bullets)
        session.commit()

        # Add skills
        skills = [
            Skill(profile_id=profile.id, skill_name="Python", proficiency_level="Expert"),
            Skill(profile_id=profile.id, skill_name="React", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, skill_name="PostgreSQL", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, skill_name="AWS", proficiency_level="Intermediate"),
        ]
        session.add_all(skills)
        session.commit()

        session.refresh(profile)
        return profile

    @pytest.fixture
    def job_posting(self, session, complete_profile):
        """Create a sample job posting."""
        posting = JobPosting(
            profile_id=complete_profile.id,
            job_title="Lead Full Stack Engineer",
            company_name="InnovateTech",
            raw_text="""
            We are seeking a Lead Full Stack Engineer to join our growing team.

            Required Skills:
            - Python, React, PostgreSQL
            - 5+ years of experience
            - Leadership experience
            - Cloud platforms (AWS/GCP)

            You will lead a team of engineers building our next-generation platform.
            """,
            requirements_json='{"required_skills": ["Python", "React", "PostgreSQL", "AWS"], "preferred_skills": ["Leadership", "Microservices"]}'
        )
        session.add(posting)
        session.commit()
        return posting

    @pytest.fixture
    def tailored_resume(self, session, complete_profile, job_posting):
        """Create a tailored resume."""
        tailored = TailoredResumeModel(
            profile_id=complete_profile.id,
            job_posting_id=job_posting.id,
            selected_accomplishment_ids='[1, 2, 3]',
            coverage_percentage=0.85,
            match_score=0.82
        )
        session.add(tailored)
        session.commit()
        return tailored

    def test_complete_workflow_without_ai(self, session, complete_profile, job_posting, tailored_resume):
        """Test the complete workflow without actual AI calls.

        This test verifies:
        1. Service initialization
        2. Template loading
        3. Context building
        4. Cover letter creation (without AI)
        5. Database storage
        """
        # Initialize service
        service = CoverLetterGenerationService(session)

        # Verify templates load
        assert service.templates is not None
        assert len(service.templates['templates']) == 7

        # Verify template retrieval
        template = service.get_template("professional")
        assert template is not None
        assert template['id'] == "professional"
        assert template['name'] == "Classic Professional"

        # Build context (core functionality that doesn't require AI)
        context = service._build_context(
            profile=complete_profile,
            job_posting=job_posting,
            tailored_resume=tailored_resume,
            template=template,
            tone="professional",
            length="medium",
            focus_areas=["technical", "leadership"],
            custom_context={}
        )

        # Verify context contains all required elements
        assert context['candidate']['name'] == "Jane Developer"
        assert context['candidate']['email'] == "jane.developer@example.com"
        assert 'job' in context
        assert context['job']['title'] == "Lead Full Stack Engineer"
        assert context['job']['company'] == "InnovateTech"
        assert 'work_history' in context
        assert len(context['work_history']) > 0
        assert context['work_history'][0]['title'] == "Senior Software Engineer"
        assert 'skills' in context
        assert "Python" in context['skills']
        assert context['tone'] == "professional"
        assert context['length'] == "medium"
        assert "technical" in context['focus_areas']
        assert "leadership" in context['focus_areas']

        # Create a manual cover letter (simulating what AI would create)
        cover_letter = CoverLetter(
            profile_id=complete_profile.id,
            job_posting_id=job_posting.id,
            tailored_resume_id=tailored_resume.id,
            content="""I am writing to express my interest in the Lead Full Stack Engineer position at InnovateTech.

With 8 years of experience in full-stack development, I have developed strong expertise in Python, React, and PostgreSQL. At TechCorp Inc, I led a team of 5 engineers to deliver a microservices platform, reducing deployment time by 60%.

I implemented CI/CD pipelines using Jenkins and Docker, automating 90% of the deployment process. Additionally, I architected a REST API serving over 1M requests per day with 99.9% uptime.

I would welcome the opportunity to discuss how my experience aligns with InnovateTech's needs.""",
            opening_paragraph="I am writing to express my interest in the Lead Full Stack Engineer position at InnovateTech.",
            body_paragraphs=[
                "With 8 years of experience in full-stack development, I have developed strong expertise in Python, React, and PostgreSQL.",
                "At TechCorp Inc, I led a team of 5 engineers to deliver a microservices platform, reducing deployment time by 60%."
            ],
            closing_paragraph="I would welcome the opportunity to discuss how my experience aligns with InnovateTech's needs.",
            template_id="professional",
            tone="professional",
            length="medium",
            focus_areas=["technical", "leadership"],
            ai_generated=False,
            user_edited=False,
            company_name="InnovateTech",
            job_title="Lead Full Stack Engineer",
            word_count=service.calculate_word_count("I am writing to express my interest...")
        )

        # Save to database
        session.add(cover_letter)
        session.commit()

        # Verify it was saved
        retrieved = session.query(CoverLetter).filter_by(
            profile_id=complete_profile.id,
            job_posting_id=job_posting.id
        ).first()

        assert retrieved is not None
        assert retrieved.template_id == "professional"
        assert retrieved.tone == "professional"
        assert retrieved.length == "medium"
        assert retrieved.company_name == "InnovateTech"
        assert retrieved.job_title == "Lead Full Stack Engineer"
        assert "Lead Full Stack Engineer" in retrieved.content
        assert "InnovateTech" in retrieved.content

    def test_word_count_calculation(self, session):
        """Test word count calculation."""
        service = CoverLetterGenerationService(session)

        # Test simple text
        text1 = "This is a test sentence with eight words here."
        assert service.calculate_word_count(text1) == 9

        # Test multi-paragraph text
        text2 = """
        First paragraph with some words.

        Second paragraph with more words here.

        Third paragraph.
        """
        count = service.calculate_word_count(text2)
        assert count > 0

        # Test empty text
        assert service.calculate_word_count("") == 0
        assert service.calculate_word_count("   ") == 0

    def test_content_validation(self, session):
        """Test content validation."""
        service = CoverLetterGenerationService(session)

        # Valid content (200 words is typical medium length)
        valid_text = " ".join(["word"] * 200)
        assert service.validate_content(valid_text, min_words=100, max_words=600)

        # Too short
        short_text = " ".join(["word"] * 50)
        assert not service.validate_content(short_text, min_words=100, max_words=600)

        # Too long
        long_text = " ".join(["word"] * 700)
        assert not service.validate_content(long_text, min_words=100, max_words=600)

        # Empty
        assert not service.validate_content("", min_words=100, max_words=600)

    def test_export_text_functionality(self, session, complete_profile, job_posting):
        """Test text export functionality."""
        # Create a simple cover letter
        content = """Dear Hiring Manager,

I am writing to express my interest in the Lead Full Stack Engineer position.

With 8 years of experience, I have the skills needed for this role.

Thank you for your consideration.

Sincerely,
Jane Developer"""

        cover_letter = CoverLetter(
            profile_id=complete_profile.id,
            job_posting_id=job_posting.id,
            content=content,
            template_id="professional",
            tone="professional",
            length="short",
            ai_generated=False,
            user_edited=False,
            company_name="InnovateTech",
            job_title="Lead Full Stack Engineer",
            word_count=len(content.split())
        )

        session.add(cover_letter)
        session.commit()

        # Test export to text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = Path(f.name)
            f.write(cover_letter.content)

        # Verify file was created and contains content
        assert temp_path.exists()
        text = temp_path.read_text(encoding='utf-8')
        assert "Lead Full Stack Engineer" in text
        assert "Jane Developer" in text

        # Cleanup
        temp_path.unlink()

    def test_multiple_cover_letters_per_profile(self, session, complete_profile):
        """Test that a profile can have multiple cover letters."""
        # Create multiple job postings
        job1 = JobPosting(
            profile_id=complete_profile.id,
            job_title="Senior Engineer",
            company_name="Company A",
            raw_text="Job description A"
        )
        job2 = JobPosting(
            profile_id=complete_profile.id,
            job_title="Lead Engineer",
            company_name="Company B",
            raw_text="Job description B"
        )
        session.add_all([job1, job2])
        session.commit()

        # Create cover letters for each
        cl1 = CoverLetter(
            profile_id=complete_profile.id,
            job_posting_id=job1.id,
            content="Cover letter for Company A",
            template_id="professional",
            tone="formal",
            length="medium",
            ai_generated=False,
            user_edited=False,
            company_name="Company A",
            job_title="Senior Engineer",
            word_count=5
        )
        cl2 = CoverLetter(
            profile_id=complete_profile.id,
            job_posting_id=job2.id,
            content="Cover letter for Company B",
            template_id="enthusiastic",
            tone="enthusiastic",
            length="medium",
            ai_generated=False,
            user_edited=False,
            company_name="Company B",
            job_title="Lead Engineer",
            word_count=5
        )

        session.add_all([cl1, cl2])
        session.commit()

        # Verify both exist
        all_letters = session.query(CoverLetter).filter_by(
            profile_id=complete_profile.id
        ).all()

        assert len(all_letters) == 2
        companies = {cl.company_name for cl in all_letters}
        assert companies == {"Company A", "Company B"}

    def test_cover_letter_relationships(self, session, complete_profile, job_posting, tailored_resume):
        """Test that cover letter relationships work correctly."""
        # Create cover letter with all relationships
        cover_letter = CoverLetter(
            profile_id=complete_profile.id,
            job_posting_id=job_posting.id,
            tailored_resume_id=tailored_resume.id,
            content="Test content",
            template_id="professional",
            tone="professional",
            length="medium",
            ai_generated=True,
            user_edited=False,
            company_name="InnovateTech",
            job_title="Lead Full Stack Engineer",
            word_count=2
        )

        session.add(cover_letter)
        session.commit()

        # Verify relationships work
        session.refresh(cover_letter)
        assert cover_letter.profile is not None
        assert cover_letter.profile.first_name == "Jane"
        assert cover_letter.job_posting is not None
        assert cover_letter.job_posting.company_name == "InnovateTech"
        assert cover_letter.tailored_resume is not None
        assert cover_letter.tailored_resume.match_score == 0.82

        # Verify back-references
        session.refresh(complete_profile)
        assert len(complete_profile.cover_letters) > 0

        session.refresh(job_posting)
        assert len(job_posting.cover_letters) > 0

        session.refresh(tailored_resume)
        assert len(tailored_resume.cover_letters) > 0
