"""
Unit tests for ProfileService.

Tests cover:
- Profile creation with validation
- Profile retrieval (by ID, by email, all)
- Profile updates
- Profile deletion
- Error handling
- Business logic validation
"""

import pytest
from adaptive_resume.services.profile_service import (
    ProfileService,
    ProfileNotFoundError,
    ProfileValidationError,
    DuplicateEmailError
)


class TestProfileServiceCreate:
    """Test suite for profile creation."""
    
    def test_create_profile_basic(self, session):
        """Test creating a profile with minimal required fields."""
        service = ProfileService(session)
        
        profile = service.create_profile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        assert profile.id is not None
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.email == "john.doe@example.com"
    
    def test_create_profile_with_all_fields(self, session):
        """Test creating a profile with all optional fields."""
        service = ProfileService(session)
        
        profile = service.create_profile(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="555-123-4567",
            city="Atlanta",
            state="Georgia",
            linkedin_url="https://linkedin.com/in/janesmith",
            portfolio_url="https://janesmith.dev",
            professional_summary="Experienced developer"
        )
        
        assert profile.phone == "555-123-4567"
        assert profile.city == "Atlanta"
        assert profile.state == "Georgia"
        assert profile.linkedin_url == "https://linkedin.com/in/janesmith"
        assert profile.portfolio_url == "https://janesmith.dev"
        assert profile.professional_summary == "Experienced developer"
    
    def test_create_profile_strips_whitespace(self, session):
        """Test that whitespace is stripped from fields."""
        service = ProfileService(session)
        
        profile = service.create_profile(
            first_name="  John  ",
            last_name="  Doe  ",
            email="  john@example.com  "
        )
        
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.email == "john@example.com"
    
    def test_create_profile_email_lowercase(self, session):
        """Test that email is converted to lowercase."""
        service = ProfileService(session)
        
        profile = service.create_profile(
            first_name="John",
            last_name="Doe",
            email="John.Doe@EXAMPLE.COM"
        )
        
        assert profile.email == "john.doe@example.com"
    
    def test_create_profile_missing_first_name(self, session):
        """Test that first name is required."""
        service = ProfileService(session)
        
        with pytest.raises(ProfileValidationError, match="First name is required"):
            service.create_profile(
                first_name="",
                last_name="Doe",
                email="john@example.com"
            )
    
    def test_create_profile_missing_last_name(self, session):
        """Test that last name is required."""
        service = ProfileService(session)
        
        with pytest.raises(ProfileValidationError, match="Last name is required"):
            service.create_profile(
                first_name="John",
                last_name="",
                email="john@example.com"
            )
    
    def test_create_profile_missing_email(self, session):
        """Test that email is required."""
        service = ProfileService(session)
        
        with pytest.raises(ProfileValidationError, match="Email is required"):
            service.create_profile(
                first_name="John",
                last_name="Doe",
                email=""
            )
    
    def test_create_profile_invalid_email_format(self, session):
        """Test that email format is validated."""
        service = ProfileService(session)
        
        with pytest.raises(ProfileValidationError, match="Invalid email format"):
            service.create_profile(
                first_name="John",
                last_name="Doe",
                email="notanemail"
            )
    
    def test_create_profile_prevents_multiple_profiles(self, session):
        """Test that only one profile is allowed (single-profile mode)."""
        from adaptive_resume.services.profile_service import MultipleProfilesError
        service = ProfileService(session)

        # Create first profile
        service.create_profile(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )

        # Try to create second profile - should fail regardless of email
        with pytest.raises(MultipleProfilesError, match="Only one profile is allowed"):
            service.create_profile(
                first_name="Jane",
                last_name="Smith",
                email="different@example.com"  # Even different email should fail
            )
    
    def test_create_profile_invalid_linkedin_url(self, session):
        """Test that LinkedIn URL is validated."""
        service = ProfileService(session)
        
        with pytest.raises(ProfileValidationError, match="must start with http"):
            service.create_profile(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                linkedin_url="linkedin.com/in/johndoe"
            )


