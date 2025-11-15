"""
Unit tests for MatchingEngine service.

Tests cover:
- Initialization and weight validation
- Skill matching (direct, family, semantic)
- Semantic similarity scoring
- Recency scoring
- Metrics scoring
- Combined scoring
- Top accomplishment selection
- Reason generation
"""

import pytest
from unittest.mock import Mock
from datetime import date, timedelta
from adaptive_resume.services.matching_engine import (
    MatchingEngine,
    ScoredAccomplishment,
    MatchingEngineError,
)
from adaptive_resume.services.nlp_analyzer import JobRequirements


class TestScoredAccomplishment:
    """Test suite for ScoredAccomplishment dataclass."""

    def test_scored_accomplishment_defaults(self):
        """Test ScoredAccomplishment with default values."""
        scored = ScoredAccomplishment(bullet_id=1, bullet_text="Test bullet")

        assert scored.bullet_id == 1
        assert scored.bullet_text == "Test bullet"
        assert scored.final_score == 0.0
        assert scored.matched_skills == []
        assert scored.reasons == []

    def test_scored_accomplishment_with_values(self):
        """Test ScoredAccomplishment with specific values."""
        scored = ScoredAccomplishment(
            bullet_id=1,
            bullet_text="Developed Python application",
            final_score=0.85,
            skill_match_score=0.9,
            matched_skills=["Python", "SQL"],
            reasons=["Strong Python match"]
        )

        assert scored.final_score == 0.85
        assert len(scored.matched_skills) == 2
        assert len(scored.reasons) == 1


class TestMatchingEngineInit:
    """Test suite for MatchingEngine initialization."""

    def test_init_default_weights(self):
        """Test initialization with default weights."""
        engine = MatchingEngine()

        assert engine.weights['skill_match'] == 0.4
        assert engine.weights['semantic'] == 0.3
        assert engine.weights['recency'] == 0.2
        assert engine.weights['metrics'] == 0.1
        assert sum(engine.weights.values()) == pytest.approx(1.0)

    def test_init_custom_weights(self):
        """Test initialization with custom weights."""
        custom_weights = {
            'skill_match': 0.5,
            'semantic': 0.2,
            'recency': 0.2,
            'metrics': 0.1
        }
        engine = MatchingEngine(weights=custom_weights)

        assert engine.weights['skill_match'] == 0.5
        assert engine.weights['semantic'] == 0.2

    def test_init_invalid_weights(self):
        """Test initialization with invalid weights raises error."""
        invalid_weights = {
            'skill_match': 0.5,
            'semantic': 0.3,
            'recency': 0.1,
            'metrics': 0.05  # Sum = 0.95, not 1.0
        }

        with pytest.raises(MatchingEngineError):
            MatchingEngine(weights=invalid_weights)

    def test_is_spacy_available(self):
        """Test spaCy availability check."""
        engine = MatchingEngine()
        assert isinstance(engine.is_spacy_available, bool)


class TestMatchingEngineRecencyScoring:
    """Test suite for recency scoring."""

    def test_recency_current_role(self):
        """Test recency score for current role."""
        engine = MatchingEngine()

        # Current role should get maximum score
        score = engine._calculate_recency_score(date(2020, 1, 1), is_current=True)
        assert score == 1.0

    def test_recency_recent_past(self):
        """Test recency score for recent past role."""
        engine = MatchingEngine()

        # 1 year ago
        one_year_ago = date.today() - timedelta(days=365)
        score = engine._calculate_recency_score(one_year_ago, is_current=False)

        assert 0.75 < score < 0.85  # Should be high but not 1.0

    def test_recency_distant_past(self):
        """Test recency score for distant past role."""
        engine = MatchingEngine()

        # 10 years ago
        ten_years_ago = date.today() - timedelta(days=3650)
        score = engine._calculate_recency_score(ten_years_ago, is_current=False)

        assert 0.1 < score < 0.2  # Should be low

    def test_recency_no_date(self):
        """Test recency score when no date provided."""
        engine = MatchingEngine()

        score = engine._calculate_recency_score(None, is_current=False)
        assert score == 0.3  # Default low score


