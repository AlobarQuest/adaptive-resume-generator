"""
Unit tests for JobService.

Tests cover:
- Job CRUD operations
- BulletPoint CRUD operations
- Tag management for bullet points
- Date validation
- Business logic validation
"""

import pytest
from datetime import date
from adaptive_resume.services.job_service import (
    JobService,
    JobNotFoundError,
    JobValidationError,
    BulletPointNotFoundError,
    BulletPointValidationError
)


class TestJobServiceCreate:
    """Test suite for job creation."""
    
    def test_create_job_basic(self, session, sample_profile):
        """Test creating a job with required fields."""
        service = JobService(session)
        
        job = service.create_job(
            profile_id=sample_profile.id,
            company_name="TechCorp",
            job_title="Software Engineer",
            start_date=date(2020, 1, 1)
        )
        
        assert job.id is not None
        assert job.company_name == "TechCorp"
        assert job.job_title == "Software Engineer"
        assert job.start_date == date(2020, 1, 1)
        assert job.is_current is False
    
    def test_create_job_current_position(self, session, sample_profile):
        """Test creating a current position."""
        service = JobService(session)
        
        job = service.create_job(
            profile_id=sample_profile.id,
            company_name="CurrentCorp",
            job_title="Senior Developer",
            start_date=date(2023, 1, 1),
            is_current=True
        )
        
        assert job.is_current is True
        assert job.end_date is None
    
    def test_create_job_with_all_fields(self, session, sample_profile):
        """Test creating job with all optional fields."""
        service = JobService(session)
        
        job = service.create_job(
            profile_id=sample_profile.id,
            company_name="FullCorp",
            job_title="Lead Engineer",
            location="San Francisco, CA",
            start_date=date(2019, 3, 15),
            end_date=date(2022, 6, 30),
            is_current=False,
            description="Led development team",
            display_order=1
        )
        
        assert job.location == "San Francisco, CA"
        assert job.description == "Led development team"
        assert job.display_order == 1
    
    def test_create_job_missing_company_name(self, session, sample_profile):
        """Test that company name is required."""
        service = JobService(session)
        
        with pytest.raises(JobValidationError, match="Company name is required"):
            service.create_job(
                profile_id=sample_profile.id,
                company_name="",
                job_title="Engineer",
                start_date=date(2020, 1, 1)
            )
    
    def test_create_job_missing_job_title(self, session, sample_profile):
        """Test that job title is required."""
        service = JobService(session)
        
        with pytest.raises(JobValidationError, match="Job title is required"):
            service.create_job(
                profile_id=sample_profile.id,
                company_name="TechCorp",
                job_title="",
                start_date=date(2020, 1, 1)
            )
    
    def test_create_job_invalid_profile(self, session):
        """Test that profile must exist."""
        service = JobService(session)
        
        with pytest.raises(JobValidationError, match="does not exist"):
            service.create_job(
                profile_id=99999,
                company_name="TechCorp",
                job_title="Engineer",
                start_date=date(2020, 1, 1)
            )
    
    def test_create_job_end_before_start(self, session, sample_profile):
        """Test that end date cannot be before start date."""
        service = JobService(session)
        
        with pytest.raises(JobValidationError, match="End date cannot be before start date"):
            service.create_job(
                profile_id=sample_profile.id,
                company_name="TechCorp",
                job_title="Engineer",
                start_date=date(2020, 1, 1),
                end_date=date(2019, 1, 1)
            )
    
    def test_create_job_current_with_end_date(self, session, sample_profile):
        """Test that current jobs cannot have end date."""
        service = JobService(session)
        
        with pytest.raises(JobValidationError, match="Current jobs cannot have an end date"):
            service.create_job(
                profile_id=sample_profile.id,
                company_name="TechCorp",
                job_title="Engineer",
                start_date=date(2020, 1, 1),
                end_date=date(2023, 1, 1),
                is_current=True
            )


