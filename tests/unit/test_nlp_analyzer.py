"""
Unit tests for NLPAnalyzer service.

Tests cover:
- Initialization with/without spaCy and AI
- spaCy-based extraction
- AI-based extraction (mocked)
- Result merging
- Skill extraction
- Years of experience extraction
- Education level extraction
- Responsibilities extraction
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from adaptive_resume.services.nlp_analyzer import (
    NLPAnalyzer,
    JobRequirements,
    NLPAnalyzerError,
)


class TestJobRequirements:
    """Test suite for JobRequirements dataclass."""

    def test_job_requirements_defaults(self):
        """Test JobRequirements with default values."""
        req = JobRequirements()

        assert req.required_skills == []
        assert req.preferred_skills == []
        assert req.years_experience is None
        assert req.education_level is None
        assert req.key_responsibilities == []
        assert req.confidence_score == 0.0
        assert req.raw_sections == {}
        assert req.extraction_method == "unknown"

    def test_job_requirements_with_values(self):
        """Test JobRequirements with specific values."""
        req = JobRequirements(
            required_skills=["Python", "SQL"],
            preferred_skills=["AWS"],
            years_experience=5,
            education_level="Bachelor's",
            key_responsibilities=["Develop software"],
            confidence_score=0.85,
            extraction_method="hybrid"
        )

        assert req.required_skills == ["Python", "SQL"]
        assert req.preferred_skills == ["AWS"]
        assert req.years_experience == 5
        assert req.education_level == "Bachelor's"
        assert len(req.key_responsibilities) == 1
        assert req.confidence_score == 0.85
        assert req.extraction_method == "hybrid"


class TestNLPAnalyzerInit:
    """Test suite for NLPAnalyzer initialization."""

    def test_init_without_spacy(self, monkeypatch):
        """Test initialization when spaCy is not available."""
        import adaptive_resume.services.nlp_analyzer as nlp_module
        monkeypatch.setattr(nlp_module, 'SPACY_AVAILABLE', False)

        analyzer = NLPAnalyzer()

        assert not analyzer.is_spacy_available
        assert analyzer.nlp is None

    def test_init_properties(self):
        """Test analyzer properties."""
        analyzer = NLPAnalyzer()

        assert isinstance(analyzer.is_spacy_available, bool)
        assert isinstance(analyzer.is_ai_available, bool)


class TestNLPAnalyzerYearsExtraction:
    """Test suite for years of experience extraction."""

    def test_extract_years_basic(self):
        """Test basic years extraction."""
        analyzer = NLPAnalyzer()

        text = "5 years of experience required"
        years = analyzer._extract_years_experience(text)
        assert years == 5

    def test_extract_years_variations(self):
        """Test various year formats."""
        analyzer = NLPAnalyzer()

        test_cases = [
            ("3+ years experience", 3),
            ("Experience: 7 years", 7),
            ("Minimum 10 years of experience", 10),
            ("2 yrs required", 2),
        ]

        for text, expected in test_cases:
            years = analyzer._extract_years_experience(text)
            assert years == expected, f"Failed for: {text}"

    def test_extract_years_not_found(self):
        """Test when years not mentioned."""
        analyzer = NLPAnalyzer()

        text = "Looking for an experienced developer"
        years = analyzer._extract_years_experience(text)
        assert years is None

    def test_extract_years_sanity_check(self):
        """Test that unrealistic years are rejected."""
        analyzer = NLPAnalyzer()

        text = "100 years of experience"
        years = analyzer._extract_years_experience(text)
        assert years is None  # 100 years exceeds sanity check


class TestNLPAnalyzerEducationExtraction:
    """Test suite for education level extraction."""

    def test_extract_education_bachelors(self):
        """Test bachelor's degree extraction."""
        analyzer = NLPAnalyzer()

        test_cases = [
            "Bachelor's degree required",
            "BS in Computer Science",
            "B.S. degree",
        ]

        for text in test_cases:
            education = analyzer._extract_education_level(text)
            assert education == "Bachelor'S", f"Failed for: {text}"

    def test_extract_education_masters(self):
        """Test master's degree extraction."""
        analyzer = NLPAnalyzer()

        text = "Master's degree preferred"
        education = analyzer._extract_education_level(text)
        assert education == "Master'S"

    def test_extract_education_phd(self):
        """Test PhD extraction."""
        analyzer = NLPAnalyzer()

        text = "PhD in Computer Science"
        education = analyzer._extract_education_level(text)
        assert education == "Phd"

    def test_extract_education_not_found(self):
        """Test when education not mentioned."""
        analyzer = NLPAnalyzer()

        text = "Looking for experienced developers"
        education = analyzer._extract_education_level(text)
        assert education is None