class TestMatchingEngineMetricsScoring:
    """Test suite for metrics scoring."""

    def test_metrics_with_percentage(self):
        """Test metrics detection with percentages."""
        engine = MatchingEngine()

        text = "Improved performance by 50% using optimization techniques"
        score = engine._calculate_metrics_score(text)

        assert score > 0.5  # Has percentage

    def test_metrics_with_money(self):
        """Test metrics detection with money values."""
        engine = MatchingEngine()

        text = "Saved $100K annually by streamlining processes"
        score = engine._calculate_metrics_score(text)

        assert score > 0.5  # Has money and impact word

    def test_metrics_with_action_verb(self):
        """Test metrics detection with action verbs."""
        engine = MatchingEngine()

        text = "Developed new feature for customer management"
        score = engine._calculate_metrics_score(text)

        assert score >= 0.25  # Has action verb

    def test_metrics_comprehensive(self):
        """Test metrics with all elements."""
        engine = MatchingEngine()

        text = "Led team that increased revenue by 150% ($2M annually)"
        score = engine._calculate_metrics_score(text)

        assert score >= 0.9  # Has metrics, action verb, and impact word

    def test_metrics_none(self):
        """Test metrics when no achievements present."""
        engine = MatchingEngine()

        text = "Worked on various projects"
        score = engine._calculate_metrics_score(text)

        assert score == 0.0  # No metrics


class TestMatchingEngineSkillMatching:
    """Test suite for skill matching."""

    def test_skill_match_direct(self):
        """Test direct keyword skill matching."""
        engine = MatchingEngine()

        text = "Developed web application using Python and Django"
        skills = {'python', 'django', 'sql'}

        score, matched = engine._calculate_skill_match(text, skills)

        assert 'python' in matched
        assert 'django' in matched
        assert score > 0.5

    def test_skill_match_case_insensitive(self):
        """Test case-insensitive skill matching."""
        engine = MatchingEngine()

        text = "Worked with PYTHON and JavaScript"
        skills = {'python', 'javascript'}

        score, matched = engine._calculate_skill_match(text, skills)

        assert 'python' in matched
        assert 'javascript' in matched

    def test_skill_match_technology_family(self):
        """Test technology family matching."""
        engine = MatchingEngine()

        text = "Built frontend using React and TypeScript"
        skills = {'javascript', 'frontend'}  # React is in JavaScript family

        score, matched = engine._calculate_skill_match(text, skills)

        # Should match via technology family
        assert len(matched) > 0
        assert score > 0.0

    def test_skill_match_no_skills(self):
        """Test skill matching with no skills."""
        engine = MatchingEngine()

        text = "General project management"
        skills = set()

        score, matched = engine._calculate_skill_match(text, skills)

        assert score == 0.0
        assert matched == []

    def test_skill_in_text_word_boundaries(self):
        """Test skill matching respects word boundaries."""
        engine = MatchingEngine()

        # "go" should not match "google"
        assert not engine._skill_in_text("go", "worked at google")

        # But should match standalone "go"
        assert engine._skill_in_text("go", "programmed in go")


class TestMatchingEngineSemanticSimilarity:
    """Test suite for semantic similarity (requires spaCy)."""

    @pytest.mark.skipif(
        not pytest.importorskip("spacy", reason="spaCy not available"),
        reason="spaCy not available"
    )
    def test_semantic_similarity_basic(self):
        """Test basic semantic similarity calculation."""
        engine = MatchingEngine()

        if not engine.is_spacy_available:
            pytest.skip("spaCy model not loaded")

        # Similar texts should have higher similarity
        bullet = "Developed Python web applications"
        job_text = "Looking for developer with Python and web development experience"

        job_vector = engine._get_or_cache_vector(job_text)
        score = engine._calculate_semantic_similarity(bullet, job_vector)

        assert score > 0.3  # Should have some similarity

    def test_semantic_similarity_no_spacy(self, monkeypatch):
        """Test semantic similarity without spaCy."""
        import adaptive_resume.services.matching_engine as me_module
        monkeypatch.setattr(me_module, 'SPACY_AVAILABLE', False)

        engine = MatchingEngine()
        score = engine._calculate_semantic_similarity("test", None)

        assert score == 0.0  # Should return 0 without spaCy


