"""
JobService - Business logic for Job and BulletPoint operations.

This service handles CRUD operations for jobs and their associated
bullet points, including validation, business rules, and tag management.
"""

from typing import Optional, List, Tuple
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from adaptive_resume.models import Job, BulletPoint, Tag, BulletTag, Profile
from adaptive_resume.models.base import DEFAULT_PROFILE_ID


class JobServiceError(Exception):
    """Base exception for JobService errors."""
    pass


class JobNotFoundError(JobServiceError):
    """Raised when a job cannot be found."""
    pass


class JobValidationError(JobServiceError):
    """Raised when job validation fails."""
    pass


class BulletPointNotFoundError(JobServiceError):
    """Raised when a bullet point cannot be found."""
    pass


class BulletPointValidationError(JobServiceError):
    """Raised when bullet point validation fails."""
    pass


class JobService:
    """
    Service for managing jobs and bullet points.
    
    Provides CRUD operations with business logic validation.
    """
    
    def __init__(self, session: Session):
        """
        Initialize the JobService.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    # ==================== Job CRUD Operations ====================
    
    def create_job(
        self,
        company_name: str,
        job_title: str,
        start_date: date,
        location: Optional[str] = None,
        end_date: Optional[date] = None,
        is_current: bool = False,
        description: Optional[str] = None,
        display_order: int = 0,
        profile_id: int = DEFAULT_PROFILE_ID
    ) -> Job:
        """
        Create a new job.

        Args:
            company_name: Company name
            job_title: Job title
            start_date: Employment start date
            location: Optional job location
            end_date: Optional employment end date (None if current)
            is_current: Whether this is a current position
            description: Optional job description
            display_order: Display order (default 0)
            profile_id: ID of the profile this job belongs to (default: DEFAULT_PROFILE_ID)

        Returns:
            Job: The created job

        Raises:
            JobValidationError: If validation fails
        """
        # Validate required fields
        self._validate_required_job_fields(company_name, job_title)
        
        # Validate profile exists
        if not self._profile_exists(profile_id):
            raise JobValidationError(f"Profile with id {profile_id} does not exist")
        
        # Validate dates
        self._validate_job_dates(start_date, end_date, is_current)
        
        # Create job
        job = Job(
            profile_id=profile_id,
            company_name=company_name.strip(),
            job_title=job_title.strip(),
            location=location.strip() if location else None,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description.strip() if description else None,
            display_order=display_order
        )
        
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
    
    def get_job_by_id(self, job_id: int, include_deleted: bool = False) -> Job:
        """
        Get a job by ID.

        Args:
            job_id: The job ID
            include_deleted: If True, include soft-deleted jobs

        Returns:
            Job: The job

        Raises:
            JobNotFoundError: If job not found
        """
        query = self.session.query(Job).filter_by(id=job_id)

        if not include_deleted:
            query = query.filter(Job.deleted_at.is_(None))

        job = query.first()

        if not job:
            raise JobNotFoundError(f"Job with id {job_id} not found")

        return job
    
    def get_jobs_for_profile(self, profile_id: int = DEFAULT_PROFILE_ID, include_deleted: bool = False) -> List[Job]:
        """
        Get all jobs for a profile.

        Args:
            profile_id: The profile ID (default: DEFAULT_PROFILE_ID)
            include_deleted: If True, include soft-deleted jobs

        Returns:
            List[Job]: All jobs for the profile, ordered by start date (newest first)
        """
        query = self.session.query(Job).filter_by(profile_id=profile_id)

        if not include_deleted:
            query = query.filter(Job.deleted_at.is_(None))

        return query.order_by(Job.start_date.desc()).all()
    
    def update_job(
        self,
        job_id: int,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_current: Optional[bool] = None,
        description: Optional[str] = None,
        display_order: Optional[int] = None
    ) -> Job:
        """
        Update a job.
        
        Only provided fields will be updated. None values are ignored.
        
        Args:
            job_id: The job ID to update
            company_name: Optional new company name
            job_title: Optional new job title
            location: Optional new location
            start_date: Optional new start date
            end_date: Optional new end date
            is_current: Optional new is_current flag
            description: Optional new description
            display_order: Optional new display order
            
        Returns:
            Job: The updated job
            
        Raises:
            JobNotFoundError: If job not found
            JobValidationError: If validation fails
        """
        job = self.get_job_by_id(job_id)
        
        # Update fields if provided
        if company_name is not None:
            if not company_name.strip():
                raise JobValidationError("Company name cannot be empty")
            job.company_name = company_name.strip()
        
        if job_title is not None:
            if not job_title.strip():
                raise JobValidationError("Job title cannot be empty")
            job.job_title = job_title.strip()
        
        if location is not None:
            job.location = location.strip() if location.strip() else None
        
        if start_date is not None:
            job.start_date = start_date
        
        if end_date is not None:
            job.end_date = end_date
        
        if is_current is not None:
            job.is_current = is_current
        
        if description is not None:
            job.description = description.strip() if description.strip() else None
        
        if display_order is not None:
            job.display_order = display_order
        
        # Validate dates after updates
        self._validate_job_dates(job.start_date, job.end_date, job.is_current)
        
        self.session.commit()
        self.session.refresh(job)
        return job
    
    def delete_job(self, job_id: int) -> None:
        """
        Soft delete a job.

        This will also soft delete all associated bullet points.

        Args:
            job_id: The job ID to delete

        Raises:
            JobNotFoundError: If job not found
        """
        job = self.get_job_by_id(job_id)

        # Soft delete the job
        job.deleted_at = datetime.now()

        # Soft delete all bullet points
        for bullet in job.bullet_points:
            if bullet.deleted_at is None:
                bullet.deleted_at = datetime.now()

        self.session.commit()
    
    # ==================== BulletPoint CRUD Operations ====================
    
    def create_bullet_point(
        self,
        job_id: int,
        content: str,
        metrics: Optional[str] = None,
        impact: Optional[str] = None,
        display_order: int = 0,
        is_highlighted: bool = False,
        tag_names: Optional[List[str]] = None
    ) -> BulletPoint:
        """
        Create a new bullet point for a job.
        
        Args:
            job_id: ID of the job this bullet belongs to
            content: Bullet point content
            metrics: Optional metrics/quantification
            impact: Optional business impact
            display_order: Display order (default 0)
            is_highlighted: Whether this is a standout achievement
            tag_names: Optional list of tag names to apply
            
        Returns:
            BulletPoint: The created bullet point
            
        Raises:
            BulletPointValidationError: If validation fails
        """
        # Validate required fields
        if not content or not content.strip():
            raise BulletPointValidationError("Bullet point content is required")
        
        if len(content.strip()) < 10:
            raise BulletPointValidationError("Bullet point content must be at least 10 characters")
        
        if len(content.strip()) > 1000:
            raise BulletPointValidationError("Bullet point content must be 1000 characters or less")
        
        # Validate job exists
        if not self._job_exists(job_id):
            raise BulletPointValidationError(f"Job with id {job_id} does not exist")
        
        # Create bullet point
        bullet = BulletPoint(
            job_id=job_id,
            content=content.strip(),
            metrics=metrics.strip() if metrics else None,
            impact=impact.strip() if impact else None,
            display_order=display_order,
            is_highlighted=is_highlighted
        )
        
        self.session.add(bullet)
        self.session.commit()
        self.session.refresh(bullet)
        
        # Add tags if provided
        if tag_names:
            self.add_tags_to_bullet(bullet.id, tag_names)
        
        return bullet
    
    def get_bullet_point_by_id(self, bullet_id: int, include_deleted: bool = False) -> BulletPoint:
        """
        Get a bullet point by ID.

        Args:
            bullet_id: The bullet point ID
            include_deleted: If True, include soft-deleted bullet points

        Returns:
            BulletPoint: The bullet point

        Raises:
            BulletPointNotFoundError: If bullet point not found
        """
        query = self.session.query(BulletPoint).filter_by(id=bullet_id)

        if not include_deleted:
            query = query.filter(BulletPoint.deleted_at.is_(None))

        bullet = query.first()

        if not bullet:
            raise BulletPointNotFoundError(f"Bullet point with id {bullet_id} not found")

        return bullet
    
    def get_bullet_points_for_job(self, job_id: int, include_deleted: bool = False) -> List[BulletPoint]:
        """
        Get all bullet points for a job.

        Args:
            job_id: The job ID
            include_deleted: If True, include soft-deleted bullet points

        Returns:
            List[BulletPoint]: All bullet points for the job, ordered by display_order
        """
        query = self.session.query(BulletPoint).filter_by(job_id=job_id)

        if not include_deleted:
            query = query.filter(BulletPoint.deleted_at.is_(None))

        return query.order_by(BulletPoint.display_order).all()
    
    def update_bullet_point(
        self,
        bullet_id: int,
        content: Optional[str] = None,
        metrics: Optional[str] = None,
        impact: Optional[str] = None,
        display_order: Optional[int] = None,
        is_highlighted: Optional[bool] = None
    ) -> BulletPoint:
        """
        Update a bullet point.
        
        Args:
            bullet_id: The bullet point ID
            content: Optional new content
            metrics: Optional new metrics
            impact: Optional new impact
            display_order: Optional new display order
            is_highlighted: Optional new highlighted flag
            
        Returns:
            BulletPoint: The updated bullet point
            
        Raises:
            BulletPointNotFoundError: If bullet point not found
            BulletPointValidationError: If validation fails
        """
        bullet = self.get_bullet_point_by_id(bullet_id)
        
        if content is not None:
            if not content.strip():
                raise BulletPointValidationError("Bullet point content cannot be empty")
            if len(content.strip()) < 10:
                raise BulletPointValidationError("Bullet point content must be at least 10 characters")
            if len(content.strip()) > 1000:
                raise BulletPointValidationError("Bullet point content must be 1000 characters or less")
            bullet.content = content.strip()
        
        if metrics is not None:
            bullet.metrics = metrics.strip() if metrics.strip() else None
        
        if impact is not None:
            bullet.impact = impact.strip() if impact.strip() else None
        
        if display_order is not None:
            bullet.display_order = display_order
        
        if is_highlighted is not None:
            bullet.is_highlighted = is_highlighted
        
        self.session.commit()
        self.session.refresh(bullet)
        return bullet
    
    def delete_bullet_point(self, bullet_id: int) -> None:
        """
        Soft delete a bullet point.

        Args:
            bullet_id: The bullet point ID to delete

        Raises:
            BulletPointNotFoundError: If bullet point not found
        """
        bullet = self.get_bullet_point_by_id(bullet_id)

        # Soft delete the bullet point
        bullet.deleted_at = datetime.now()

        self.session.commit()

    # ==================== Soft Delete Management ====================

    def get_recently_deleted_jobs(self, profile_id: int = DEFAULT_PROFILE_ID, days: int = 30) -> List[Job]:
        """
        Get jobs that were soft-deleted within the specified number of days.

        Args:
            profile_id: The profile ID (default: DEFAULT_PROFILE_ID)
            days: Number of days to look back (default 30)

        Returns:
            List[Job]: Recently deleted jobs, ordered by deletion date (newest first)
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        return self.session.query(Job).filter(
            Job.profile_id == profile_id,
            Job.deleted_at.isnot(None),
            Job.deleted_at >= cutoff_date
        ).order_by(Job.deleted_at.desc()).all()

    def get_recently_deleted_bullets(self, profile_id: int = DEFAULT_PROFILE_ID, days: int = 30) -> List[BulletPoint]:
        """
        Get bullet points that were soft-deleted within the specified number of days.

        Args:
            profile_id: The profile ID (default: DEFAULT_PROFILE_ID)
            days: Number of days to look back (default 30)

        Returns:
            List[BulletPoint]: Recently deleted bullets, ordered by deletion date (newest first)
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        return self.session.query(BulletPoint).join(Job).filter(
            Job.profile_id == profile_id,
            BulletPoint.deleted_at.isnot(None),
            BulletPoint.deleted_at >= cutoff_date
        ).order_by(BulletPoint.deleted_at.desc()).all()

    def restore_job(self, job_id: int) -> Job:
        """
        Restore a soft-deleted job and its bullet points.

        Args:
            job_id: The job ID to restore

        Returns:
            Job: The restored job

        Raises:
            JobNotFoundError: If job not found (including non-deleted jobs)
        """
        job = self.get_job_by_id(job_id, include_deleted=True)

        if job.deleted_at is None:
            raise JobValidationError("Job is not deleted")

        # Restore the job
        job.deleted_at = None

        # Restore all bullet points that were deleted at the same time
        for bullet in job.bullet_points:
            if bullet.deleted_at is not None:
                bullet.deleted_at = None

        self.session.commit()
        self.session.refresh(job)
        return job

    def restore_bullet_point(self, bullet_id: int) -> BulletPoint:
        """
        Restore a soft-deleted bullet point.

        Args:
            bullet_id: The bullet point ID to restore

        Returns:
            BulletPoint: The restored bullet point

        Raises:
            BulletPointNotFoundError: If bullet point not found
            BulletPointValidationError: If bullet point is not deleted
        """
        bullet = self.get_bullet_point_by_id(bullet_id, include_deleted=True)

        if bullet.deleted_at is None:
            raise BulletPointValidationError("Bullet point is not deleted")

        # Restore the bullet point
        bullet.deleted_at = None

        self.session.commit()
        self.session.refresh(bullet)
        return bullet

    def permanently_delete_job(self, job_id: int) -> None:
        """
        Permanently delete a job and all its bullet points.

        This is irreversible. The job must already be soft-deleted.

        Args:
            job_id: The job ID to permanently delete

        Raises:
            JobNotFoundError: If job not found
            JobValidationError: If job is not soft-deleted
        """
        job = self.get_job_by_id(job_id, include_deleted=True)

        if job.deleted_at is None:
            raise JobValidationError("Job must be soft-deleted before permanent deletion")

        # Permanently delete
        self.session.delete(job)
        self.session.commit()

    def permanently_delete_bullet_point(self, bullet_id: int) -> None:
        """
        Permanently delete a bullet point.

        This is irreversible. The bullet point must already be soft-deleted.

        Args:
            bullet_id: The bullet point ID to permanently delete

        Raises:
            BulletPointNotFoundError: If bullet point not found
            BulletPointValidationError: If bullet point is not soft-deleted
        """
        bullet = self.get_bullet_point_by_id(bullet_id, include_deleted=True)

        if bullet.deleted_at is None:
            raise BulletPointValidationError("Bullet point must be soft-deleted before permanent deletion")

        # Permanently delete
        self.session.delete(bullet)
        self.session.commit()

    def purge_old_deleted_items(self, profile_id: int = DEFAULT_PROFILE_ID, days: int = 30) -> Tuple[int, int]:
        """
        Permanently delete all soft-deleted items older than the specified number of days.

        Args:
            profile_id: The profile ID (default: DEFAULT_PROFILE_ID)
            days: Number of days (items deleted more than this long ago will be purged)

        Returns:
            Tuple[int, int]: Number of jobs and bullet points permanently deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        # Find old deleted jobs
        old_jobs = self.session.query(Job).filter(
            Job.profile_id == profile_id,
            Job.deleted_at.isnot(None),
            Job.deleted_at < cutoff_date
        ).all()

        # Find old deleted bullet points (not part of deleted jobs)
        old_bullets = self.session.query(BulletPoint).join(Job).filter(
            Job.profile_id == profile_id,
            Job.deleted_at.is_(None),  # Job is not deleted
            BulletPoint.deleted_at.isnot(None),
            BulletPoint.deleted_at < cutoff_date
        ).all()

        jobs_count = len(old_jobs)
        bullets_count = len(old_bullets)

        # Permanently delete them
        for job in old_jobs:
            self.session.delete(job)

        for bullet in old_bullets:
            self.session.delete(bullet)

        self.session.commit()

        return jobs_count, bullets_count

    # ==================== Tag Management ====================
    
    def add_tags_to_bullet(self, bullet_id: int, tag_names: List[str]) -> BulletPoint:
        """
        Add tags to a bullet point.
        
        Args:
            bullet_id: The bullet point ID
            tag_names: List of tag names to add
            
        Returns:
            BulletPoint: The updated bullet point
            
        Raises:
            BulletPointNotFoundError: If bullet point not found
        """
        bullet = self.get_bullet_point_by_id(bullet_id)
        
        for tag_name in tag_names:
            tag_name = tag_name.strip().lower()
            
            # Get or create tag
            tag = self.session.query(Tag).filter_by(name=tag_name).first()
            if not tag:
                # Skip if tag doesn't exist (we only use predefined tags)
                continue
            
            # Check if association already exists
            existing = self.session.query(BulletTag).filter_by(
                bullet_point_id=bullet_id,
                tag_id=tag.id
            ).first()
            
            if not existing:
                bullet_tag = BulletTag(bullet_point_id=bullet_id, tag_id=tag.id)
                self.session.add(bullet_tag)
        
        self.session.commit()
        self.session.refresh(bullet)
        return bullet
    
    def remove_tag_from_bullet(self, bullet_id: int, tag_name: str) -> BulletPoint:
        """
        Remove a tag from a bullet point.
        
        Args:
            bullet_id: The bullet point ID
            tag_name: Name of tag to remove
            
        Returns:
            BulletPoint: The updated bullet point
            
        Raises:
            BulletPointNotFoundError: If bullet point not found
        """
        bullet = self.get_bullet_point_by_id(bullet_id)
        
        tag = self.session.query(Tag).filter_by(name=tag_name.strip().lower()).first()
        if tag:
            bullet_tag = self.session.query(BulletTag).filter_by(
                bullet_point_id=bullet_id,
                tag_id=tag.id
            ).first()
            
            if bullet_tag:
                self.session.delete(bullet_tag)
                self.session.commit()
        
        self.session.refresh(bullet)
        return bullet
    
    def get_bullets_by_tag(self, tag_name: str) -> List[BulletPoint]:
        """
        Get all bullet points with a specific tag.
        
        Args:
            tag_name: The tag name
            
        Returns:
            List[BulletPoint]: All bullet points with that tag
        """
        return self.session.query(BulletPoint).join(BulletTag).join(Tag).filter(
            Tag.name == tag_name.strip().lower()
        ).all()
    
    # ==================== Private Helper Methods ====================
    
    def _validate_required_job_fields(self, company_name: str, job_title: str) -> None:
        """Validate that required job fields are provided."""
        if not company_name or not company_name.strip():
            raise JobValidationError("Company name is required")
        
        if not job_title or not job_title.strip():
            raise JobValidationError("Job title is required")
    
    def _validate_job_dates(
        self,
        start_date: date,
        end_date: Optional[date],
        is_current: bool
    ) -> None:
        """Validate job date logic."""
        if is_current and end_date is not None:
            raise JobValidationError("Current jobs cannot have an end date")
        
        if end_date and start_date and end_date < start_date:
            raise JobValidationError("End date cannot be before start date")
    
    def _profile_exists(self, profile_id: int) -> bool:
        """Check if a profile exists."""
        return self.session.query(Profile).filter_by(id=profile_id).count() > 0
    
    def _job_exists(self, job_id: int) -> bool:
        """Check if a job exists."""
        return self.session.query(Job).filter_by(id=job_id).count() > 0