class TestProfileServiceRead:
    """Test suite for profile retrieval."""
    
    def test_get_profile_by_id(self, session, sample_profile):
        """Test retrieving profile by ID."""
        service = ProfileService(session)
        
        profile = service.get_profile_by_id(sample_profile.id)
        
        assert profile.id == sample_profile.id
        assert profile.email == sample_profile.email
    
    def test_get_profile_by_id_not_found(self, session):
        """Test that ProfileNotFoundError is raised for invalid ID."""
        service = ProfileService(session)
        
        with pytest.raises(ProfileNotFoundError, match="not found"):
            service.get_profile_by_id(99999)
    
    def test_get_profile_by_email(self, session, sample_profile):
        """Test retrieving profile by email."""
        service = ProfileService(session)
        
        profile = service.get_profile_by_email(sample_profile.email)
        
        assert profile is not None
        assert profile.id == sample_profile.id
    
    def test_get_profile_by_email_not_found(self, session):
        """Test that None is returned for non-existent email."""
        service = ProfileService(session)
        
        profile = service.get_profile_by_email("nonexistent@example.com")
        
        assert profile is None
    
    def test_get_default_profile_and_ensure_exists(self, session):
        """Test retrieving default profile and ensure_profile_exists (single-profile mode)."""
        service = ProfileService(session)

        # At first, no profile should exist
        profile = service.get_default_profile()
        assert profile is None

        # ensure_profile_exists should create a profile if none exists
        profile = service.ensure_profile_exists()
        assert profile is not None
        assert profile.id == 1

        # Calling again should return the same profile
        profile2 = service.ensure_profile_exists()
        assert profile2.id == profile.id

        # get_default_profile should now return the profile
        profile3 = service.get_default_profile()
        assert profile3.id == 1

        # Attempting to create a second profile should fail
        from adaptive_resume.services.profile_service import MultipleProfilesError
        with pytest.raises(MultipleProfilesError):
            service.create_profile("Second", "Profile", "second@example.com")
    
    def test_profile_exists(self, session, sample_profile):
        """Test checking if profile exists."""
        service = ProfileService(session)
        
        assert service.profile_exists(sample_profile.id) is True
        assert service.profile_exists(99999) is False


class TestProfileServiceUpdate:
    """Test suite for profile updates."""
    
    def test_update_profile_first_name(self, session, sample_profile):
        """Test updating first name."""
        service = ProfileService(session)
        
        updated = service.update_profile(
            profile_id=sample_profile.id,
            first_name="Jonathan"
        )
        
        assert updated.first_name == "Jonathan"
        assert updated.last_name == sample_profile.last_name  # Unchanged
    
    def test_update_profile_multiple_fields(self, session, sample_profile):
        """Test updating multiple fields at once."""
        service = ProfileService(session)
        
        updated = service.update_profile(
            profile_id=sample_profile.id,
            first_name="Jonathan",
            city="San Francisco",
            state="California"
        )
        
        assert updated.first_name == "Jonathan"
        assert updated.city == "San Francisco"
        assert updated.state == "California"
    
    def test_update_profile_email(self, session, sample_profile):
        """Test updating email."""
        service = ProfileService(session)
        
        updated = service.update_profile(
            profile_id=sample_profile.id,
            email="newemail@example.com"
        )
        
        assert updated.email == "newemail@example.com"
    
    @pytest.mark.skip(reason="Single-profile mode: duplicate email checking not applicable with only one profile")
    def test_update_profile_email_duplicate(self, session):
        """Test that duplicate email is prevented on update (obsolete in single-profile mode)."""
        pass
    
    def test_update_profile_not_found(self, session):
        """Test updating non-existent profile."""
        service = ProfileService(session)
        
        with pytest.raises(ProfileNotFoundError):
            service.update_profile(
                profile_id=99999,
                first_name="John"
            )
    
    def test_update_profile_empty_first_name(self, session, sample_profile):
        """Test that empty first name is not allowed."""
        service = ProfileService(session)
        
        with pytest.raises(ProfileValidationError, match="cannot be empty"):
            service.update_profile(
                profile_id=sample_profile.id,
                first_name=""
            )
    
    def test_update_profile_clear_optional_field(self, session, sample_profile):
        """Test clearing an optional field."""
        service = ProfileService(session)
        
        # First set a value
        service.update_profile(
            profile_id=sample_profile.id,
            phone="555-123-4567"
        )
        
        # Then clear it
        updated = service.update_profile(
            profile_id=sample_profile.id,
            phone=""
        )
        
        assert updated.phone is None


class TestProfileServiceDelete:
    """Test suite for profile deletion."""
    
    def test_delete_profile(self, session, sample_profile):
        """Test deleting a profile."""
        service = ProfileService(session)
        
        profile_id = sample_profile.id
        
        service.delete_profile(profile_id)
        
        # Profile should no longer exist
        assert service.profile_exists(profile_id) is False
    
    def test_delete_profile_not_found(self, session):
        """Test deleting non-existent profile."""
        service = ProfileService(session)
        
        with pytest.raises(ProfileNotFoundError):
            service.delete_profile(99999)
    
    def test_delete_profile_cascade(self, session, sample_profile, sample_job):
        """Test that deleting profile cascades to related data."""
        service = ProfileService(session)
        
        from adaptive_resume.models import Job
        
        profile_id = sample_profile.id
        job_id = sample_job.id
        
        # Delete profile
        service.delete_profile(profile_id)
        
        # Job should also be deleted (cascade)
        assert session.query(Job).filter_by(id=job_id).first() is None
