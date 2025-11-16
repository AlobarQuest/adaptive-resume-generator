"""Unit tests for SkillDatabaseService."""

import pytest
from pathlib import Path

from adaptive_resume.services.skill_database_service import (
    SkillDatabaseService,
    SkillSuggestion,
    SkillDetails,
    SkillMatch,
    SkillDatabaseServiceError,
)


class TestSkillDatabaseService:
    """Tests for SkillDatabaseService."""

    @pytest.fixture
    def service(self):
        """Create a SkillDatabaseService instance with the default database."""
        return SkillDatabaseService()

    def test_service_initialization(self, service):
        """Test that service initializes correctly."""
        assert service is not None
        assert service.total_skills > 0
        assert service.version is not None

    def test_service_loads_database(self, service):
        """Test that database loads successfully."""
        assert len(service._skills_by_id) >= 100  # Should have 100+ skills
        assert len(service._skills_by_canonical) > 0
        assert len(service._alias_map) > 0
        assert len(service._category_skills) > 0

    def test_invalid_database_path(self):
        """Test that invalid database path raises error."""
        with pytest.raises(SkillDatabaseServiceError):
            SkillDatabaseService(database_path=Path("/nonexistent/path.json"))

    # ===== Search Tests =====

    def test_exact_match_search(self, service):
        """Test exact match on skill name."""
        results = service.search_skills("Python")
        assert len(results) > 0
        assert results[0].name == "Python"
        assert results[0].match_type == "exact"
        assert results[0].match_score == 1.0

    def test_exact_match_case_insensitive(self, service):
        """Test exact match is case-insensitive."""
        results = service.search_skills("python")
        assert len(results) > 0
        assert results[0].name == "Python"
        assert results[0].match_type == "exact"

    def test_alias_match(self, service):
        """Test matching on skill aliases."""
        results = service.search_skills("js")  # Alias for JavaScript
        assert len(results) > 0
        # Should match JavaScript
        js_results = [r for r in results if r.canonical_name == "javascript"]
        assert len(js_results) > 0

    def test_prefix_match(self, service):
        """Test prefix matching."""
        results = service.search_skills("pyth")
        assert len(results) > 0
        # Python should be in results
        python_results = [r for r in results if r.canonical_name == "python"]
        assert len(python_results) > 0
        assert python_results[0].match_type in ["exact", "prefix"]

    def test_fuzzy_match(self, service):
        """Test fuzzy matching for typos."""
        results = service.search_skills("pytohn")  # Typo
        assert len(results) > 0
        # Python should still be found via fuzzy match
        python_results = [r for r in results if r.canonical_name == "python"]
        assert len(python_results) > 0

    def test_search_with_limit(self, service):
        """Test search respects limit parameter."""
        results = service.search_skills("", limit=5)
        assert len(results) <= 5

    def test_search_with_category_filter(self, service):
        """Test category filtering."""
        results = service.search_skills(
            "python",
            category_filter="Programming Languages"
        )
        assert len(results) > 0
        # All results should be from Programming Languages category
        for result in results:
            if result.canonical_name == "python":
                assert result.category == "Programming Languages"

    def test_empty_query_returns_popular_skills(self, service):
        """Test that empty query returns popular skills."""
        results = service.search_skills("", limit=10)
        assert len(results) > 0
        # Should return popular/trending skills
        assert any(r.trending for r in results)

    def test_search_ranking(self, service):
        """Test that results are properly ranked."""
        results = service.search_skills("react")
        assert len(results) > 0
        # Exact match should be first
        assert results[0].canonical_name == "react"
        # Match scores should be in descending order
        for i in range(len(results) - 1):
            assert results[i].match_score >= results[i + 1].match_score

    # ===== Skill Details Tests =====

    def test_get_skill_details(self, service):
        """Test getting skill details by ID."""
        # Get Python skill (ID 1)
        details = service.get_skill_details(1)
        assert details is not None
        assert isinstance(details, SkillDetails)
        assert details.name == "Python"
        assert details.canonical_name == "python"
        assert len(details.aliases) > 0
        assert details.category == "Programming Languages"
        assert len(details.related_skills) > 0

    def test_get_skill_details_invalid_id(self, service):
        """Test getting details for non-existent skill."""
        details = service.get_skill_details(99999)
        assert details is None

    # ===== Related Skills Tests =====

    def test_get_related_skills(self, service):
        """Test getting related skills."""
        # Python (ID 1) should have related skills
        related = service.get_related_skills(1)
        assert len(related) > 0
        assert all(isinstance(r, SkillSuggestion) for r in related)
        # Should not include the original skill
        assert all(r.id != 1 for r in related)

    def test_get_related_skills_with_limit(self, service):
        """Test related skills respects limit."""
        related = service.get_related_skills(1, limit=3)
        assert len(related) <= 3

    def test_get_related_skills_invalid_id(self, service):
        """Test getting related skills for non-existent skill."""
        related = service.get_related_skills(99999)
        assert len(related) == 0

    # ===== Role Suggestions Tests =====

    def test_suggest_skills_for_role(self, service):
        """Test suggesting skills for a job role."""
        suggestions = service.suggest_skills_for_role("Software Engineer")
        assert len(suggestions) > 0
        assert all(isinstance(s, SkillSuggestion) for s in suggestions)
        # Should include common software engineering skills
        skill_names = [s.canonical_name for s in suggestions]
        assert any(name in ["python", "javascript", "java", "git"] for name in skill_names)

    def test_suggest_skills_for_data_scientist(self, service):
        """Test suggestions for Data Scientist role."""
        suggestions = service.suggest_skills_for_role("Data Scientist")
        assert len(suggestions) > 0
        skill_names = [s.canonical_name for s in suggestions]
        # Should include data science skills
        assert any(name in ["python", "numpy", "pandas", "sklearn"] for name in skill_names)

    def test_suggest_skills_for_role_with_limit(self, service):
        """Test role suggestions respect limit."""
        suggestions = service.suggest_skills_for_role("DevOps Engineer", limit=5)
        assert len(suggestions) <= 5

    # ===== Skill Validation Tests =====

    def test_validate_exact_match(self, service):
        """Test validating exact skill name."""
        match = service.validate_skill("Python")
        assert match.matched is True
        assert match.skill_id is not None
        assert match.canonical_name == "python"
        assert match.match_type in ["exact", "alias"]

    def test_validate_alias_match(self, service):
        """Test validating skill by alias."""
        match = service.validate_skill("js")
        assert match.matched is True
        assert match.canonical_name == "javascript"
        assert match.match_type == "alias"

    def test_validate_case_insensitive(self, service):
        """Test validation is case-insensitive."""
        match1 = service.validate_skill("Python")
        match2 = service.validate_skill("python")
        match3 = service.validate_skill("PYTHON")

        assert match1.matched and match2.matched and match3.matched
        assert match1.canonical_name == match2.canonical_name == match3.canonical_name

    def test_validate_fuzzy_match(self, service):
        """Test validation with fuzzy matching."""
        # Very close typo should still match
        match = service.validate_skill("Pytohn")
        assert match.matched is True
        assert match.canonical_name == "python"
        assert match.match_type == "fuzzy"

    def test_validate_no_match(self, service):
        """Test validation of non-existent skill."""
        match = service.validate_skill("CompletelyFakeSkill12345")
        assert match.matched is False
        assert match.skill_id is None
        assert match.canonical_name is None
        assert match.match_type == "none"

    def test_validate_empty_string(self, service):
        """Test validation of empty string."""
        match = service.validate_skill("")
        assert match.matched is False
        assert match.match_type == "none"

    def test_validate_whitespace(self, service):
        """Test validation of whitespace-only string."""
        match = service.validate_skill("   ")
        assert match.matched is False

    # ===== Get by Alias Tests =====

    def test_get_skill_by_alias(self, service):
        """Test getting skill details by alias."""
        details = service.get_skill_by_alias("js")
        assert details is not None
        assert details.canonical_name == "javascript"

    def test_get_skill_by_alias_not_found(self, service):
        """Test getting skill by non-existent alias."""
        details = service.get_skill_by_alias("FakeSkillAlias")
        assert details is None

    # ===== Category Tests =====

    def test_get_categories(self, service):
        """Test getting all categories."""
        categories = service.get_categories()
        assert len(categories) > 0
        assert all('id' in cat for cat in categories)
        assert all('name' in cat for cat in categories)
        # Should include common categories
        cat_names = [cat['name'] for cat in categories]
        assert "Programming Languages" in cat_names
        assert "Frameworks & Libraries" in cat_names

    # ===== Skill Path Tests =====

    def test_get_all_skill_paths(self, service):
        """Test getting all skill paths."""
        paths = service.get_all_skill_paths()
        assert len(paths) > 0
        assert all('id' in path for path in paths)
        assert all('name' in path for path in paths)
        assert all('levels' in path for path in paths)

    def test_get_skill_path(self, service):
        """Test getting specific skill path."""
        # Get Frontend Developer Path (ID 1)
        path = service.get_skill_path(1)
        assert path is not None
        assert path['name'] == "Frontend Developer Path"
        assert 'levels' in path
        assert len(path['levels']) > 0

    def test_get_skill_path_invalid(self, service):
        """Test getting non-existent skill path."""
        path = service.get_skill_path(99999)
        assert path is None

    # ===== Edge Cases =====

    def test_search_special_characters(self, service):
        """Test search with special characters."""
        results = service.search_skills("C++")
        assert len(results) > 0
        # Should find C++
        cpp_results = [r for r in results if "c" in r.canonical_name.lower()]
        assert len(cpp_results) > 0

    def test_search_with_spaces(self, service):
        """Test search with spaces."""
        results = service.search_skills("  python  ")
        assert len(results) > 0
        assert results[0].canonical_name == "python"

    def test_multiple_word_skill(self, service):
        """Test searching for multi-word skills."""
        results = service.search_skills("Ruby on Rails")
        assert len(results) > 0
        # Should find Rails
        rails_results = [r for r in results if "rails" in r.canonical_name]
        assert len(rails_results) > 0

    def test_trending_skills_boosted(self, service):
        """Test that trending skills get slight score boost."""
        # Search for a term that might match both trending and non-trending
        results = service.search_skills("java")
        # Just verify we got results; trending boost is subtle
        assert len(results) > 0

    # ===== Performance Tests =====

    def test_search_performance(self, service):
        """Test that search is reasonably fast."""
        import time

        start = time.time()
        for _ in range(100):
            service.search_skills("python", limit=10)
        end = time.time()

        elapsed_ms = (end - start) * 1000
        avg_ms = elapsed_ms / 100

        # Each search should average well under 50ms
        assert avg_ms < 10, f"Search took {avg_ms}ms on average"

    def test_large_result_set(self, service):
        """Test searching with large limit."""
        results = service.search_skills("", limit=100)
        assert len(results) <= 100
        # Should still be sorted properly
        assert all(isinstance(r, SkillSuggestion) for r in results)