class TestNLPAnalyzerSectionIdentification:
    """Test suite for section identification."""

    def test_identify_sections_basic(self):
        """Test basic section identification."""
        analyzer = NLPAnalyzer()

        text = """Software Engineer

Requirements:
- Python
- SQL

Responsibilities:
- Develop software
- Write tests

Benefits:
- Health insurance
- 401k
"""

        sections = analyzer._identify_sections(text)

        assert 'requirements' in sections
        assert 'responsibilities' in sections
        assert 'benefits' in sections
        assert 'Python' in sections['requirements']
        assert 'Develop software' in sections['responsibilities']


class TestNLPAnalyzerSkillMerging:
    """Test suite for skill list merging."""

    def test_merge_skill_lists_no_duplicates(self):
        """Test merging lists without duplicates."""
        analyzer = NLPAnalyzer()

        list1 = ["Python", "SQL"]
        list2 = ["AWS", "Docker"]

        merged = analyzer._merge_skill_lists(list1, list2)

        assert len(merged) == 4
        assert "Python" in merged
        assert "AWS" in merged

    def test_merge_skill_lists_with_duplicates(self):
        """Test merging lists with duplicates (case-insensitive)."""
        analyzer = NLPAnalyzer()

        list1 = ["Python", "SQL", "AWS"]
        list2 = ["python", "Docker", "aws"]

        merged = analyzer._merge_skill_lists(list1, list2)

        # Should have 4 unique skills (Python, SQL, AWS, Docker)
        assert len(merged) == 4
        # Check case-insensitive deduplication worked
        python_count = sum(1 for s in merged if s.lower() == 'python')
        assert python_count == 1


class TestNLPAnalyzerConfidence:
    """Test suite for confidence calculation."""

    def test_calculate_confidence_full_data(self):
        """Test confidence with all data present."""
        analyzer = NLPAnalyzer()

        skills = {'required': ['Python', 'SQL', 'AWS'], 'preferred': ['Docker']}
        years = 5
        education = "Bachelor's"
        responsibilities = ['Develop', 'Test', 'Deploy']

        confidence = analyzer._calculate_spacy_confidence(
            skills, years, education, responsibilities
        )

        assert 0.7 <= confidence <= 1.0  # Should be high with all data

    def test_calculate_confidence_minimal_data(self):
        """Test confidence with minimal data."""
        analyzer = NLPAnalyzer()

        skills = {'required': [], 'preferred': []}
        years = None
        education = None
        responsibilities = []

        confidence = analyzer._calculate_spacy_confidence(
            skills, years, education, responsibilities
        )

        assert confidence == 0.0  # No data found

    def test_calculate_confidence_partial_data(self):
        """Test confidence with partial data."""
        analyzer = NLPAnalyzer()

        skills = {'required': ['Python'], 'preferred': []}
        years = 5
        education = None
        responsibilities = []

        confidence = analyzer._calculate_spacy_confidence(
            skills, years, education, responsibilities
        )

        assert 0.2 < confidence < 0.5  # Some data found


class TestNLPAnalyzerSpacyExtraction:
    """Test suite for spaCy-based extraction."""

    @pytest.mark.skipif(
        not pytest.importorskip("spacy", reason="spaCy not available"),
        reason="spaCy not available"
    )
    def test_extract_with_spacy_real_posting(self):
        """Test spaCy extraction with real job posting."""
        analyzer = NLPAnalyzer()

        if not analyzer.is_spacy_available:
            pytest.skip("spaCy model not loaded")

        job_text = """
        Software Engineer - Python/Django

        Requirements:
        - 5+ years of experience in software development
        - Strong proficiency in Python and Django
        - Bachelor's degree in Computer Science

        Responsibilities:
        - Develop scalable web applications
        - Write clean, maintainable code
        - Collaborate with cross-functional teams
        """

        result = analyzer._extract_with_spacy(job_text)

        assert isinstance(result, JobRequirements)
        assert result.years_experience == 5
        assert result.education_level == "Bachelor'S"
        assert result.extraction_method == "spacy"
        assert result.confidence_score > 0


class TestNLPAnalyzerAIExtraction:
    """Test suite for AI-based extraction (mocked)."""

    def test_extract_with_ai_success(self):
        """Test AI extraction with mocked successful response."""
        analyzer = NLPAnalyzer(api_key="test-key")

        # Mock the Anthropic client
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = """{
            "required_skills": ["Python", "Django", "PostgreSQL"],
            "preferred_skills": ["AWS", "Docker"],
            "years_experience": 5,
            "education_level": "Bachelor's degree",
            "key_responsibilities": [
                "Develop web applications",
                "Write tests",
                "Deploy to production"
            ]
        }"""

        with patch.object(analyzer.client.messages, 'create', return_value=mock_response):
            result = analyzer._extract_with_ai("Test job posting text")

        assert isinstance(result, JobRequirements)
        assert "Python" in result.required_skills
        assert "AWS" in result.preferred_skills
        assert result.years_experience == 5
        assert result.education_level == "Bachelor's degree"
        assert len(result.key_responsibilities) == 3
        assert result.confidence_score == 0.9

    def test_extract_with_ai_json_error(self):
        """Test AI extraction with invalid JSON response."""
        analyzer = NLPAnalyzer(api_key="test-key")

        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is not valid JSON"

        with patch.object(analyzer.client.messages, 'create', return_value=mock_response):
            with pytest.raises(NLPAnalyzerError):
                analyzer._extract_with_ai("Test job posting")

    def test_extract_with_ai_not_available(self):
        """Test AI extraction when service not available."""
        analyzer = NLPAnalyzer()  # No API key
        analyzer.ai_service_enabled = False  # Explicitly disable

        with pytest.raises(NLPAnalyzerError, match="AI service not available"):
            analyzer._extract_with_ai("Test job posting")


