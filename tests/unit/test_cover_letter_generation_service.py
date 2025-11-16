"""Unit tests for CoverLetterGenerationService."""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date

from adaptive_resume.services.cover_letter_generation_service import CoverLetterGenerationService
from adaptive_resume.models.cover_letter import CoverLetter
from adaptive_resume.models.profile import Profile
from adaptive_resume.models.job import Job
from adaptive_resume.models.bullet_point import BulletPoint
from adaptive_resume.models.skill import Skill
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.models.tailored_resume import TailoredResumeModel


class TestCoverLetterGenerationService:
    """Test CoverLetterGenerationService functionality."""

    @pytest.fixture
    def service(self, session):
        """Create service instance with mocked API key."""
        with patch('adaptive_resume.services.cover_letter_generation_service.Settings') as mock_settings:
            mock_settings_instance = Mock()
            mock_settings_instance.get_api_key.return_value = "test-api-key"
            mock_settings.return_value = mock_settings_instance

            service = CoverLetterGenerationService(session)
            return service

    @pytest.fixture
    def service_no_api_key(self, session):
        """Create service instance without API key."""
        with patch('adaptive_resume.services.cover_letter_generation_service.Settings') as mock_settings:
            mock_settings_instance = Mock()
            mock_settings_instance.get_api_key.return_value = None
            mock_settings.return_value = mock_settings_instance

            service = CoverLetterGenerationService(session)
            return service

    @pytest.fixture
    def sample_profile(self, session):
        """Create sample profile for testing."""
        profile = Profile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="555-1234",
            professional_summary="Experienced software engineer with 5 years in web development"
        )
        session.add(profile)
        session.commit()

        # Add a job
        job = Job(
            profile_id=profile.id,
            job_title="Senior Software Engineer",
            company_name="Tech Corp",
            start_date=date(2020, 1, 1),
            end_date=None
        )
        session.add(job)
        session.commit()

        # Add bullet points
        bullet1 = BulletPoint(
            job_id=job.id,
            content="Led team of 5 engineers to deliver microservices platform, reducing deployment time by 60%",
            display_order=0
        )
        bullet2 = BulletPoint(
            job_id=job.id,
            content="Implemented CI/CD pipeline using Jenkins and Docker, automating 90% of deployment process",
            display_order=1
        )
        session.add_all([bullet1, bullet2])
        session.commit()

        # Add skills
        skills = [
            Skill(profile_id=profile.id, skill_name="Python", proficiency_level="Expert"),
            Skill(profile_id=profile.id, skill_name="React", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, skill_name="AWS", proficiency_level="Intermediate"),
        ]
        session.add_all(skills)
        session.commit()

        # Refresh to load relationships
        session.refresh(profile)
        return profile

    @pytest.fixture
    def sample_job_posting(self, session, sample_profile):
        """Create sample job posting for testing."""
        job_posting = JobPosting(
            profile_id=sample_profile.id,
            job_title="Full Stack Engineer",
            company_name="StartupCo",
            raw_text="We're looking for a Full Stack Engineer with Python and React experience...",
            requirements_json='{"required_skills": ["Python", "React", "PostgreSQL"], "preferred_skills": ["AWS", "Docker", "TypeScript"]}'
        )
        session.add(job_posting)
        session.commit()
        return job_posting

    @pytest.fixture
    def sample_tailored_resume(self, session, sample_profile, sample_job_posting):
        """Create sample tailored resume for testing."""
        tailored = TailoredResumeModel(
            profile_id=sample_profile.id,
            job_posting_id=sample_job_posting.id,
            selected_accomplishment_ids=json.dumps([1, 2]),
            coverage_percentage=0.85,
            match_score=0.78
        )
        session.add(tailored)
        session.commit()
        return tailored

    # Template Loading Tests

    def test_load_templates_success(self, service):
        """Test successful template loading."""
        templates = service.load_templates()

        assert templates is not None
        assert 'templates' in templates
        assert 'tone_guidelines' in templates
        assert 'length_guidelines' in templates
        assert len(templates['templates']) == 7  # We created 7 templates

    def test_get_template_exists(self, service):
        """Test getting an existing template."""
        template = service.get_template("professional")

        assert template is not None
        assert template['id'] == "professional"
        assert template['name'] == "Classic Professional"
        assert template['tone'] == "formal"

    def test_get_template_not_exists(self, service):
        """Test getting a non-existent template."""
        template = service.get_template("nonexistent")
        assert template is None

    def test_get_all_template_ids(self, service):
        """Test that all expected templates exist."""
        expected_ids = [
            "professional",
            "enthusiastic",
            "technical",
            "career_change",
            "referral",
            "cold_application",
            "networking_followup"
        ]

        for template_id in expected_ids:
            template = service.get_template(template_id)
            assert template is not None, f"Template {template_id} not found"

    # Service Availability Tests

    def test_service_enabled_with_api_key(self, service):
        """Test service is enabled when API key is present."""
        assert service.enabled is True
        assert service.is_available is True
        assert service.client is not None

    def test_service_disabled_without_api_key(self, service_no_api_key):
        """Test service is disabled when API key is missing."""
        assert service_no_api_key.enabled is False
        assert service_no_api_key.is_available is False
        assert service_no_api_key.client is None

    # Context Building Tests

    def test_build_context_basic(self, service, sample_profile):
        """Test context building with minimal inputs."""
        template = service.get_template("professional")

        context = service._build_context(
            profile=sample_profile,
            job_posting=None,
            tailored_resume=None,
            template=template,
            tone="formal",
            length="medium",
            focus_areas=["technical"],
            custom_context={}
        )

        assert context is not None
        assert context['tone'] == "formal"
        assert context['length'] == "medium"
        assert context['focus_areas'] == ["technical"]
        assert 'candidate' in context
        assert context['candidate']['name'] == "John Doe"
        assert context['candidate']['email'] == "john.doe@example.com"

    def test_build_context_with_job_posting(self, service, sample_profile, sample_job_posting):
        """Test context building includes job posting information."""
        template = service.get_template("professional")

        context = service._build_context(
            profile=sample_profile,
            job_posting=sample_job_posting,
            tailored_resume=None,
            template=template,
            tone="professional",
            length="medium",
            focus_areas=[],
            custom_context={}
        )

        assert 'job' in context
        assert context['job']['title'] == "Full Stack Engineer"
        assert context['job']['company'] == "StartupCo"
        assert "Python" in context['job']['required_skills']
        assert "React" in context['job']['required_skills']

    def test_build_context_includes_work_history(self, service, sample_profile):
        """Test context includes work history from profile."""
        template = service.get_template("professional")

        context = service._build_context(
            profile=sample_profile,
            job_posting=None,
            tailored_resume=None,
            template=template,
            tone="professional",
            length="medium",
            focus_areas=[],
            custom_context={}
        )

        assert 'work_history' in context
        assert len(context['work_history']) > 0
        assert context['work_history'][0]['title'] == "Senior Software Engineer"
        assert context['work_history'][0]['company'] == "Tech Corp"
        assert len(context['work_history'][0]['accomplishments']) > 0

    def test_build_context_includes_skills(self, service, sample_profile):
        """Test context includes skills from profile."""
        template = service.get_template("professional")

        context = service._build_context(
            profile=sample_profile,
            job_posting=None,
            tailored_resume=None,
            template=template,
            tone="professional",
            length="medium",
            focus_areas=[],
            custom_context={}
        )

        assert 'skills' in context
        assert len(context['skills']) > 0
        assert "Python" in context['skills']
        assert "React" in context['skills']

    def test_build_context_with_tailored_resume(
        self,
        service,
        sample_profile,
        sample_job_posting,
        sample_tailored_resume
    ):
        """Test context includes tailored resume information."""
        template = service.get_template("professional")

        context = service._build_context(
            profile=sample_profile,
            job_posting=sample_job_posting,
            tailored_resume=sample_tailored_resume,
            template=template,
            tone="professional",
            length="medium",
            focus_areas=[],
            custom_context={}
        )

        assert 'tailored_resume' in context
        assert context['tailored_resume']['match_score'] == 0.78
        assert context['tailored_resume']['coverage_percentage'] == 0.85

    def test_build_context_custom_context_merged(self, service, sample_profile):
        """Test custom context is merged into final context."""
        template = service.get_template("professional")

        context = service._build_context(
            profile=sample_profile,
            job_posting=None,
            tailored_resume=None,
            template=template,
            tone="professional",
            length="medium",
            focus_areas=[],
            custom_context={'custom_key': 'custom_value', 'referral_name': 'Jane Smith'}
        )

        assert context['custom_key'] == 'custom_value'
        assert context['referral_name'] == 'Jane Smith'

    # Prompt Building Tests

    def test_build_opening_prompt(self, service, sample_profile):
        """Test opening prompt generation."""
        template = service.get_template("professional")
        context = service._build_context(
            profile=sample_profile,
            job_posting=None,
            tailored_resume=None,
            template=template,
            tone="formal",
            length="medium",
            focus_areas=["technical"],
            custom_context={}
        )

        prompt = service._build_opening_prompt(template, context)

        assert prompt is not None
        assert "John Doe" in prompt
        assert "formal" in prompt.lower()
        assert "technical" in prompt.lower()
        assert "opening paragraph" in prompt.lower()

    def test_build_body_prompt(self, service, sample_profile, sample_job_posting):
        """Test body paragraphs prompt generation."""
        template = service.get_template("professional")
        context = service._build_context(
            profile=sample_profile,
            job_posting=sample_job_posting,
            tailored_resume=None,
            template=template,
            tone="professional",
            length="medium",
            focus_areas=["technical", "results"],
            custom_context={}
        )

        prompt = service._build_body_prompt(template, context, num_paragraphs=2)

        assert prompt is not None
        assert "2" in prompt  # Number of paragraphs
        assert "StartupCo" in prompt  # Company name
        assert "Full Stack Engineer" in prompt  # Job title
        assert "technical" in prompt.lower()
        assert "results" in prompt.lower()

    def test_build_closing_prompt(self, service, sample_profile, sample_job_posting):
        """Test closing prompt generation."""
        template = service.get_template("professional")
        context = service._build_context(
            profile=sample_profile,
            job_posting=sample_job_posting,
            tailored_resume=None,
            template=template,
            tone="formal",
            length="medium",
            focus_areas=[],
            custom_context={}
        )

        prompt = service._build_closing_prompt(template, context)

        assert prompt is not None
        assert "StartupCo" in prompt
        assert "formal" in prompt.lower()
        assert "closing paragraph" in prompt.lower()

    # AI Generation Tests (Mocked)

    def test_generate_cover_letter_without_api_key(self, service_no_api_key, sample_profile):
        """Test generation fails gracefully without API key."""
        with pytest.raises(ValueError, match="AI generation is not enabled"):
            service_no_api_key.generate_cover_letter(
                profile=sample_profile,
                template_id="professional"
            )

    def test_generate_cover_letter_invalid_template(self, service, sample_profile):
        """Test generation fails with invalid template."""
        with pytest.raises(ValueError, match="Template not found"):
            service.generate_cover_letter(
                profile=sample_profile,
                template_id="nonexistent"
            )

    @patch('adaptive_resume.services.cover_letter_generation_service.Anthropic')
    def test_generate_cover_letter_success(self, mock_anthropic_class, service, sample_profile, sample_job_posting):
        """Test successful cover letter generation."""
        # Mock AI responses
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        service.client = mock_client

        # Mock opening response
        opening_response = Mock()
        opening_response.content = [Mock(text="I am writing to express my strong interest in the Full Stack Engineer position at StartupCo.")]

        # Mock body response (JSON)
        body_response = Mock()
        body_response.content = [Mock(text=json.dumps({
            "paragraphs": [
                "With 5 years of experience in web development, I have developed strong expertise in Python and React.",
                "In my current role at Tech Corp, I led a team of 5 engineers to deliver a microservices platform."
            ]
        }))]

        # Mock closing response
        closing_response = Mock()
        closing_response.content = [Mock(text="I would welcome the opportunity to discuss how my experience aligns with StartupCo's needs.")]

        # Set up mock to return different responses based on call order
        mock_client.messages.create.side_effect = [opening_response, body_response, closing_response]

        # Generate cover letter
        cover_letter = service.generate_cover_letter(
            profile=sample_profile,
            job_posting=sample_job_posting,
            template_id="professional",
            tone="formal",
            length="medium",
            focus_areas=["technical", "leadership"]
        )

        # Verify cover letter was created
        assert cover_letter is not None
        assert isinstance(cover_letter, CoverLetter)
        assert cover_letter.profile_id == sample_profile.id
        assert cover_letter.job_posting_id == sample_job_posting.id
        assert cover_letter.template_id == "professional"
        assert cover_letter.tone == "formal"
        assert cover_letter.length == "medium"
        assert cover_letter.focus_areas == ["technical", "leadership"]
        assert cover_letter.ai_generated is True
        assert cover_letter.ai_model == "claude-sonnet-4-20250514"
        assert cover_letter.user_edited is False
        assert cover_letter.company_name == "StartupCo"
        assert cover_letter.job_title == "Full Stack Engineer"

        # Verify content
        assert "express my strong interest" in cover_letter.content
        assert "5 years of experience" in cover_letter.content
        assert "welcome the opportunity" in cover_letter.content

        # Verify sections are stored separately
        assert cover_letter.opening_paragraph is not None
        assert cover_letter.body_paragraphs is not None
        assert len(cover_letter.body_paragraphs) == 2
        assert cover_letter.closing_paragraph is not None

        # Verify word count
        assert cover_letter.word_count > 0

        # Verify AI was called 3 times (opening, body, closing)
        assert mock_client.messages.create.call_count == 3

    @patch('adaptive_resume.services.cover_letter_generation_service.Anthropic')
    def test_generate_cover_letter_uses_template_default_tone(
        self,
        mock_anthropic_class,
        service,
        sample_profile
    ):
        """Test generation uses template's default tone when not specified."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        service.client = mock_client

        # Mock responses (opening, body as JSON, closing)
        opening_response = Mock(content=[Mock(text="Opening paragraph.")])
        body_response = Mock(content=[Mock(text=json.dumps({"paragraphs": ["Body paragraph 1.", "Body paragraph 2."]}))])
        closing_response = Mock(content=[Mock(text="Closing paragraph.")])
        mock_client.messages.create.side_effect = [opening_response, body_response, closing_response]

        # Generate without specifying tone (should use template default)
        cover_letter = service.generate_cover_letter(
            profile=sample_profile,
            template_id="enthusiastic"  # Default tone is "enthusiastic"
        )

        assert cover_letter.tone == "enthusiastic"

    # Utility Tests

    def test_calculate_word_count(self, service):
        """Test word count calculation."""
        text = "This is a test sentence with eight words total."
        count = service.calculate_word_count(text)
        assert count == 9

    def test_calculate_word_count_empty(self, service):
        """Test word count with empty text."""
        assert service.calculate_word_count("") == 0
        assert service.calculate_word_count("   ") == 0

    def test_validate_content_valid(self, service):
        """Test content validation with valid content."""
        # Create text with ~200 words (within range)
        text = " ".join(["word"] * 200)
        assert service.validate_content(text, min_words=100, max_words=600) is True

    def test_validate_content_too_short(self, service):
        """Test content validation with too-short content."""
        text = " ".join(["word"] * 50)
        assert service.validate_content(text, min_words=100, max_words=600) is False

    def test_validate_content_too_long(self, service):
        """Test content validation with too-long content."""
        text = " ".join(["word"] * 700)
        assert service.validate_content(text, min_words=100, max_words=600) is False

    def test_validate_content_empty(self, service):
        """Test content validation with empty content."""
        assert service.validate_content("", min_words=100, max_words=600) is False
        assert service.validate_content("   ", min_words=100, max_words=600) is False

    def test_assemble_cover_letter(self, service):
        """Test cover letter assembly from sections."""
        opening = "I am writing to apply for this position."
        body = ["This is the first body paragraph.", "This is the second body paragraph."]
        closing = "I look forward to hearing from you."

        assembled = service._assemble_cover_letter(opening, body, closing)

        assert "I am writing to apply" in assembled
        assert "first body paragraph" in assembled
        assert "second body paragraph" in assembled
        assert "look forward to hearing" in assembled

        # Check proper paragraph separation (double newlines)
        assert "\n\n" in assembled

    # Enhancement Tests

    @patch('adaptive_resume.services.cover_letter_generation_service.Anthropic')
    def test_enhance_section(self, mock_anthropic_class, service):
        """Test section enhancement."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        service.client = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Enhanced version of the text.")]
        mock_client.messages.create.return_value = mock_response

        original = "Original text here."
        enhanced = service.enhance_section(
            text=original,
            instructions="Make it more enthusiastic"
        )

        assert enhanced == "Enhanced version of the text."
        assert mock_client.messages.create.call_count == 1

    def test_enhance_section_without_api_key(self, service_no_api_key):
        """Test enhancement returns original when API not available."""
        original = "Original text here."
        enhanced = service_no_api_key.enhance_section(
            text=original,
            instructions="Make it better"
        )

        assert enhanced == original  # Should return original unchanged

    @patch('adaptive_resume.services.cover_letter_generation_service.Anthropic')
    def test_enhance_section_with_error(self, mock_anthropic_class, service):
        """Test enhancement returns original on error."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        service.client = mock_client

        # Mock an error
        mock_client.messages.create.side_effect = Exception("API Error")

        original = "Original text here."
        enhanced = service.enhance_section(
            text=original,
            instructions="Make it better"
        )

        assert enhanced == original  # Should return original on error

    # Regeneration Tests

    @patch('adaptive_resume.services.cover_letter_generation_service.Anthropic')
    def test_regenerate_section_opening(
        self,
        mock_anthropic_class,
        service,
        session,
        sample_profile,
        sample_job_posting
    ):
        """Test regenerating the opening section."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        service.client = mock_client

        # Create a cover letter in DB
        cover_letter = CoverLetter(
            profile_id=sample_profile.id,
            job_posting_id=sample_job_posting.id,
            content="Full content here.",
            opening_paragraph="Old opening.",
            body_paragraphs=["Body paragraph 1.", "Body paragraph 2."],
            closing_paragraph="Old closing.",
            template_id="professional",
            tone="formal",
            length="medium",
            ai_generated=True,
            ai_model="claude-sonnet-4-20250514",
            user_edited=False,
            word_count=50
        )
        session.add(cover_letter)
        session.commit()

        # Mock AI response
        mock_response = Mock()
        mock_response.content = [Mock(text="New opening paragraph.")]
        mock_client.messages.create.return_value = mock_response

        # Regenerate opening
        new_opening = service.regenerate_section(
            cover_letter=cover_letter,
            section="opening"
        )

        assert new_opening == "New opening paragraph."
        assert new_opening != "Old opening."

    def test_regenerate_section_invalid(self, service, session, sample_profile):
        """Test regeneration fails with invalid section."""
        cover_letter = CoverLetter(
            profile_id=sample_profile.id,
            content="Full content.",
            template_id="professional",
            tone="formal",
            length="medium",
            ai_generated=True,
            ai_model="claude-sonnet-4-20250514",
            user_edited=False,
            word_count=50
        )
        session.add(cover_letter)
        session.commit()

        with pytest.raises(ValueError, match="Invalid section"):
            service.regenerate_section(
                cover_letter=cover_letter,
                section="invalid_section"
            )

    # Integration Tests

    def test_service_initialization_creates_client_with_api_key(self, session):
        """Test service properly initializes Anthropic client when API key is present."""
        with patch('adaptive_resume.services.cover_letter_generation_service.Settings') as mock_settings:
            with patch('adaptive_resume.services.cover_letter_generation_service.Anthropic') as mock_anthropic:
                mock_settings_instance = Mock()
                mock_settings_instance.get_api_key.return_value = "test-api-key"
                mock_settings.return_value = mock_settings_instance

                service = CoverLetterGenerationService(session)

                # Verify Anthropic was called with the API key
                mock_anthropic.assert_called_once_with(api_key="test-api-key")
                assert service.enabled is True

    def test_service_initialization_without_api_key(self, session):
        """Test service properly handles missing API key."""
        with patch('adaptive_resume.services.cover_letter_generation_service.Settings') as mock_settings:
            mock_settings_instance = Mock()
            mock_settings_instance.get_api_key.return_value = None
            mock_settings.return_value = mock_settings_instance

            service = CoverLetterGenerationService(session)

            assert service.enabled is False
            assert service.client is None

    def test_templates_file_path_correct(self, service):
        """Test that templates file path is correct."""
        assert service.TEMPLATES_FILE.exists()
        assert service.TEMPLATES_FILE.name == "cover_letter_templates.json"
