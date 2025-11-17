"""Unit tests for TagService."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from adaptive_resume.models.tag import Tag, BulletTag
from adaptive_resume.models.bullet_point import BulletPoint
from adaptive_resume.services.tag_service import (
    TagService,
    TagServiceError,
    TagNotFoundError,
)


class TestTagService:
    """Test suite for TagService."""

    @pytest.fixture
    def tag_service(self, session):
        """Create a TagService instance."""
        return TagService(session)

    def test_create_tag(self, tag_service):
        """Test creating a new tag."""
        tag = tag_service.create_tag("Python", "programming")

        assert tag.id is not None
        assert tag.name == "python"
        assert tag.category == "programming"

    def test_create_tag_normalizes_name(self, tag_service):
        """Test that tag names are normalized."""
        tag1 = tag_service.create_tag("Python Programming", "technical")
        tag2 = tag_service.create_tag("MACHINE_LEARNING", "technical")

        assert tag1.name == "python-programming"
        assert tag2.name == "machine-learning"

    def test_create_tag_duplicate_raises_error(self, tag_service):
        """Test that creating duplicate tag raises error."""
        tag_service.create_tag("Python", "programming")

        with pytest.raises(TagServiceError, match="already exists"):
            tag_service.create_tag("python", "programming")

    def test_get_tag_by_id(self, tag_service):
        """Test retrieving tag by ID."""
        tag = tag_service.create_tag("JavaScript", "programming")

        retrieved = tag_service.get_tag_by_id(tag.id)
        assert retrieved.id == tag.id
        assert retrieved.name == "javascript"

    def test_get_tag_by_id_not_found(self, tag_service):
        """Test getting non-existent tag by ID raises error."""
        with pytest.raises(TagNotFoundError, match="not found"):
            tag_service.get_tag_by_id(99999)

    def test_get_tag_by_name(self, tag_service):
        """Test retrieving tag by name."""
        tag_service.create_tag("Ruby", "programming")

        tag = tag_service.get_tag_by_name("Ruby")
        assert tag is not None
        assert tag.name == "ruby"

    def test_get_tag_by_name_normalizes(self, tag_service):
        """Test that get_tag_by_name normalizes the search name."""
        tag_service.create_tag("Go Lang", "programming")

        tag = tag_service.get_tag_by_name("GO_LANG")
        assert tag is not None
        assert tag.name == "go-lang"

    def test_get_tag_by_name_not_found(self, tag_service):
        """Test getting non-existent tag by name returns None."""
        tag = tag_service.get_tag_by_name("NonExistent")
        assert tag is None

    def test_get_or_create_tag_creates_new(self, tag_service):
        """Test get_or_create creates tag when it doesn't exist."""
        tag = tag_service.get_or_create_tag("TypeScript", "programming")

        assert tag.id is not None
        assert tag.name == "typescript"
        assert tag.category == "programming"

    def test_get_or_create_tag_returns_existing(self, tag_service):
        """Test get_or_create returns existing tag."""
        tag1 = tag_service.create_tag("Rust", "programming")
        tag2 = tag_service.get_or_create_tag("Rust", "programming")

        assert tag1.id == tag2.id

    def test_get_or_create_tag_updates_category(self, tag_service):
        """Test get_or_create updates category if different."""
        tag1 = tag_service.create_tag("Docker", "tools")
        tag2 = tag_service.get_or_create_tag("Docker", "devops")

        assert tag1.id == tag2.id
        assert tag2.category == "devops"

    def test_get_all_tags(self, tag_service):
        """Test retrieving all tags."""
        tag_service.create_tag("Python", "programming")
        tag_service.create_tag("AWS", "cloud")
        tag_service.create_tag("Docker", "devops")

        tags = tag_service.get_all_tags()
        assert len(tags) == 3

    def test_get_all_tags_filtered_by_category(self, tag_service):
        """Test retrieving tags filtered by category."""
        tag_service.create_tag("Python", "programming")
        tag_service.create_tag("JavaScript", "programming")
        tag_service.create_tag("AWS", "cloud")

        programming_tags = tag_service.get_all_tags(category="programming")
        assert len(programming_tags) == 2
        assert all(tag.category == "programming" for tag in programming_tags)

    def test_get_tags_by_category(self, tag_service):
        """Test grouping tags by category."""
        tag_service.create_tag("Python", "programming")
        tag_service.create_tag("JavaScript", "programming")
        tag_service.create_tag("AWS", "cloud")
        tag_service.create_tag("Docker")  # No category

        grouped = tag_service.get_tags_by_category()

        assert "programming" in grouped
        assert len(grouped["programming"]) == 2
        assert "cloud" in grouped
        assert len(grouped["cloud"]) == 1
        assert "uncategorized" in grouped
        assert len(grouped["uncategorized"]) == 1

    def test_update_tag_name(self, tag_service):
        """Test updating tag name."""
        tag = tag_service.create_tag("Python2", "programming")

        updated = tag_service.update_tag(tag.id, name="Python 3")
        assert updated.name == "python-3"

    def test_update_tag_category(self, tag_service):
        """Test updating tag category."""
        tag = tag_service.create_tag("Kubernetes", "tools")

        updated = tag_service.update_tag(tag.id, category="devops")
        assert updated.category == "devops"

    def test_update_tag_name_conflict(self, tag_service):
        """Test updating tag name to existing name raises error."""
        tag1 = tag_service.create_tag("Python", "programming")
        tag2 = tag_service.create_tag("JavaScript", "programming")

        with pytest.raises(TagServiceError, match="already exists"):
            tag_service.update_tag(tag2.id, name="Python")

    def test_update_tag_not_found(self, tag_service):
        """Test updating non-existent tag raises error."""
        with pytest.raises(TagNotFoundError):
            tag_service.update_tag(99999, name="NewName")

    def test_delete_tag(self, tag_service):
        """Test deleting a tag."""
        tag = tag_service.create_tag("Obsolete", "deprecated")
        tag_id = tag.id

        tag_service.delete_tag(tag_id)

        with pytest.raises(TagNotFoundError):
            tag_service.get_tag_by_id(tag_id)

    def test_delete_tag_in_use_without_force(self, tag_service, sample_bullet_point, session):
        """Test deleting tag in use without force raises error."""
        # Create a tag and associate it with a bullet point
        tag = tag_service.create_tag("InUse", "test")
        bullet_tag = BulletTag(bullet_point_id=sample_bullet_point.id, tag_id=tag.id)
        session.add(bullet_tag)
        session.commit()

        with pytest.raises(TagServiceError, match="is used by"):
            tag_service.delete_tag(tag.id, force=False)

    def test_delete_tag_in_use_with_force(self, tag_service, sample_bullet_point, session):
        """Test deleting tag in use with force succeeds."""
        # Create a tag and associate it with a bullet point
        tag = tag_service.create_tag("InUse", "test")
        bullet_tag = BulletTag(bullet_point_id=sample_bullet_point.id, tag_id=tag.id)
        session.add(bullet_tag)
        session.commit()

        tag_service.delete_tag(tag.id, force=True)

        with pytest.raises(TagNotFoundError):
            tag_service.get_tag_by_id(tag.id)

    def test_delete_tag_not_found(self, tag_service):
        """Test deleting non-existent tag raises error."""
        with pytest.raises(TagNotFoundError):
            tag_service.delete_tag(99999)

    def test_find_matching_tags_exact_match(self, tag_service):
        """Test finding tags with exact name match."""
        tag_service.create_tag("programming", "technical")
        tag_service.create_tag("database", "technical")

        text = "Looking for programming and database skills"
        matches = tag_service.find_matching_tags(text)

        assert len(matches) == 2
        tag_names = [tag.name for tag, score in matches]
        assert "programming" in tag_names
        assert "database" in tag_names

    def test_find_matching_tags_synonym_match(self, tag_service):
        """Test finding tags using synonym matching."""
        tag_service.create_tag("programming", "technical")

        text = "Experience with software development and coding"
        matches = tag_service.find_matching_tags(text, threshold=0.3)

        # "software development" and "coding" are synonyms of "programming"
        assert len(matches) >= 1
        assert matches[0][0].name == "programming"

    def test_find_matching_tags_threshold(self, tag_service):
        """Test threshold filtering in tag matching."""
        tag_service.create_tag("programming", "technical")

        text = "Experience with software development"

        # High threshold should filter out weak matches
        high_threshold_matches = tag_service.find_matching_tags(text, threshold=0.99)
        low_threshold_matches = tag_service.find_matching_tags(text, threshold=0.3)

        assert len(low_threshold_matches) >= len(high_threshold_matches)

    def test_find_matching_tags_category_weights(self, tag_service):
        """Test that category weights affect scores."""
        # Technical tags get higher weight
        tech_tag = tag_service.create_tag("programming", "technical")
        soft_tag = tag_service.create_tag("communication", "soft-skills")

        text = "programming and communication skills needed"
        matches = tag_service.find_matching_tags(text)

        # Programming should score higher due to category weight
        tag_scores = {tag.name: score for tag, score in matches}
        if "programming" in tag_scores and "communication" in tag_scores:
            assert tag_scores["programming"] > tag_scores["communication"]

    def test_suggest_tags_for_text(self, tag_service):
        """Test suggesting tags for text."""
        tag_service.create_tag("python", "programming")
        tag_service.create_tag("aws", "cloud")
        tag_service.create_tag("docker", "devops")
        tag_service.create_tag("kubernetes", "devops")

        text = "Need Python developer with AWS and Docker experience"
        suggestions = tag_service.suggest_tags_for_text(text, max_suggestions=5)

        assert len(suggestions) <= 5
        suggested_names = [tag.name for tag in suggestions]
        assert "python" in suggested_names
        assert "aws" in suggested_names

    def test_suggest_tags_respects_max_suggestions(self, tag_service):
        """Test that suggestion limit is respected."""
        for i in range(10):
            tag_service.create_tag(f"tag{i}", "test")

        text = " ".join([f"tag{i}" for i in range(10)])
        suggestions = tag_service.suggest_tags_for_text(text, max_suggestions=3)

        assert len(suggestions) == 3

    def test_expand_tag_query_includes_synonyms(self, tag_service):
        """Test expanding tag query includes synonyms."""
        expanded = tag_service.expand_tag_query(["programming"])

        # Should include programming and its synonyms
        assert "programming" in expanded
        assert "coding" in expanded
        assert "development" in expanded

    def test_expand_tag_query_reverse_mapping(self, tag_service):
        """Test expanding synonym returns primary tag."""
        # "coding" is a synonym of "programming"
        expanded = tag_service.expand_tag_query(["coding"])

        assert "programming" in expanded
        assert "coding" in expanded

    def test_seed_predefined_tags(self, tag_service):
        """Test seeding predefined tags."""
        count = tag_service.seed_predefined_tags()

        assert count > 0

        # Verify some tags were created
        programming_tag = tag_service.get_tag_by_name("programming")
        assert programming_tag is not None
        assert programming_tag.category == "technical"

    def test_seed_predefined_tags_idempotent(self, tag_service):
        """Test seeding tags multiple times doesn't create duplicates."""
        count1 = tag_service.seed_predefined_tags()
        count2 = tag_service.seed_predefined_tags()

        # Second run should create 0 new tags
        all_tags = tag_service.get_all_tags()
        assert len(all_tags) == count1

    def test_normalize_tag_name(self, tag_service):
        """Test tag name normalization."""
        assert tag_service._normalize_tag_name("Python") == "python"
        assert tag_service._normalize_tag_name("Machine Learning") == "machine-learning"
        assert tag_service._normalize_tag_name("FULL_STACK") == "full-stack"
        assert tag_service._normalize_tag_name("  API Development  ") == "api-development"

    def test_build_synonym_cache(self, tag_service):
        """Test building synonym cache."""
        tag_service._build_synonym_cache()

        assert tag_service._synonym_cache is not None
        assert tag_service._reverse_synonym_cache is not None

        # Check forward mapping
        assert "programming" in tag_service._synonym_cache
        assert "coding" in tag_service._synonym_cache["programming"]

        # Check reverse mapping
        assert "coding" in tag_service._reverse_synonym_cache
        assert tag_service._reverse_synonym_cache["coding"] == "programming"

    def test_synonym_cache_lazy_loading(self, tag_service):
        """Test that synonym cache is built on first use."""
        assert tag_service._synonym_cache is None

        # Trigger cache build
        tag_service.create_tag("programming", "technical")
        text = "software development experience"
        tag_service.find_matching_tags(text)

        assert tag_service._synonym_cache is not None

    def test_empty_database(self, tag_service):
        """Test operations on empty database."""
        tags = tag_service.get_all_tags()
        assert tags == []

        grouped = tag_service.get_tags_by_category()
        assert grouped == {}

    def test_tag_with_no_category(self, tag_service):
        """Test creating and managing tags without category."""
        tag = tag_service.create_tag("Miscellaneous")

        assert tag.category is None

        grouped = tag_service.get_tags_by_category()
        assert "uncategorized" in grouped
        assert tag in grouped["uncategorized"]
