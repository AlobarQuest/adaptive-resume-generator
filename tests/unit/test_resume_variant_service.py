"""Unit tests for ResumeVariantService."""

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from adaptive_resume.models.base import Base
from adaptive_resume.models.profile import Profile
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.models.tailored_resume import TailoredResumeModel
from adaptive_resume.services.resume_variant_service import ResumeVariantService, VariantComparison


@pytest.fixture
def session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def profile(session):
    """Create a test profile."""
    profile = Profile(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        phone="555-1234",
        city="Test City"
    )
    session.add(profile)
    session.commit()
    return profile


@pytest.fixture
def job_posting(session, profile):
    """Create a test job posting."""
    job_posting = JobPosting(
        profile_id=profile.id,
        company_name="Test Company",
        job_title="Software Engineer",
        raw_text="Test job description",
        requirements_json=json.dumps({"skills": ["Python", "SQL"]})
    )
    session.add(job_posting)
    session.commit()
    return job_posting


@pytest.fixture
def base_resume(session, profile, job_posting):
    """Create a base tailored resume."""
    resume = TailoredResumeModel(
        profile_id=profile.id,
        job_posting_id=job_posting.id,
        selected_accomplishment_ids=json.dumps([1, 2, 3]),
        skill_coverage_json=json.dumps({"Python": True, "SQL": True, "AWS": False}),
        coverage_percentage=0.67,
        gaps_json=json.dumps(["AWS"]),
        recommendations_json=json.dumps(["Add AWS experience"]),
        match_score=0.75,
        variant_name=None,
        variant_number=1,
        is_primary=True
    )
    session.add(resume)
    session.commit()
    return resume