class TestNLPAnalyzerResultMerging:
    """Test suite for result merging."""

    def test_merge_results_basic(self):
        """Test basic result merging."""
        analyzer = NLPAnalyzer()

        spacy_result = JobRequirements(
            required_skills=["Python", "SQL"],
            preferred_skills=["AWS"],
            years_experience=5,
            education_level="Bachelor's",
            confidence_score=0.6,
            raw_sections={"requirements": "Python, SQL"}
        )

        ai_result = JobRequirements(
            required_skills=["Python", "Django", "PostgreSQL"],
            preferred_skills=["Docker"],
            years_experience=5,
            education_level="Bachelor's degree",
            key_responsibilities=["Develop software"],
            confidence_score=0.9
        )

        merged = analyzer._merge_results(spacy_result, ai_result)

        # Should have combined skills
        assert "Python" in merged.required_skills
        assert "Django" in merged.required_skills
        assert "PostgreSQL" in merged.required_skills

        # Should deduplicate Python
        python_count = sum(1 for s in merged.required_skills if s.lower() == 'python')
        assert python_count == 1

        # Should prefer AI responsibilities
        assert merged.key_responsibilities == ["Develop software"]

        # Should use spaCy's sections
        assert merged.raw_sections == {"requirements": "Python, SQL"}

        # Confidence should be boosted (both agree on years)
        assert merged.confidence_score > 0.75


class TestNLPAnalyzerAnalyze:
    """Test suite for main analyze() method."""

    def test_analyze_empty_text(self):
        """Test analyzing empty text raises error."""
        analyzer = NLPAnalyzer()

        with pytest.raises(NLPAnalyzerError):
            analyzer.analyze("")

    def test_analyze_spacy_only(self):
        """Test analyze with spaCy only (no AI)."""
        analyzer = NLPAnalyzer()  # No API key

        job_text = """
        Senior Developer position requiring 5 years experience.
        Python and SQL required. AWS preferred.
        Bachelor's degree required.
        """

        result = analyzer.analyze(job_text, use_ai=False)

        assert isinstance(result, JobRequirements)
        assert result.extraction_method == "spacy"
        assert result.years_experience == 5

    def test_analyze_with_ai_fallback(self):
        """Test analyze falling back to spaCy when AI fails."""
        analyzer = NLPAnalyzer(api_key="test-key")

        # Mock AI failure
        with patch.object(analyzer, '_extract_with_ai', side_effect=Exception("API Error")):
            result = analyzer.analyze("Job posting text", use_ai=True)

        assert result.extraction_method == "spacy"


class TestNLPAnalyzerIntegration:
    """Integration tests with real job postings."""

    def test_analyze_sample_job_posting(self):
        """Test analyzing sample job posting file."""
        analyzer = NLPAnalyzer()

        test_file = Path(__file__).parent.parent / "fixtures" / "sample_job_postings" / "sample_job_posting.txt"

        if not test_file.exists():
            pytest.skip("Sample job posting file not found")

        with open(test_file, 'r', encoding='utf-8') as f:
            job_text = f.read()

        # Analyze without AI (to avoid API costs in tests)
        result = analyzer.analyze(job_text, use_ai=False)

        assert isinstance(result, JobRequirements)
        # Should find years (5+ years mentioned in sample)
        assert result.years_experience == 5
        # Should find education (Bachelor's mentioned)
        assert result.education_level is not None
        # Should find some skills
        assert len(result.required_skills) + len(result.preferred_skills) > 0

    def test_analyze_simple_posting(self):
        """Test analyzing simple job posting."""
        analyzer = NLPAnalyzer()

        test_file = Path(__file__).parent.parent / "fixtures" / "sample_job_postings" / "simple_posting.txt"

        if not test_file.exists():
            pytest.skip("Simple posting file not found")

        with open(test_file, 'r', encoding='utf-8') as f:
            job_text = f.read()

        result = analyzer.analyze(job_text, use_ai=False)

        assert isinstance(result, JobRequirements)
        assert result.years_experience == 3  # "3+ years" in simple posting
        # Should have some confidence
        assert result.confidence_score > 0
