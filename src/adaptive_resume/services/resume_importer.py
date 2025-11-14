"""Resume importer service for converting extracted data to database models.

This service takes ExtractedResume data and imports it into the database,
creating or updating Profile, Job, Education, Skill, and Certification records
with intelligent deduplication and error handling.
"""

from __future__ import annotations

import re
import logging
from datetime import date, datetime
from typing import Optional, Tuple, List
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from adaptive_resume.models import (
    Profile, Job, BulletPoint, Education, Skill, Certification
)
from .resume_extractor import (
    ExtractedResume, ExtractedJob, ExtractedEducation, ExtractedCertification
)

logger = logging.getLogger(__name__)


class ResumeImportError(Exception):
    """Base exception for resume import errors."""
    pass


class ResumeImporter:
    """Service for importing extracted resume data into the database.

    This service converts ExtractedResume objects into database models,
    handling:
    - Profile creation/update
    - Job and bullet point creation
    - Education, skill, and certification import
    - Date parsing and normalization
    - Intelligent deduplication
    - Transaction management and error handling
    """

    def __init__(self, session: Session):
        """Initialize the resume importer.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def import_resume(
        self,
        extracted_resume: ExtractedResume,
        profile_id: Optional[int] = None,
        create_new_profile: bool = True
    ) -> Tuple[Profile, dict]:
        """Import an extracted resume into the database.

        Args:
            extracted_resume: Extracted resume data
            profile_id: Existing profile ID to update (optional)
            create_new_profile: If True and no profile_id, create new profile

        Returns:
            Tuple of (Profile, import_stats) where import_stats contains:
                - jobs_created: int
                - bullet_points_created: int
                - education_created: int
                - skills_created: int
                - certifications_created: int
                - errors: List[str]

        Raises:
            ResumeImportError: If import fails critically
        """
        logger.info(f"Starting resume import (profile_id={profile_id}, create_new={create_new_profile})")

        stats = {
            'jobs_created': 0,
            'bullet_points_created': 0,
            'education_created': 0,
            'skills_created': 0,
            'certifications_created': 0,
            'errors': []
        }

        try:
            # Get or create profile
            if profile_id:
                profile = self.session.get(Profile, profile_id)
                if not profile:
                    raise ResumeImportError(f"Profile with id {profile_id} not found")
                profile = self._update_profile(profile, extracted_resume)
                logger.info(f"Updated existing profile {profile_id}")
            elif create_new_profile:
                profile = self._create_profile(extracted_resume)
                logger.info(f"Created new profile {profile.id}")
            else:
                raise ResumeImportError("No profile_id provided and create_new_profile=False")

            # Import jobs
            jobs_count, bullets_count, job_errors = self._import_jobs(profile, extracted_resume.jobs)
            stats['jobs_created'] = jobs_count
            stats['bullet_points_created'] = bullets_count
            stats['errors'].extend(job_errors)

            # Import education
            edu_count, edu_errors = self._import_education(profile, extracted_resume.education)
            stats['education_created'] = edu_count
            stats['errors'].extend(edu_errors)

            # Import skills
            skill_count, skill_errors = self._import_skills(profile, extracted_resume.skills)
            stats['skills_created'] = skill_count
            stats['errors'].extend(skill_errors)

            # Import certifications
            cert_count, cert_errors = self._import_certifications(profile, extracted_resume.certifications)
            stats['certifications_created'] = cert_count
            stats['errors'].extend(cert_errors)

            # Commit transaction
            self.session.commit()
            logger.info(f"Resume import completed successfully: {stats}")

            return profile, stats

        except Exception as e:
            # Rollback on any error
            self.session.rollback()
            logger.error(f"Resume import failed, rolling back: {e}", exc_info=True)
            raise ResumeImportError(f"Failed to import resume: {str(e)}") from e

    def _create_profile(self, extracted_resume: ExtractedResume) -> Profile:
        """Create a new profile from extracted data.

        Args:
            extracted_resume: Extracted resume data

        Returns:
            Created Profile object

        Raises:
            ResumeImportError: If required fields are missing
        """
        # Validate required fields
        if not extracted_resume.first_name or not extracted_resume.last_name:
            raise ResumeImportError("First name and last name are required")

        if not extracted_resume.email:
            raise ResumeImportError("Email is required")

        # Parse location
        city, state = self._parse_location(extracted_resume.location)

        # Create profile
        profile = Profile(
            first_name=extracted_resume.first_name,
            last_name=extracted_resume.last_name,
            email=extracted_resume.email,
            phone=extracted_resume.phone,
            city=city,
            state=state,
            linkedin_url=extracted_resume.linkedin_url,
            portfolio_url=extracted_resume.github_url or extracted_resume.website_url
        )

        self.session.add(profile)
        self.session.flush()  # Get the ID

        return profile

    def _update_profile(self, profile: Profile, extracted_resume: ExtractedResume) -> Profile:
        """Update an existing profile with extracted data.

        Args:
            profile: Existing profile to update
            extracted_resume: Extracted resume data

        Returns:
            Updated Profile object
        """
        # Update fields if provided
        if extracted_resume.first_name:
            profile.first_name = extracted_resume.first_name
        if extracted_resume.last_name:
            profile.last_name = extracted_resume.last_name
        if extracted_resume.email:
            profile.email = extracted_resume.email
        if extracted_resume.phone:
            profile.phone = extracted_resume.phone

        # Parse and update location
        if extracted_resume.location:
            city, state = self._parse_location(extracted_resume.location)
            if city:
                profile.city = city
            if state:
                profile.state = state

        if extracted_resume.linkedin_url:
            profile.linkedin_url = extracted_resume.linkedin_url

        # Prefer GitHub, but fall back to website
        if extracted_resume.github_url:
            profile.portfolio_url = extracted_resume.github_url
        elif extracted_resume.website_url:
            profile.portfolio_url = extracted_resume.website_url

        return profile

    def _import_jobs(
        self,
        profile: Profile,
        extracted_jobs: List[ExtractedJob]
    ) -> Tuple[int, int, List[str]]:
        """Import jobs and bullet points.

        Args:
            profile: Profile to attach jobs to
            extracted_jobs: List of extracted jobs

        Returns:
            Tuple of (jobs_created, bullet_points_created, errors)
        """
        jobs_created = 0
        bullets_created = 0
        errors = []

        for i, extracted_job in enumerate(extracted_jobs):
            try:
                # Parse dates
                start_date = self._parse_date(extracted_job.start_date)
                end_date = self._parse_date(extracted_job.end_date) if not extracted_job.is_current else None

                # Validate required fields
                if not extracted_job.company_name or not extracted_job.job_title:
                    errors.append(f"Job {i+1}: Missing company name or job title")
                    continue

                if not start_date:
                    errors.append(f"Job {i+1}: Could not parse start date '{extracted_job.start_date}'")
                    continue

                # Create job
                job = Job(
                    profile_id=profile.id,
                    company_name=extracted_job.company_name,
                    job_title=extracted_job.job_title,
                    location=extracted_job.location,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=extracted_job.is_current,
                    display_order=i
                )

                self.session.add(job)
                self.session.flush()  # Get the ID
                jobs_created += 1

                # Import bullet points
                for j, bullet_text in enumerate(extracted_job.bullet_points):
                    if bullet_text.strip():
                        bullet = BulletPoint(
                            job_id=job.id,
                            content=bullet_text.strip(),
                            display_order=j
                        )
                        self.session.add(bullet)
                        bullets_created += 1

            except Exception as e:
                logger.warning(f"Failed to import job {i+1}: {e}")
                errors.append(f"Job {i+1}: {str(e)}")

        return jobs_created, bullets_created, errors

    def _import_education(
        self,
        profile: Profile,
        extracted_education: List[ExtractedEducation]
    ) -> Tuple[int, List[str]]:
        """Import education entries.

        Args:
            profile: Profile to attach education to
            extracted_education: List of extracted education

        Returns:
            Tuple of (education_created, errors)
        """
        edu_created = 0
        errors = []

        for i, extracted_edu in enumerate(extracted_education):
            try:
                # Validate required fields
                if not extracted_edu.school_name:
                    errors.append(f"Education {i+1}: Missing school name")
                    continue

                # Parse dates
                graduation_date = self._parse_date(extracted_edu.graduation_date)

                # Parse GPA
                gpa = self._parse_gpa(extracted_edu.gpa)

                # Create education entry
                education = Education(
                    profile_id=profile.id,
                    institution=extracted_edu.school_name,
                    degree=extracted_edu.degree_type or "Degree",
                    field_of_study=extracted_edu.major,
                    end_date=graduation_date,
                    gpa=gpa,
                    display_order=i
                )

                self.session.add(education)
                edu_created += 1

            except Exception as e:
                logger.warning(f"Failed to import education {i+1}: {e}")
                errors.append(f"Education {i+1}: {str(e)}")

        return edu_created, errors

    def _import_skills(
        self,
        profile: Profile,
        extracted_skills: List[str]
    ) -> Tuple[int, List[str]]:
        """Import skills with deduplication.

        Args:
            profile: Profile to attach skills to
            extracted_skills: List of skill names

        Returns:
            Tuple of (skills_created, errors)
        """
        skills_created = 0
        errors = []

        # Get existing skills for this profile (for deduplication)
        existing_skills = {
            skill.skill_name.lower(): skill
            for skill in self.session.query(Skill).filter_by(profile_id=profile.id).all()
        }

        for i, skill_name in enumerate(extracted_skills):
            try:
                skill_name = skill_name.strip()
                if not skill_name:
                    continue

                # Check for duplicates (case-insensitive)
                if skill_name.lower() in existing_skills:
                    logger.debug(f"Skipping duplicate skill: {skill_name}")
                    continue

                # Create skill
                skill = Skill(
                    profile_id=profile.id,
                    skill_name=skill_name,
                    display_order=i
                )

                self.session.add(skill)
                existing_skills[skill_name.lower()] = skill
                skills_created += 1

            except Exception as e:
                logger.warning(f"Failed to import skill '{skill_name}': {e}")
                errors.append(f"Skill '{skill_name}': {str(e)}")

        return skills_created, errors

    def _import_certifications(
        self,
        profile: Profile,
        extracted_certifications: List[ExtractedCertification]
    ) -> Tuple[int, List[str]]:
        """Import certifications.

        Args:
            profile: Profile to attach certifications to
            extracted_certifications: List of extracted certifications

        Returns:
            Tuple of (certifications_created, errors)
        """
        certs_created = 0
        errors = []

        for i, extracted_cert in enumerate(extracted_certifications):
            try:
                # Validate required fields
                if not extracted_cert.name:
                    errors.append(f"Certification {i+1}: Missing name")
                    continue

                # Parse dates
                issue_date = self._parse_date(extracted_cert.issue_date)
                expiration_date = self._parse_date(extracted_cert.expiration_date)

                # Create certification
                certification = Certification(
                    profile_id=profile.id,
                    name=extracted_cert.name,
                    issuing_organization=extracted_cert.issuing_organization or "Unknown",
                    issue_date=issue_date,
                    expiration_date=expiration_date,
                    display_order=i
                )

                self.session.add(certification)
                certs_created += 1

            except Exception as e:
                logger.warning(f"Failed to import certification {i+1}: {e}")
                errors.append(f"Certification {i+1}: {str(e)}")

        return certs_created, errors

    def _parse_location(self, location: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Parse location string into city and state.

        Args:
            location: Location string (e.g., "San Francisco, CA" or "New York")

        Returns:
            Tuple of (city, state)
        """
        if not location:
            return None, None

        # Try to parse "City, State" format
        if ',' in location:
            parts = [p.strip() for p in location.split(',')]
            if len(parts) >= 2:
                return parts[0], parts[1]
            else:
                return parts[0], None
        else:
            # Just a city name
            return location.strip(), None

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string into date object.

        Handles formats like:
        - "Jan 2020", "January 2020"
        - "2020", "2020-01", "2020-01-15"
        - "Present" → None (for current jobs)

        Args:
            date_str: Date string to parse

        Returns:
            date object or None if parsing fails
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # Handle "Present", "Current", etc.
        if date_str.lower() in ['present', 'current', 'now', 'ongoing']:
            return None

        # Try various date formats
        formats = [
            '%Y-%m-%d',      # 2020-01-15
            '%Y-%m',         # 2020-01
            '%Y',            # 2020
            '%b %Y',         # Jan 2020
            '%B %Y',         # January 2020
            '%m/%Y',         # 01/2020
            '%m/%d/%Y',      # 01/15/2020
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.date()
            except ValueError:
                continue

        # Try to extract just the year
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            year = int(year_match.group())
            return date(year, 1, 1)

        logger.warning(f"Could not parse date: '{date_str}'")
        return None

    def _parse_gpa(self, gpa_str: Optional[str]) -> Optional[Decimal]:
        """Parse GPA string into Decimal.

        Args:
            gpa_str: GPA string (e.g., "3.75", "3.75/4.0")

        Returns:
            Decimal GPA value or None if parsing fails
        """
        if not gpa_str:
            return None

        gpa_str = str(gpa_str).strip()

        # Extract numeric value (handle "3.75/4.0" format)
        if '/' in gpa_str:
            gpa_str = gpa_str.split('/')[0].strip()

        try:
            gpa = Decimal(gpa_str)

            # Validate range
            if 0.0 <= gpa <= 4.0:
                return gpa
            else:
                logger.warning(f"GPA out of range (0.0-4.0): {gpa}")
                return None
        except (ValueError, ArithmeticError):
            logger.warning(f"Could not parse GPA: '{gpa_str}'")
            return None


__all__ = ['ResumeImporter', 'ResumeImportError']