class TestJobServiceRead:
    """Test suite for job retrieval."""
    
    def test_get_job_by_id(self, session, sample_job):
        """Test retrieving job by ID."""
        service = JobService(session)
        
        job = service.get_job_by_id(sample_job.id)
        
        assert job.id == sample_job.id
        assert job.company_name == sample_job.company_name
    
    def test_get_job_by_id_not_found(self, session):
        """Test that JobNotFoundError is raised for invalid ID."""
        service = JobService(session)
        
        with pytest.raises(JobNotFoundError, match="not found"):
            service.get_job_by_id(99999)
    
    def test_get_jobs_for_profile(self, session, sample_profile):
        """Test retrieving all jobs for a profile."""
        service = JobService(session)
        
        # Create multiple jobs
        service.create_job(
            profile_id=sample_profile.id,
            company_name="Company A",
            job_title="Engineer",
            start_date=date(2018, 1, 1),
            end_date=date(2020, 1, 1)
        )
        service.create_job(
            profile_id=sample_profile.id,
            company_name="Company B",
            job_title="Senior Engineer",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 1, 1)
        )
        
        jobs = service.get_jobs_for_profile(sample_profile.id)
        
        assert len(jobs) >= 2
        # Should be sorted by start date descending (newest first)
        assert jobs[0].start_date >= jobs[1].start_date


class TestJobServiceUpdate:
    """Test suite for job updates."""
    
    def test_update_job_company_name(self, session, sample_job):
        """Test updating company name."""
        service = JobService(session)
        
        updated = service.update_job(
            job_id=sample_job.id,
            company_name="NewCorp"
        )
        
        assert updated.company_name == "NewCorp"
    
    def test_update_job_multiple_fields(self, session, sample_job):
        """Test updating multiple fields."""
        service = JobService(session)
        
        updated = service.update_job(
            job_id=sample_job.id,
            job_title="Lead Engineer",
            location="New York, NY"
        )
        
        assert updated.job_title == "Lead Engineer"
        assert updated.location == "New York, NY"
    
    def test_update_job_not_found(self, session):
        """Test updating non-existent job."""
        service = JobService(session)
        
        with pytest.raises(JobNotFoundError):
            service.update_job(job_id=99999, company_name="Test")


class TestJobServiceDelete:
    """Test suite for job deletion."""
    
    def test_delete_job(self, session, sample_job):
        """Test deleting a job."""
        service = JobService(session)
        
        job_id = sample_job.id
        service.delete_job(job_id)
        
        with pytest.raises(JobNotFoundError):
            service.get_job_by_id(job_id)
    
    def test_delete_job_cascades_to_bullets(self, session, sample_job, sample_bullet_point):
        """Test that deleting job cascades to bullet points."""
        service = JobService(session)
        
        bullet_id = sample_bullet_point.id
        service.delete_job(sample_job.id)
        
        with pytest.raises(BulletPointNotFoundError):
            service.get_bullet_point_by_id(bullet_id)


class TestBulletPointServiceCreate:
    """Test suite for bullet point creation."""
    
    def test_create_bullet_point_basic(self, session, sample_job):
        """Test creating a bullet point with required fields."""
        service = JobService(session)
        
        bullet = service.create_bullet_point(
            job_id=sample_job.id,
            content="Developed microservices architecture"
        )
        
        assert bullet.id is not None
        assert bullet.content == "Developed microservices architecture"
        assert bullet.job_id == sample_job.id
    
    def test_create_bullet_point_with_all_fields(self, session, sample_job):
        """Test creating bullet with all optional fields."""
        service = JobService(session)
        
        bullet = service.create_bullet_point(
            job_id=sample_job.id,
            content="Optimized database queries",
            metrics="Reduced query time by 50%",
            impact="Improved user experience",
            display_order=1,
            is_highlighted=True
        )
        
        assert bullet.metrics == "Reduced query time by 50%"
        assert bullet.impact == "Improved user experience"
        assert bullet.is_highlighted is True
    
    def test_create_bullet_point_missing_content(self, session, sample_job):
        """Test that content is required."""
        service = JobService(session)
        
        with pytest.raises(BulletPointValidationError, match="content is required"):
            service.create_bullet_point(
                job_id=sample_job.id,
                content=""
            )
    
    def test_create_bullet_point_content_too_short(self, session, sample_job):
        """Test that content must be at least 10 characters."""
        service = JobService(session)
        
        with pytest.raises(BulletPointValidationError, match="at least 10 characters"):
            service.create_bullet_point(
                job_id=sample_job.id,
                content="Too short"
            )
    
    def test_create_bullet_point_content_too_long(self, session, sample_job):
        """Test that content cannot exceed 1000 characters."""
        service = JobService(session)
        
        long_content = "A" * 1001
        
        with pytest.raises(BulletPointValidationError, match="1000 characters or less"):
            service.create_bullet_point(
                job_id=sample_job.id,
                content=long_content
            )


