"""
ProfileService - Business logic for Profile operations.

This service handles all CRUD operations for user profiles,
including validation, business rules, and error handling.

Note: Desktop app enforces single-profile design. Only one profile (id=1)
is allowed per database. Multi-user support is planned for web version.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from adaptive_resume.models import Profile
from adaptive_resume.models.base import DEFAULT_PROFILE_ID


class ProfileServiceError(Exception):
    """Base exception for ProfileService errors."""
    pass


class ProfileNotFoundError(ProfileServiceError):
    """Raised when a profile cannot be found."""
    pass


class ProfileValidationError(ProfileServiceError):
    """Raised when profile validation fails."""
    pass


class DuplicateEmailError(ProfileServiceError):
    """Raised when attempting to create/update with duplicate email."""
    pass


class MultipleProfilesError(ProfileServiceError):
    """Raised when attempting to create a second profile (single-profile mode)."""
    pass


class ProfileService:
    """
    Service for managing user profiles.

    Provides CRUD operations with business logic validation.

    Desktop app enforces single-profile design: only one profile (id=1) per database.
    Use get_default_profile() or ensure_profile_exists() for single-profile access.
    """

    def __init__(self, session: Session):
        """
        Initialize the ProfileService.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_default_profile(self) -> Optional[Profile]:
        """
        Get the default (singleton) profile.

        Returns:
            Profile or None: The default profile (id=1) if it exists, None otherwise
        """
        return self.session.query(Profile).filter_by(id=DEFAULT_PROFILE_ID).first()

    def ensure_profile_exists(self) -> Profile:
        """
        Ensure a default profile exists, creating one if necessary.

        If no profile exists, creates a minimal profile that must be completed by user.

        Returns:
            Profile: The default profile
        """
        profile = self.get_default_profile()

        if profile is None:
            # Create a minimal profile that user must complete
            profile = Profile(
                id=DEFAULT_PROFILE_ID,
                first_name="",
                last_name="",
                email="user@example.com"  # Placeholder - should be updated
            )
            self.session.add(profile)
            self.session.commit()
            self.session.refresh(profile)

        return profile
    
    def create_profile(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        portfolio_url: Optional[str] = None,
        professional_summary: Optional[str] = None
    ) -> Profile:
        """
        Create a new profile.

        Desktop app: Only one profile is allowed. If a profile already exists, raises MultipleProfilesError.

        Args:
            first_name: User's first name
            last_name: User's last name
            email: User's email (must be unique)
            phone: Optional phone number
            city: Optional city
            state: Optional state
            linkedin_url: Optional LinkedIn profile URL
            portfolio_url: Optional portfolio/website URL
            professional_summary: Optional professional summary

        Returns:
            Profile: The created profile

        Raises:
            ProfileValidationError: If validation fails
            DuplicateEmailError: If email already exists
            MultipleProfilesError: If a profile already exists (single-profile mode)
        """
        # Check if profile already exists (single-profile enforcement)
        existing_profile = self.get_default_profile()
        if existing_profile is not None:
            raise MultipleProfilesError(
                "Only one profile is allowed in desktop mode. "
                "Please update the existing profile instead."
            )

        # Validate required fields
        self._validate_required_fields(first_name, last_name, email)

        # Validate email format
        self._validate_email(email)

        # Validate URLs if provided
        if linkedin_url:
            self._validate_url(linkedin_url, "LinkedIn URL")
        if portfolio_url:
            self._validate_url(portfolio_url, "Portfolio URL")

        # Create profile with explicit id=1
        profile = Profile(
            id=DEFAULT_PROFILE_ID,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.strip().lower(),
            phone=phone.strip() if phone else None,
            city=city.strip() if city else None,
            state=state.strip() if state else None,
            linkedin_url=linkedin_url.strip() if linkedin_url else None,
            portfolio_url=portfolio_url.strip() if portfolio_url else None,
            professional_summary=professional_summary.strip() if professional_summary else None
        )

        try:
            self.session.add(profile)
            self.session.commit()
            self.session.refresh(profile)
            return profile
        except IntegrityError as e:
            self.session.rollback()
            raise DuplicateEmailError(f"Profile with email '{email}' already exists") from e
    
    def get_profile_by_id(self, profile_id: int) -> Profile:
        """
        Get a profile by ID.
        
        Args:
            profile_id: The profile ID
            
        Returns:
            Profile: The profile
            
        Raises:
            ProfileNotFoundError: If profile not found
        """
        profile = self.session.query(Profile).filter_by(id=profile_id).first()
        
        if not profile:
            raise ProfileNotFoundError(f"Profile with id {profile_id} not found")
        
        return profile
    
    def get_profile_by_email(self, email: str) -> Optional[Profile]:
        """
        Get a profile by email.
        
        Args:
            email: The email address
            
        Returns:
            Profile or None: The profile if found, None otherwise
        """
        return self.session.query(Profile).filter_by(email=email.strip().lower()).first()
    
    def get_all_profiles(self) -> List[Profile]:
        """
        Get all profiles.
        
        Returns:
            List[Profile]: All profiles in the system
        """
        return self.session.query(Profile).order_by(Profile.last_name, Profile.first_name).all()
    
    def update_profile(
        self,
        profile_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        portfolio_url: Optional[str] = None,
        professional_summary: Optional[str] = None
    ) -> Profile:
        """
        Update a profile.
        
        Only provided fields will be updated. None values are ignored.
        
        Args:
            profile_id: The profile ID to update
            first_name: Optional new first name
            last_name: Optional new last name
            email: Optional new email
            phone: Optional new phone
            city: Optional new city
            state: Optional new state
            linkedin_url: Optional new LinkedIn URL
            portfolio_url: Optional new portfolio URL
            professional_summary: Optional new summary
            
        Returns:
            Profile: The updated profile
            
        Raises:
            ProfileNotFoundError: If profile not found
            ProfileValidationError: If validation fails
            DuplicateEmailError: If new email already exists
        """
        # Get existing profile
        profile = self.get_profile_by_id(profile_id)
        
        # Update fields if provided
        if first_name is not None:
            if not first_name.strip():
                raise ProfileValidationError("First name cannot be empty")
            profile.first_name = first_name.strip()
        
        if last_name is not None:
            if not last_name.strip():
                raise ProfileValidationError("Last name cannot be empty")
            profile.last_name = last_name.strip()
        
        if email is not None:
            email = email.strip().lower()
            self._validate_email(email)
            
            # Check if email changed and new email exists
            if email != profile.email:
                if self._email_exists(email, exclude_id=profile_id):
                    raise DuplicateEmailError(f"Profile with email '{email}' already exists")
                profile.email = email
        
        if phone is not None:
            profile.phone = phone.strip() if phone.strip() else None
        
        if city is not None:
            profile.city = city.strip() if city.strip() else None
        
        if state is not None:
            profile.state = state.strip() if state.strip() else None
        
        if linkedin_url is not None:
            if linkedin_url.strip():
                self._validate_url(linkedin_url, "LinkedIn URL")
                profile.linkedin_url = linkedin_url.strip()
            else:
                profile.linkedin_url = None
        
        if portfolio_url is not None:
            if portfolio_url.strip():
                self._validate_url(portfolio_url, "Portfolio URL")
                profile.portfolio_url = portfolio_url.strip()
            else:
                profile.portfolio_url = None
        
        if professional_summary is not None:
            profile.professional_summary = professional_summary.strip() if professional_summary.strip() else None
        
        try:
            self.session.commit()
            self.session.refresh(profile)
            return profile
        except IntegrityError as e:
            self.session.rollback()
            raise DuplicateEmailError(f"Profile with email '{email}' already exists") from e
    
    def delete_profile(self, profile_id: int) -> None:
        """
        Delete a profile.

        This will cascade delete all related data (jobs, skills, etc.)

        Note: In single-profile mode, this is generally not recommended.
        Consider using update_profile() to clear data instead.

        Args:
            profile_id: The profile ID to delete

        Raises:
            ProfileNotFoundError: If profile not found
        """
        profile = self.get_profile_by_id(profile_id)

        self.session.delete(profile)
        self.session.commit()
    
    def profile_exists(self, profile_id: int) -> bool:
        """
        Check if a profile exists.
        
        Args:
            profile_id: The profile ID to check
            
        Returns:
            bool: True if profile exists, False otherwise
        """
        return self.session.query(Profile).filter_by(id=profile_id).count() > 0
    
    # Private validation methods
    
    def _validate_required_fields(self, first_name: str, last_name: str, email: str) -> None:
        """Validate that required fields are provided and not empty."""
        if not first_name or not first_name.strip():
            raise ProfileValidationError("First name is required")
        
        if not last_name or not last_name.strip():
            raise ProfileValidationError("Last name is required")
        
        if not email or not email.strip():
            raise ProfileValidationError("Email is required")
    
    def _validate_email(self, email: str) -> None:
        """Validate email format."""
        email = email.strip()
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            raise ProfileValidationError(f"Invalid email format: {email}")
        
        # Check for minimum length
        if len(email) < 5:  # a@b.c is minimum valid
            raise ProfileValidationError(f"Email is too short: {email}")
    
    def _validate_url(self, url: str, field_name: str) -> None:
        """Validate URL format."""
        url = url.strip()
        
        if not url.startswith(('http://', 'https://')):
            raise ProfileValidationError(f"{field_name} must start with http:// or https://")
        
        if len(url) < 10:  # http://a.b is minimum
            raise ProfileValidationError(f"{field_name} is too short")
    
    def _email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if email already exists in database.
        
        Args:
            email: Email to check
            exclude_id: Optional profile ID to exclude from check (for updates)
            
        Returns:
            bool: True if email exists, False otherwise
        """
        query = self.session.query(Profile).filter_by(email=email.strip().lower())
        
        if exclude_id is not None:
            query = query.filter(Profile.id != exclude_id)
        
        return query.count() > 0
