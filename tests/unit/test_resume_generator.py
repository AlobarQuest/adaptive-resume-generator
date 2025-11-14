"""
Unit tests for ResumeGenerator service.

Tests cover:
- Tailored resume generation
- Skill coverage analysis
- Gap identification
- Recommendation generation
- Match score calculation
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import date, datetime
from adaptive_resume.services.resume_generator import (
    ResumeGenerator,
    TailoredResume,
    ResumeGeneratorError,
)
from adaptive_resume.services.nlp_analyzer import JobRequirements
from adaptive_resume.services.matching_engine import ScoredAccomplishment


class TestTailoredResume:
    """Test suite for TailoredResume dataclass."""

    def test_tailored_resume_defaults(self):
        """Test TailoredResume with default values."""
        resume = TailoredResume(profile_id=1)

        assert resume.profile_id == 1
        assert resume.job_posting_id is None
        assert resume.selected_accomplishments == []
        assert resume.skill_coverage == {}
        assert resume.coverage_percentage == 0.0
        assert resume.gaps == []
        assert resume.recommendations == []
        assert isinstance(resume.created_at, datetime)

    def test_tailored_resume_with_values(self):
        """Test TailoredResume with specific values."""
        accomplishments = [
            ScoredAccomplishment(
                bullet_id=1,
                bullet_text="Test",
                final_score=0.8
            )
        ]

        resume = TailoredResume(
            profile_id=1,
            job_posting_id=5,
            selected_accomplishments=accomplishments,
            skill_coverage={"Python": True, "AWS": False},
            coverage_percentage=0.5,
            gaps=["AWS"],
            recommendations=["Add more AWS experience"],
            job_title="Software Engineer",
            company_name="TechCorp"
        )

        assert resume.profile_id == 1
        assert resume.job_posting_id == 5
        assert len(resume.selected_accomplishments) == 1
        assert resume.coverage_percentage == 0.5
        assert "AWS" in resume.gaps
        assert resume.job_title == "Software Engineer"


class TestResumeGeneratorInit:
    """Test suite for ResumeGenerator initialization."""

    def test_init_default(self):
        """Test initialization with default matching engine."""
        generator = ResumeGenerator()

        assert generator.matching_engine is not None

    def test_init_custom_engine(self):
        """Test initialization with custom matching engine."""
        custom_engine = Mock()
        generator = ResumeGenerator(matching_engine=custom_engine)

        assert generator.matching_engine == custom_engine


class TestResumeGeneratorSkillCoverage:
    """Test suite for skill coverage analysis."""

    def test_analyze_skill_coverage_all_covered(self):
        """Test skill coverage when all required skills are covered."""
        generator = ResumeGenerator()

        selected = [
            ScoredAccomplishment(
                bullet_id=1,
                bullet_text="Test",
                matched_skills=["Python", "SQL"]
            )
        ]

        requirements = JobRequirements(
            required_skills=["Python", "SQL"],
            preferred_skills=["AWS"]
        )

        coverage, pct = generator._analyze_skill_coverage(selected, requirements)

        assert coverage["Python"] is True
        assert coverage["SQL"] is True
        assert pct == 1.0  # 100% coverage

    def test_analyze_skill_coverage_partial(self):
        """Test skill coverage with partial match."""
        generator = ResumeGenerator()

        selected = [
            ScoredAccomplishment(
                bullet_id=1,
                bullet_text="Test",
                matched_skills=["Python"]
            )
        ]

        requirements = JobRequirements(
            required_skills=["Python", "SQL", "AWS"],
            preferred_skills=[]
        )

        coverage, pct = generator._analyze_skill_coverage(selected, requirements)

        assert coverage["Python"] is True
        assert coverage["SQL"] is False
        assert coverage["AWS"] is False
        assert pct == pytest.approx(1/3)  # 33% coverage

    def test_analyze_skill_coverage_none(self):
        """Test skill coverage with no matches."""
        generator = ResumeGenerator()

        selected = [
            ScoredAccomplishment(
                bullet_id=1,
                bullet_text="Test",
                matched_skills=[]
            )
        ]

        requirements = JobRequirements(
            required_skills=["Python", "SQL"],
            preferred_skills=[]
        )

        coverage, pct = generator._analyze_skill_coverage(selected, requirements)

        assert coverage["Python"] is False
        assert coverage["SQL"] is False
        assert pct == 0.0

    def test_analyze_skill_coverage_empty_requirements(self):
        """Test skill coverage with no requirements."""
        generator = ResumeGenerator()

        selected = [
            ScoredAccomplishment(
                bullet_id=1,
                bullet_text="Test",
                matched_skills=["Python"]
            )
        ]

        requirements = JobRequirements()

        coverage, pct = generator._analyze_skill_coverage(selected, requirements)

        assert pct == 1.0  # No requirements = 100%


class TestResumeGeneratorGapIdentification:
    """Test suite for gap identification."""

    def test_identify_gaps_with_missing_skills(self):
        """Test gap identification when skills are missing."""
        generator = ResumeGenerator()

        coverage = {
            "Python": True,
            "SQL": False,
            "AWS": False
        }

        requirements = JobRequirements(
            required_skills=["Python", "SQL"],
            preferred_skills=["AWS"]
        )

        gaps = generator._identify_gaps(coverage, requirements)

        assert "SQL" in gaps
        assert "AWS" in gaps
        assert "Python" not in gaps

    def test_identify_gaps_no_gaps(self):
        """Test gap identification with no gaps."""
        generator = ResumeGenerator()

        coverage = {
            "Python": True,
            "SQL": True
        }

        requirements = JobRequirements(
            required_skills=["Python", "SQL"],
            preferred_skills=[]
        )

        gaps = generator._identify_gaps(coverage, requirements)

        assert gaps == []


class TestResumeGeneratorRecommendations:
    """Test suite for recommendation generation."""

    def test_generate_recommendations_high_coverage(self):
        """Test recommendations with high skill coverage."""
        generator = ResumeGenerator()

        selected = [
            ScoredAccomplishment(bullet_id=i, bullet_text=f"Test {i}", metrics_score=0.8)
            for i in range(10)
        ]

        coverage = {"Python": True, "SQL": True, "AWS": True}
        gaps = []
        requirements = JobRequirements(
            required_skills=["Python", "SQL", "AWS"]
        )

        recommendations = generator._generate_recommendations(
            selected, coverage, gaps, requirements, coverage_pct=1.0
        )

        # Should have positive recommendation
        assert any("strong" in r.lower() or "✅" in r for r in recommendations)

    def test_generate_recommendations_low_coverage(self):
        """Test recommendations with low skill coverage."""
        generator = ResumeGenerator()

        selected = [
            ScoredAccomplishment(bullet_id=1, bullet_text="Test")
        ]

        coverage = {"Python": True, "SQL": False, "AWS": False, "Docker": False}
        gaps = ["SQL", "AWS", "Docker"]
        requirements = JobRequirements(
            required_skills=["Python", "SQL", "AWS", "Docker"]
        )

        recommendations = generator._generate_recommendations(
            selected, coverage, gaps, requirements, coverage_pct=0.25
        )

        # Should have warning/improvement recommendations
        assert any("⚠️" in r or "low" in r.lower() for r in recommendations)
        # Should mention missing skills
        assert any("sql" in r.lower() or "aws" in r.lower() or "docker" in r.lower() for r in recommendations)

    def test_generate_recommendations_with_education(self):
        """Test recommendations include education requirements."""
        generator = ResumeGenerator()

        selected = []
        coverage = {}
        gaps = []
        requirements = JobRequirements(
            education_level="Bachelor's degree",
            years_experience=5
        )

        recommendations = generator._generate_recommendations(
            selected, coverage, gaps, requirements, coverage_pct=1.0
        )

        # Should mention education
        assert any("education" in r.lower() or "bachelor" in r.lower() for r in recommendations)
        # Should mention experience
        assert any("experience" in r.lower() or "5" in r for r in recommendations)


class TestResumeGeneratorMatchScore:
    """Test suite for overall match score calculation."""

    def test_calculate_match_score_high_match(self):
        """Test match score calculation for high match."""
        generator = ResumeGenerator()

        accomplishments = [
            ScoredAccomplishment(
                bullet_id=i,
                bullet_text=f"Test {i}",
                final_score=0.9
            )
            for i in range(20)
        ]

        resume = TailoredResume(
            profile_id=1,
            selected_accomplishments=accomplishments,
            skill_coverage={"Python": True, "SQL": True, "AWS": True},
            coverage_percentage=1.0,
            gaps=[]
        )

        score = generator.calculate_match_score(resume)

        assert score > 0.8  # Should be high

    def test_calculate_match_score_low_match(self):
        """Test match score calculation for low match."""
        generator = ResumeGenerator()

        accomplishments = [
            ScoredAccomplishment(
                bullet_id=1,
                bullet_text="Test",
                final_score=0.3
            )
        ]

        resume = TailoredResume(
            profile_id=1,
            selected_accomplishments=accomplishments,
            skill_coverage={"Python": False, "SQL": False, "AWS": False},
            coverage_percentage=0.0,
            gaps=["Python", "SQL", "AWS"]
        )

        score = generator.calculate_match_score(resume)

        assert score < 0.5  # Should be low

    def test_calculate_match_score_empty(self):
        """Test match score with no accomplishments."""
        generator = ResumeGenerator()

        resume = TailoredResume(
            profile_id=1,
            selected_accomplishments=[],
            coverage_percentage=0.0
        )

        score = generator.calculate_match_score(resume)

        assert score == 0.0


class TestResumeGeneratorGeneration:
    """Test suite for tailored resume generation."""

    def create_mock_bullet(self, text: str, bullet_id: int = 1):
        """Create a mock BulletPoint."""
        bullet = Mock()
        bullet.id = bullet_id
        bullet.bullet_text = text
        return bullet

    def create_mock_job(self, is_current: bool = False):
        """Create a mock Job."""
        job = Mock()
        job.company_name = "TechCorp"
        job.job_title = "Engineer"
        job.start_date = date(2020, 1, 1)
        job.is_current = is_current
        return job

    def test_generate_tailored_resume_success(self):
        """Test successful tailored resume generation."""
        # Create generator with mocked matching engine
        mock_engine = Mock()

        # Mock scored accomplishments
        scored = [
            ScoredAccomplishment(
                bullet_id=1,
                bullet_text="Developed Python API",
                final_score=0.9,
                matched_skills=["Python", "API"],
                is_current=True
            ),
            ScoredAccomplishment(
                bullet_id=2,
                bullet_text="Managed SQL databases",
                final_score=0.7,
                matched_skills=["SQL"],
                is_current=False
            )
        ]

        mock_engine.score_accomplishments.return_value = scored
        mock_engine.select_top_accomplishments.return_value = scored[:1]  # Select top 1

        generator = ResumeGenerator(matching_engine=mock_engine)

        # Create test data
        accomplishments = [
            (self.create_mock_bullet("Developed Python API", 1), self.create_mock_job(True)),
            (self.create_mock_bullet("Managed SQL databases", 2), self.create_mock_job(False))
        ]

        requirements = JobRequirements(
            required_skills=["Python", "SQL"],
            preferred_skills=[]
        )

        # Generate resume
        result = generator.generate_tailored_resume(
            profile_id=1,
            accomplishments=accomplishments,
            requirements=requirements,
            job_title="Senior Engineer",
            company_name="TargetCorp"
        )

        assert isinstance(result, TailoredResume)
        assert result.profile_id == 1
        assert result.job_title == "Senior Engineer"
        assert result.company_name == "TargetCorp"
        assert len(result.selected_accomplishments) > 0
        assert result.coverage_percentage > 0
        assert len(result.recommendations) > 0

    def test_generate_tailored_resume_empty_accomplishments(self):
        """Test generation with empty accomplishments raises error."""
        generator = ResumeGenerator()

        requirements = JobRequirements()

        with pytest.raises(ResumeGeneratorError):
            generator.generate_tailored_resume(
                profile_id=1,
                accomplishments=[],
                requirements=requirements
            )


class TestResumeGeneratorIntegration:
    """Integration tests for ResumeGenerator."""

    def create_realistic_data(self):
        """Create realistic test data."""
        bullets_jobs = []

        # Current role bullets
        for i in range(5):
            bullet = Mock()
            bullet.id = i
            bullet.bullet_text = f"Developed Python application {i} that improved performance by {10 + i*10}%"

            job = Mock()
            job.company_name = "CurrentCorp"
            job.job_title = "Senior Engineer"
            job.start_date = date(2022, 1, 1)
            job.is_current = True

            bullets_jobs.append((bullet, job))

        # Past role bullets
        for i in range(5, 10):
            bullet = Mock()
            bullet.id = i
            bullet.bullet_text = f"Managed SQL database with {i}M records"

            job = Mock()
            job.company_name = "OldCorp"
            job.job_title = "Engineer"
            job.start_date = date(2018, 1, 1)
            job.is_current = False

            bullets_jobs.append((bullet, job))

        return bullets_jobs

    def test_full_generation_workflow(self):
        """Test complete resume generation workflow."""
        generator = ResumeGenerator()

        accomplishments = self.create_realistic_data()

        requirements = JobRequirements(
            required_skills=["Python", "SQL", "AWS"],
            preferred_skills=["Docker", "Kubernetes"],
            years_experience=5,
            education_level="Bachelor's degree"
        )

        job_desc = "Looking for Python developer with SQL and AWS experience"

        # Generate tailored resume
        result = generator.generate_tailored_resume(
            profile_id=1,
            accomplishments=accomplishments,
            requirements=requirements,
            job_description_text=job_desc,
            job_title="Python Developer",
            company_name="TargetCompany",
            max_accomplishments=5
        )

        # Verify results
        assert isinstance(result, TailoredResume)
        assert result.profile_id == 1
        assert len(result.selected_accomplishments) <= 5
        assert 0.0 <= result.coverage_percentage <= 1.0
        assert len(result.recommendations) > 0

        # Calculate match score
        match_score = generator.calculate_match_score(result)
        assert 0.0 <= match_score <= 1.0