class TestBulletPointServiceRead:
    """Test suite for bullet point retrieval."""
    
    def test_get_bullet_point_by_id(self, session, sample_bullet_point):
        """Test retrieving bullet point by ID."""
        service = JobService(session)
        
        bullet = service.get_bullet_point_by_id(sample_bullet_point.id)
        
        assert bullet.id == sample_bullet_point.id
    
    def test_get_bullet_points_for_job(self, session, sample_job):
        """Test retrieving all bullets for a job."""
        service = JobService(session)
        
        # Create multiple bullets
        service.create_bullet_point(
            job_id=sample_job.id,
            content="First achievement here",
            display_order=1
        )
        service.create_bullet_point(
            job_id=sample_job.id,
            content="Second achievement here",
            display_order=2
        )
        
        bullets = service.get_bullet_points_for_job(sample_job.id)
        
        assert len(bullets) >= 2
        # Should be ordered by display_order
        assert bullets[0].display_order <= bullets[1].display_order


class TestBulletPointServiceUpdate:
    """Test suite for bullet point updates."""
    
    def test_update_bullet_point_content(self, session, sample_bullet_point):
        """Test updating bullet content."""
        service = JobService(session)
        
        updated = service.update_bullet_point(
            bullet_id=sample_bullet_point.id,
            content="Updated content goes here"
        )
        
        assert updated.content == "Updated content goes here"
    
    def test_update_bullet_point_metrics(self, session, sample_bullet_point):
        """Test updating metrics."""
        service = JobService(session)
        
        updated = service.update_bullet_point(
            bullet_id=sample_bullet_point.id,
            metrics="New metrics: 75% improvement"
        )
        
        assert updated.metrics == "New metrics: 75% improvement"


class TestBulletPointServiceDelete:
    """Test suite for bullet point deletion."""
    
    def test_delete_bullet_point(self, session, sample_bullet_point):
        """Test deleting a bullet point."""
        service = JobService(session)
        
        bullet_id = sample_bullet_point.id
        service.delete_bullet_point(bullet_id)
        
        with pytest.raises(BulletPointNotFoundError):
            service.get_bullet_point_by_id(bullet_id)


class TestBulletPointTagManagement:
    """Test suite for tag management on bullet points."""
    
    def test_add_tags_to_bullet(self, seeded_session, sample_job):
        """Test adding tags to a bullet point."""
        service = JobService(seeded_session)
        
        bullet = service.create_bullet_point(
            job_id=sample_job.id,
            content="Implemented cloud infrastructure"
        )
        
        updated = service.add_tags_to_bullet(
            bullet_id=bullet.id,
            tag_names=["cloud", "programming"]
        )
        
        assert updated.has_tag("cloud")
        assert updated.has_tag("programming")
    
    def test_create_bullet_with_tags(self, seeded_session, sample_job):
        """Test creating bullet point with tags."""
        service = JobService(seeded_session)
        
        bullet = service.create_bullet_point(
            job_id=sample_job.id,
            content="Led team of engineers",
            tag_names=["leadership", "team-management"]
        )
        
        assert bullet.has_tag("leadership")
        assert bullet.has_tag("team-management")
    
    def test_remove_tag_from_bullet(self, seeded_session, sample_bullet_point):
        """Test removing a tag from bullet point."""
        service = JobService(seeded_session)
        
        # Bullet already has tags from fixture
        assert sample_bullet_point.has_tag("cloud")
        
        updated = service.remove_tag_from_bullet(
            bullet_id=sample_bullet_point.id,
            tag_name="cloud"
        )
        
        assert not updated.has_tag("cloud")
    
    def test_get_bullets_by_tag(self, seeded_session, sample_job):
        """Test finding bullets by tag."""
        service = JobService(seeded_session)
        
        # Create bullets with specific tags
        service.create_bullet_point(
            job_id=sample_job.id,
            content="Led agile sprint planning",
            tag_names=["leadership"]
        )
        service.create_bullet_point(
            job_id=sample_job.id,
            content="Mentored junior developers",
            tag_names=["leadership", "mentoring"]
        )
        
        bullets = service.get_bullets_by_tag("leadership")
        
        assert len(bullets) >= 2
        assert all(bullet.has_tag("leadership") for bullet in bullets)
