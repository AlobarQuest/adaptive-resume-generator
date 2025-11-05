"""
Unit tests for the Profile model.

Tests cover:
- Profile creation and validation
- Relationships (jobs, skills, education, etc.)
- Properties (full_name)
- Methods (to_dict)
"""

import pytest
from adaptive_resume.models import Profile


class TestProfileModel:
    """Test suite for Profile model."""
    
    def test_create_profile(self, session):
        """Test creating a basic profile."""
        profile = Profile(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com"
        )
        session.add(profile)
        session.commit()
        
        assert profile.id is not None
        assert profile.first_name == "Jane"
        assert profile.last_name == "Smith"
        assert profile.email == "jane.smith@example.com"
    
    def test_profile_full_name(self, sample_profile):
        """Test the full_name property."""
        assert sample_profile.full_name == "John Doe"
    
    def test_profile_with_optional_fields(self, session):
        """Test creating a profile with all optional fields."""
        profile = Profile(
            first_name="Alice",
            last_name="Johnson",
            email="alice@example.com",
            phone="555-999-8888",
            city="San Francisco",
            state="California",
            linkedin_url="https://linkedin.com/in/alice",
            portfolio_url="https://alice.dev",
            professional_summary="Full-stack developer with 5 years experience."
        )
        session.add(profile)
        session.commit()
        
        assert profile.phone == "555-999-8888"
        assert profile.city == "San Francisco"
        assert profile.state == "California"
        assert profile.linkedin_url == "https://linkedin.com/in/alice"
        assert profile.portfolio_url == "https://alice.dev"
        assert "Full-stack developer" in profile.professional_summary
    
    def test_profile_unique_email(self, session, sample_profile):
        """Test that email must be unique."""
        duplicate_profile = Profile(
            first_name="Another",
            last_name="Person",
            email="john.doe@example.com"  # Same email as sample_profile
        )
        session.add(duplicate_profile)
        
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            session.commit()
    
    def test_profile_to_dict(self, sample_profile):
        """Test converting profile to dictionary."""
        profile_dict = sample_profile.to_dict()
        
        assert isinstance(profile_dict, dict)
        assert profile_dict['first_name'] == "John"
        assert profile_dict['last_name'] == "Doe"
        assert profile_dict['full_name'] == "John Doe"
        assert profile_dict['email'] == "john.doe@example.com"
        assert 'created_at' in profile_dict
        assert 'updated_at' in profile_dict
    
    def test_profile_repr(self, sample_profile):
        """Test string representation of profile."""
        repr_str = repr(sample_profile)
        assert "Profile" in repr_str
        assert "John Doe" in repr_str
        assert "john.doe@example.com" in repr_str
    
    def test_profile_relationships(self, sample_profile, sample_job, sample_skill):
        """Test profile relationships to other entities."""
        # Profile should have relationships
        assert len(sample_profile.jobs) == 1
        assert sample_profile.jobs[0].company_name == "TechCorp"
        
        assert len(sample_profile.skills) == 1
        assert sample_profile.skills[0].skill_name == "Python"
    
    def test_profile_cascade_delete(self, session, sample_profile, sample_job):
        """Test that deleting profile cascades to related entities."""
        profile_id = sample_profile.id
        job_id = sample_job.id
        
        # Delete profile
        session.delete(sample_profile)
        session.commit()
        
        # Profile should be gone
        assert session.query(Profile).filter_by(id=profile_id).first() is None
        
        # Job should also be deleted (cascade)
        from adaptive_resume.models import Job
        assert session.query(Job).filter_by(id=job_id).first() is None
    
    def test_profile_timestamps(self, session):
        """Test that timestamps are automatically set."""
        profile = Profile(
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        session.add(profile)
        session.commit()
        
        assert profile.created_at is not None
        assert profile.updated_at is not None
        assert profile.created_at == profile.updated_at
