"""
Unit tests for the Job model.

Tests cover:
- Job creation and validation
- Date constraints
- Relationships to Profile and BulletPoints
- Properties (date_range, duration_months)
- Methods (to_dict)
"""

import pytest
from datetime import date
from adaptive_resume.models import Job


class TestJobModel:
    """Test suite for Job model."""
    
    def test_create_job(self, session, sample_profile):
        """Test creating a basic job."""
        job = Job(
            profile_id=sample_profile.id,
            company_name="NewCorp",
            job_title="Software Developer",
            start_date=date(2018, 6, 1),
            end_date=date(2020, 12, 31),
            is_current=False
        )
        session.add(job)
        session.commit()
        
        assert job.id is not None
        assert job.company_name == "NewCorp"
        assert job.job_title == "Software Developer"
        assert job.is_current is False
    
    def test_job_date_range_property(self, sample_job):
        """Test the date_range property."""
        date_range = sample_job.date_range
        assert "January 2020" in date_range
        assert "December 2023" in date_range
    
    def test_job_current_position(self, session, sample_profile):
        """Test creating a current position."""
        job = Job(
            profile_id=sample_profile.id,
            company_name="CurrentCorp",
            job_title="CTO",
            start_date=date(2023, 1, 1),
            end_date=None,
            is_current=True
        )
        session.add(job)
        session.commit()
        
        assert job.is_current is True
        assert job.end_date is None
        assert "Present" in job.date_range
    
    def test_job_duration_months(self, sample_job):
        """Test calculating job duration in months."""
        # Job is from 2020-01-01 to 2023-12-31
        # Duration calculation: (2023-2020)*12 + (12-1) = 3*12 + 11 = 47 months
        duration = sample_job.duration_months
        assert duration == 47
    
    def test_job_with_optional_fields(self, session, sample_profile):
        """Test creating job with all optional fields."""
        job = Job(
            profile_id=sample_profile.id,
            company_name="FullCorp",
            job_title="Lead Engineer",
            location="New York, NY",
            start_date=date(2019, 3, 15),
            end_date=date(2021, 6, 30),
            is_current=False,
            description="Led team of 5 engineers developing web applications.",
            display_order=2
        )
        session.add(job)
        session.commit()
        
        assert job.location == "New York, NY"
        assert job.description == "Led team of 5 engineers developing web applications."
        assert job.display_order == 2
    
    def test_job_date_constraint(self, session, sample_profile):
        """Test that end_date must be after start_date."""
        job = Job(
            profile_id=sample_profile.id,
            company_name="BadCorp",
            job_title="Developer",
            start_date=date(2023, 1, 1),
            end_date=date(2022, 1, 1),  # Before start_date!
            is_current=False
        )
        session.add(job)
        
        with pytest.raises(Exception):  # Should violate check constraint
            session.commit()
    
    def test_job_current_with_end_date_constraint(self, session, sample_profile):
        """Test that current jobs cannot have end_date."""
        job = Job(
            profile_id=sample_profile.id,
            company_name="ConflictCorp",
            job_title="Engineer",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),  # Has end_date
            is_current=True  # But marked as current!
        )
        session.add(job)
        
        with pytest.raises(Exception):  # Should violate check constraint
            session.commit()
    
    def test_job_to_dict(self, sample_job):
        """Test converting job to dictionary."""
        job_dict = sample_job.to_dict()
        
        assert isinstance(job_dict, dict)
        assert job_dict['company_name'] == "TechCorp"
        assert job_dict['job_title'] == "Senior Software Engineer"
        assert job_dict['is_current'] is False
        assert 'date_range' in job_dict
        assert 'duration_months' in job_dict
        assert job_dict['bullet_points_count'] >= 0
    
    def test_job_repr(self, sample_job):
        """Test string representation of job."""
        repr_str = repr(sample_job)
        assert "Job" in repr_str
        assert "Senior Software Engineer" in repr_str
        assert "TechCorp" in repr_str
    
    def test_job_relationship_to_profile(self, sample_job, sample_profile):
        """Test job's relationship to profile."""
        assert sample_job.profile.id == sample_profile.id
        assert sample_job.profile.email == "john.doe@example.com"
    
    def test_job_relationship_to_bullet_points(self, sample_job, sample_bullet_point):
        """Test job's relationship to bullet points."""
        assert len(sample_job.bullet_points) == 1
        assert sample_job.bullet_points[0].content == sample_bullet_point.content
    
    def test_job_cascade_delete_to_bullets(self, session, sample_job, sample_bullet_point):
        """Test that deleting job cascades to bullet points."""
        job_id = sample_job.id
        bullet_id = sample_bullet_point.id
        
        # Delete job
        session.delete(sample_job)
        session.commit()
        
        # Job should be gone
        assert session.query(Job).filter_by(id=job_id).first() is None
        
        # Bullet point should also be deleted (cascade)
        from adaptive_resume.models import BulletPoint
        assert session.query(BulletPoint).filter_by(id=bullet_id).first() is None