class TestMatchingEngineScoring:
    """Test suite for complete scoring."""

    def create_mock_bullet(self, text: str, bullet_id: int = 1):
        """Create a mock BulletPoint."""
        bullet = Mock()
        bullet.id = bullet_id
        bullet.full_text = text
        return bullet

    def create_mock_job(
        self,
        company: str = "TechCorp",
        title: str = "Software Engineer",
        start_date: date = None,
        is_current: bool = False
    ):
        """Create a mock Job."""
        job = Mock()
        job.company_name = company
        job.job_title = title
        job.start_date = start_date or date(2020, 1, 1)
        job.is_current = is_current
        return job

    def test_score_single_accomplishment(self):
        """Test scoring a single accomplishment."""
        engine = MatchingEngine()

        bullet = self.create_mock_bullet(
            "Developed Python application that reduced processing time by 50%"
        )
        job = self.create_mock_job(is_current=True)

        requirements = JobRequirements(
            required_skills=["Python", "SQL"],
            preferred_skills=["AWS"]
        )

        scored = engine._score_single_accomplishment(
            bullet, job, requirements, {'python', 'sql', 'aws'}, None
        )

        assert isinstance(scored, ScoredAccomplishment)
        assert scored.final_score > 0.0
        assert 'python' in scored.matched_skills
        assert scored.recency_score == 1.0  # Current role
        assert scored.metrics_score > 0.5  # Has percentage

    def test_score_accomplishments_list(self):
        """Test scoring multiple accomplishments."""
        engine = MatchingEngine()

        bullets_jobs = [
            (self.create_mock_bullet("Developed Python API", 1), self.create_mock_job(is_current=True)),
            (self.create_mock_bullet("Managed SQL databases", 2), self.create_mock_job(is_current=False)),
            (self.create_mock_bullet("General project work", 3), self.create_mock_job(is_current=False)),
        ]

        requirements = JobRequirements(
            required_skills=["Python", "SQL"],
            preferred_skills=[]
        )

        scored = engine.score_accomplishments(bullets_jobs, requirements)

        assert len(scored) == 3
        # Should be sorted by score
        assert scored[0].final_score >= scored[1].final_score
        assert scored[1].final_score >= scored[2].final_score

    def test_score_empty_list(self):
        """Test scoring empty accomplishment list."""
        engine = MatchingEngine()

        requirements = JobRequirements()
        scored = engine.score_accomplishments([], requirements)

        assert scored == []


class TestMatchingEngineSelection:
    """Test suite for top accomplishment selection."""

    def create_scored_items(self, count: int):
        """Create a list of mock scored accomplishments."""
        items = []
        for i in range(count):
            item = ScoredAccomplishment(
                bullet_id=i,
                bullet_text=f"Bullet {i}",
                company_name="Company" + str(i % 3),  # Distribute across 3 companies
                final_score=1.0 - (i * 0.05),  # Decreasing scores
                is_current=(i < 5)  # First 5 are current
            )
            items.append(item)
        return items

    def test_select_top_basic(self):
        """Test basic top selection."""
        engine = MatchingEngine()

        items = self.create_scored_items(50)
        selected = engine.select_top_accomplishments(items, max_count=10)

        assert len(selected) <= 10
        # Check sorted by score
        for i in range(len(selected) - 1):
            assert selected[i].final_score >= selected[i + 1].final_score

    def test_select_with_min_score(self):
        """Test selection with minimum score threshold."""
        engine = MatchingEngine()

        items = self.create_scored_items(50)
        selected = engine.select_top_accomplishments(
            items, max_count=30, min_score=0.7
        )

        # All selected should meet minimum score
        assert all(item.final_score >= 0.7 for item in selected)

    def test_select_current_role_preference(self):
        """Test preference for current role."""
        engine = MatchingEngine()

        items = self.create_scored_items(20)
        selected = engine.select_top_accomplishments(
            items,
            max_count=10,
            current_role_preference=0.7  # 70% from current
        )

        current_count = sum(1 for item in selected if item.is_current)
        # Should have significant current role representation
        assert current_count >= 5  # At least 50% from current

    def test_select_max_per_company(self):
        """Test max bullets per company limit."""
        engine = MatchingEngine()

        # Create items all from same company
        items = []
        for i in range(20):
            item = ScoredAccomplishment(
                bullet_id=i,
                bullet_text=f"Bullet {i}",
                company_name="SameCompany",
                final_score=1.0 - (i * 0.01),
                is_current=False
            )
            items.append(item)

        selected = engine.select_top_accomplishments(
            items, max_count=15, max_per_company=5
        )

        # Should not exceed max per company
        assert len(selected) <= 5

    def test_select_empty_list(self):
        """Test selection from empty list."""
        engine = MatchingEngine()

        selected = engine.select_top_accomplishments([])
        assert selected == []