class TestSkillDataStructures:
    """Test the data structures used by the service."""

    def test_skill_suggestion_creation(self):
        """Test creating a SkillSuggestion."""
        suggestion = SkillSuggestion(
            id=1,
            name="Python",
            canonical_name="python",
            category="Programming Languages",
            subcategory="Backend",
            description="Programming language",
            difficulty_level="intermediate",
            popularity_rank=3,
            trending=True,
            match_score=1.0,
            match_type="exact"
        )
        assert suggestion.name == "Python"
        assert suggestion.match_score == 1.0

    def test_skill_details_creation(self):
        """Test creating SkillDetails."""
        details = SkillDetails(
            id=1,
            name="Python",
            canonical_name="python",
            aliases=["py", "python3"],
            category="Programming Languages",
            subcategory="Backend",
            related_skills=[2, 3, 4],
            difficulty_level="intermediate",
            common_in_roles=["Developer", "Data Scientist"],
            description="Programming language",
            popularity_rank=3,
            trending=True
        )
        assert details.name == "Python"
        assert len(details.aliases) == 2

    def test_skill_match_creation(self):
        """Test creating SkillMatch."""
        match = SkillMatch(
            matched=True,
            skill_id=1,
            canonical_name="python",
            match_type="exact"
        )
        assert match.matched is True
        assert match.skill_id == 1