class TestResumeVariantService:
    """Tests for ResumeVariantService."""

    def test_create_variant(self, session, base_resume):
        """Test creating a new variant."""
        service = ResumeVariantService(session)

        variant = service.create_variant(
            base_resume_id=base_resume.id,
            variant_name="Technical",
            notes="Technical-focused variant"
        )

        assert variant.id is not None
        assert variant.variant_name == "Technical"
        assert variant.variant_number == 2
        assert variant.parent_variant_id == base_resume.id
        assert variant.is_primary is False
        assert variant.notes == "Technical-focused variant"
        assert variant.job_posting_id == base_resume.job_posting_id
        assert variant.profile_id == base_resume.profile_id
        # Should clone the accomplishments
        assert variant.selected_accomplishment_ids == base_resume.selected_accomplishment_ids

    def test_create_variant_with_modifications(self, session, base_resume):
        """Test creating a variant with custom modifications."""
        service = ResumeVariantService(session)

        new_accomplishments = json.dumps([1, 2, 4, 5])  # Different accomplishments
        variant = service.create_variant(
            base_resume_id=base_resume.id,
            variant_name="Conservative",
            modifications={
                "selected_accomplishment_ids": new_accomplishments,
                "match_score": 0.80
            }
        )

        assert variant.selected_accomplishment_ids == new_accomplishments
        assert variant.match_score == 0.80

    def test_create_variant_duplicate_name_error(self, session, base_resume):
        """Test that creating a variant with duplicate name raises error."""
        service = ResumeVariantService(session)

        # Create first variant
        service.create_variant(
            base_resume_id=base_resume.id,
            variant_name="Technical"
        )

        # Try to create another with same name
        with pytest.raises(ValueError, match="already exists"):
            service.create_variant(
                base_resume_id=base_resume.id,
                variant_name="Technical"
            )

    def test_create_variant_invalid_base_id(self, session):
        """Test creating variant with invalid base ID raises error."""
        service = ResumeVariantService(session)

        with pytest.raises(ValueError, match="not found"):
            service.create_variant(
                base_resume_id=99999,
                variant_name="Test"
            )

    def test_list_variants(self, session, base_resume):
        """Test listing all variants for a job posting."""
        service = ResumeVariantService(session)

        # Create additional variants
        service.create_variant(base_resume.id, "Technical")
        service.create_variant(base_resume.id, "Conservative")

        variants = service.list_variants(base_resume.job_posting_id)

        assert len(variants) == 3
        assert variants[0].variant_number == 1  # Base resume
        assert variants[1].variant_number == 2  # Technical
        assert variants[2].variant_number == 3  # Conservative

    def test_list_variants_empty(self, session, job_posting):
        """Test listing variants when none exist."""
        service = ResumeVariantService(session)

        variants = service.list_variants(job_posting.id)

        assert len(variants) == 0

    def test_compare_variants(self, session, base_resume):
        """Test comparing multiple variants."""
        service = ResumeVariantService(session)

        # Create variants with different accomplishments
        variant1 = service.create_variant(
            base_resume.id,
            "Technical",
            modifications={
                "selected_accomplishment_ids": json.dumps([1, 2, 4])
            }
        )

        variant2 = service.create_variant(
            base_resume.id,
            "Conservative",
            modifications={
                "selected_accomplishment_ids": json.dumps([1, 3])
            }
        )

        comparison = service.compare_variants([base_resume.id, variant1.id, variant2.id])

        assert isinstance(comparison, VariantComparison)
        assert len(comparison.variants) == 3
        assert comparison.metadata["variant_count"] == 3
        assert comparison.metadata["job_posting_id"] == base_resume.job_posting_id

        # Check accomplishment comparison
        acc_diff = comparison.accomplishment_diffs
        assert len(acc_diff["common_accomplishments"]) == 1  # Only [1] is common
        assert acc_diff["total_unique_accomplishments"] == 4  # 1,2,3,4

    def test_compare_variants_invalid_count(self, session, base_resume):
        """Test that comparing wrong number of variants raises error."""
        service = ResumeVariantService(session)

        # Only one variant
        with pytest.raises(ValueError, match="between 2 and 3"):
            service.compare_variants([base_resume.id])

        # Too many variants
        variant1 = service.create_variant(base_resume.id, "V1")
        variant2 = service.create_variant(base_resume.id, "V2")
        variant3 = service.create_variant(base_resume.id, "V3")

        with pytest.raises(ValueError, match="between 2 and 3"):
            service.compare_variants([
                base_resume.id,
                variant1.id,
                variant2.id,
                variant3.id
            ])

    def test_compare_variants_different_jobs(self, session, profile, base_resume):
        """Test that comparing variants from different jobs raises error."""
        service = ResumeVariantService(session)

        # Create another job posting and resume
        job2 = JobPosting(
            profile_id=profile.id,
            company_name="Company 2",
            job_title="Data Scientist",
            raw_text="Different job"
        )
        session.add(job2)
        session.commit()

        resume2 = TailoredResumeModel(
            profile_id=profile.id,
            job_posting_id=job2.id,
            selected_accomplishment_ids=json.dumps([1]),
            variant_number=1,
            is_primary=True
        )
        session.add(resume2)
        session.commit()

        # Try to compare variants from different jobs
        with pytest.raises(ValueError, match="same job posting"):
            service.compare_variants([base_resume.id, resume2.id])

    def test_clone_variant(self, session, base_resume):
        """Test cloning a variant."""
        service = ResumeVariantService(session)

        # Create a variant
        original = service.create_variant(
            base_resume.id,
            "Technical",
            notes="Original notes"
        )

        # Clone it
        clone = service.clone_variant(
            source_id=original.id,
            new_name="Technical v2",
            notes="Cloned variant"
        )

        assert clone.id != original.id
        assert clone.variant_name == "Technical v2"
        assert clone.variant_number == 3  # base=1, original=2, clone=3
        assert clone.parent_variant_id == original.id
        assert clone.notes == "Cloned variant"
        assert clone.selected_accomplishment_ids == original.selected_accomplishment_ids

    def test_mark_as_primary(self, session, base_resume):
        """Test marking a variant as primary."""
        service = ResumeVariantService(session)

        # Create a variant
        variant = service.create_variant(base_resume.id, "Technical")

        # Initially, base_resume should be primary
        assert base_resume.is_primary is True
        assert variant.is_primary is False

        # Mark variant as primary
        service.mark_as_primary(variant.id)
        session.refresh(base_resume)
        session.refresh(variant)

        assert base_resume.is_primary is False
        assert variant.is_primary is True

    def test_mark_as_primary_invalid_id(self, session):
        """Test marking nonexistent variant as primary raises error."""
        service = ResumeVariantService(session)

        with pytest.raises(ValueError, match="not found"):
            service.mark_as_primary(99999)

    def test_track_performance(self, session, base_resume):
        """Test tracking performance metrics."""
        service = ResumeVariantService(session)

        metrics = {
            "interview_rate": 0.5,
            "response_time_days": 7,
            "application_count": 10
        }

        service.track_performance(base_resume.id, metrics)
        session.refresh(base_resume)

        stored_metrics = json.loads(base_resume.performance_metrics)
        assert stored_metrics["interview_rate"] == 0.5
        assert stored_metrics["response_time_days"] == 7
        assert stored_metrics["application_count"] == 10

    def test_track_performance_merge(self, session, base_resume):
        """Test that tracking performance merges with existing metrics."""
        service = ResumeVariantService(session)

        # Set initial metrics
        initial_metrics = {"interview_rate": 0.4}
        service.track_performance(base_resume.id, initial_metrics)

        # Add more metrics
        new_metrics = {"response_time_days": 5, "interview_rate": 0.5}
        service.track_performance(base_resume.id, new_metrics)
        session.refresh(base_resume)

        stored_metrics = json.loads(base_resume.performance_metrics)
        assert stored_metrics["interview_rate"] == 0.5  # Updated
        assert stored_metrics["response_time_days"] == 5  # Added

    def test_delete_variant(self, session, base_resume):
        """Test deleting a variant."""
        service = ResumeVariantService(session)

        # Create a variant
        variant = service.create_variant(base_resume.id, "Technical")

        # Delete it
        service.delete_variant(variant.id)

        # Verify deletion
        deleted = session.query(TailoredResumeModel).filter_by(id=variant.id).first()
        assert deleted is None

    def test_delete_variant_only_one_error(self, session, base_resume):
        """Test that deleting the only variant raises error."""
        service = ResumeVariantService(session)

        with pytest.raises(ValueError, match="only variant"):
            service.delete_variant(base_resume.id)

    def test_delete_primary_variant_promotes_next(self, session, base_resume):
        """Test that deleting primary variant promotes the next one."""
        service = ResumeVariantService(session)

        # Create a variant
        variant = service.create_variant(base_resume.id, "Technical")

        # base_resume is primary, delete it
        service.delete_variant(base_resume.id)

        # variant should now be primary
        session.refresh(variant)
        assert variant.is_primary is True

    def test_update_variant(self, session, base_resume):
        """Test updating variant fields."""
        service = ResumeVariantService(session)

        service.update_variant(
            variant_id=base_resume.id,
            variant_name="Updated Name",
            notes="Updated notes",
            match_score=0.85
        )

        session.refresh(base_resume)
        assert base_resume.variant_name == "Updated Name"
        assert base_resume.notes == "Updated notes"
        assert base_resume.match_score == 0.85

    def test_update_variant_invalid_id(self, session):
        """Test updating nonexistent variant raises error."""
        service = ResumeVariantService(session)

        with pytest.raises(ValueError, match="not found"):
            service.update_variant(variant_id=99999, notes="test")

    def test_get_next_variant_number(self, session, base_resume):
        """Test getting next variant number."""
        service = ResumeVariantService(session)

        # First variant should be 2 (base is 1)
        next_num = service._get_next_variant_number(base_resume.job_posting_id)
        assert next_num == 2

        # Create a variant
        service.create_variant(base_resume.id, "Technical")

        # Next should be 3
        next_num = service._get_next_variant_number(base_resume.job_posting_id)
        assert next_num == 3

    def test_compare_skill_coverage(self, session, base_resume):
        """Test skill coverage comparison."""
        service = ResumeVariantService(session)

        # Create variant with different skill coverage
        variant = service.create_variant(
            base_resume.id,
            "Technical",
            modifications={
                "skill_coverage_json": json.dumps({"Python": True, "SQL": False, "AWS": True}),
                "coverage_percentage": 0.67
            }
        )

        comparison = service.compare_variants([base_resume.id, variant.id])

        skill_diff = comparison.skill_diffs
        assert len(skill_diff["by_variant"]) == 2

        # Base resume: Python=T, SQL=T, AWS=F
        base_diff = skill_diff["by_variant"][0]
        assert len(base_diff["covered_skills"]) == 2  # Python, SQL
        assert len(base_diff["missing_skills"]) == 1  # AWS

        # Variant: Python=T, SQL=F, AWS=T
        variant_diff = skill_diff["by_variant"][1]
        assert len(variant_diff["covered_skills"]) == 2  # Python, AWS
        assert len(variant_diff["missing_skills"]) == 1  # SQL

    def test_variant_auto_increment(self, session, base_resume):
        """Test that variant numbers auto-increment correctly."""
        service = ResumeVariantService(session)

        v1 = service.create_variant(base_resume.id, "V1")
        v2 = service.create_variant(base_resume.id, "V2")
        v3 = service.create_variant(base_resume.id, "V3")

        assert base_resume.variant_number == 1
        assert v1.variant_number == 2
        assert v2.variant_number == 3
        assert v3.variant_number == 4

    def test_variant_preserves_parent_id(self, session, base_resume):
        """Test that variants preserve parent_variant_id correctly."""
        service = ResumeVariantService(session)

        # Create variant from base
        v1 = service.create_variant(base_resume.id, "V1")
        assert v1.parent_variant_id == base_resume.id

        # Create variant from v1
        v2 = service.create_variant(v1.id, "V2")
        assert v2.parent_variant_id == v1.id

        # All should still reference the same job posting
        assert base_resume.job_posting_id == v1.job_posting_id == v2.job_posting_id