class TestMatchingEngineReasonGeneration:
    """Test suite for reason generation."""

    def test_generate_reasons_strong_match(self):
        """Test reason generation for strong match."""
        engine = MatchingEngine()

        reasons = engine._generate_reasons(
            skill_score=0.9,
            semantic_score=0.7,
            recency_score=1.0,
            metrics_score=0.8,
            matched_skills=["Python", "SQL", "AWS"],
            is_current=True
        )

        assert len(reasons) > 0
        # Should mention skill match
        assert any("skill" in r.lower() for r in reasons)
        # Should mention current role
        assert any("current" in r.lower() for r in reasons)

    def test_generate_reasons_weak_match(self):
        """Test reason generation for weak match."""
        engine = MatchingEngine()

        reasons = engine._generate_reasons(
            skill_score=0.2,
            semantic_score=0.3,
            recency_score=0.4,
            metrics_score=0.1,
            matched_skills=[],
            is_current=False
        )

        # Should have at least a generic reason
        assert len(reasons) > 0

    def test_generate_reasons_partial_match(self):
        """Test reason generation for partial match."""
        engine = MatchingEngine()

        reasons = engine._generate_reasons(
            skill_score=0.5,
            semantic_score=0.5,
            recency_score=0.8,
            metrics_score=0.5,
            matched_skills=["Python"],
            is_current=False
        )

        assert len(reasons) > 0
        # Should mention partial nature
        assert any("partial" in r.lower() or "somewhat" in r.lower() for r in reasons)


class TestMatchingEngineIntegration:
    """Integration tests for MatchingEngine."""

    def create_real_test_data(self):
        """Create realistic test data."""
        bullet1 = Mock()
        bullet1.id = 1
        bullet1.full_text = "Developed Python REST API using Django that reduced query time by 60%"

        bullet2 = Mock()
        bullet2.id = 2
        bullet2.full_text = "Managed PostgreSQL database with 1M+ records"

        bullet3 = Mock()
        bullet3.id = 3
        bullet3.full_text = "Attended meetings and wrote documentation"

        job_current = Mock()
        job_current.company_name = "CurrentCorp"
        job_current.job_title = "Senior Engineer"
        job_current.start_date = date(2023, 1, 1)
        job_current.is_current = True

        job_past = Mock()
        job_past.company_name = "OldCorp"
        job_past.job_title = "Engineer"
        job_past.start_date = date(2018, 1, 1)
        job_past.is_current = False

        return [
            (bullet1, job_current),
            (bullet2, job_current),
            (bullet3, job_past),
        ]

    def test_full_workflow(self):
        """Test complete matching workflow."""
        engine = MatchingEngine()

        accomplishments = self.create_real_test_data()

        requirements = JobRequirements(
            required_skills=["Python", "Django", "PostgreSQL"],
            preferred_skills=["AWS", "Docker"],
            years_experience=5
        )

        job_desc = "Looking for Python developer with Django and PostgreSQL experience"

        # Score all accomplishments
        scored = engine.score_accomplishments(accomplishments, requirements, job_desc)

        assert len(scored) == 3

        # First item (Python Django) should score highest
        assert scored[0].bullet_id == 1
        assert scored[0].final_score > scored[1].final_score

        # Select top items
        selected = engine.select_top_accomplishments(scored, max_count=2)

        assert len(selected) == 2
        assert all(s.final_score > 0.3 for s in selected)  # Should meet reasonable threshold
