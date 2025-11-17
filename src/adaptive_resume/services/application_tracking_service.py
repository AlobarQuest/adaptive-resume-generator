"""Application tracking service for managing job application lifecycle.

This service handles the complete lifecycle of job applications from discovery
through final outcome, including status management, interview tracking, contact
management, and analytics.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from adaptive_resume.models.job_application import JobApplication
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.models.tailored_resume import TailoredResumeModel


class ApplicationTrackingService:
    """Service for managing job application lifecycle and analytics.

    Features:
    - Create applications from job postings or manual entry
    - Track status changes through the application pipeline
    - Record interviews and contact information
    - Calculate metrics (response time, time to outcome)
    - Query and filter applications
    - Generate analytics and reports
    """

    def __init__(self, session: Session):
        """Initialize the service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    # ========================================================================
    # Application CRUD Operations
    # ========================================================================

    def create_application(
        self,
        profile_id: int,
        company_name: str,
        position_title: str,
        job_description: Optional[str] = None,
        job_url: Optional[str] = None,
        job_posting_id: Optional[int] = None,
        status: str = JobApplication.STATUS_DISCOVERED,
        priority: str = JobApplication.PRIORITY_MEDIUM,
        **kwargs
    ) -> JobApplication:
        """Create a new job application.

        Args:
            profile_id: Profile ID
            company_name: Company name
            position_title: Job title
            job_description: Job description text
            job_url: URL to job posting
            job_posting_id: Optional JobPosting ID if imported/analyzed
            status: Initial status (default: discovered)
            priority: Priority level (default: medium)
            **kwargs: Additional fields (location, salary_range, etc.)

        Returns:
            Created JobApplication
        """
        app = JobApplication(
            profile_id=profile_id,
            company_name=company_name,
            position_title=position_title,
            job_description=job_description,
            job_url=job_url,
            job_posting_id=job_posting_id,
            status=status,
            priority=priority,
            discovered_date=date.today(),
            **kwargs
        )

        self.session.add(app)
        self.session.commit()
        self.session.refresh(app)

        return app

    def create_from_job_posting(
        self,
        profile_id: int,
        job_posting: JobPosting,
        tailored_resume_id: Optional[int] = None,
        status: str = JobApplication.STATUS_INTERESTED,
        **kwargs
    ) -> JobApplication:
        """Create application from an analyzed JobPosting.

        Args:
            profile_id: Profile ID
            job_posting: JobPosting object
            tailored_resume_id: Optional TailoredResume ID
            status: Initial status (default: interested)
            **kwargs: Additional fields

        Returns:
            Created JobApplication
        """
        return self.create_application(
            profile_id=profile_id,
            company_name=job_posting.company_name,
            position_title=job_posting.job_title,
            job_description=job_posting.raw_text,
            job_posting_id=job_posting.id,
            tailored_resume_id=tailored_resume_id,
            status=status,
            **kwargs
        )

    def get_application(self, application_id: int) -> Optional[JobApplication]:
        """Get application by ID.

        Args:
            application_id: Application ID

        Returns:
            JobApplication or None
        """
        return self.session.query(JobApplication).filter_by(id=application_id).first()

    def update_application(
        self,
        application_id: int,
        **kwargs
    ) -> JobApplication:
        """Update application fields.

        Args:
            application_id: Application ID
            **kwargs: Fields to update

        Returns:
            Updated JobApplication

        Raises:
            ValueError: If application not found
        """
        app = self.get_application(application_id)
        if not app:
            raise ValueError(f"Application {application_id} not found")

        for key, value in kwargs.items():
            if hasattr(app, key):
                setattr(app, key, value)

        self.session.commit()
        self.session.refresh(app)

        return app

    def delete_application(self, application_id: int) -> bool:
        """Delete an application.

        Args:
            application_id: Application ID

        Returns:
            True if deleted, False if not found
        """
        app = self.get_application(application_id)
        if not app:
            return False

        self.session.delete(app)
        self.session.commit()

        return True

    # ========================================================================
    # Status Management
    # ========================================================================

    def update_status(
        self,
        application_id: int,
        new_status: str,
        substatus: Optional[str] = None,
        notes: Optional[str] = None
    ) -> JobApplication:
        """Update application status.

        Automatically sets relevant date fields based on status:
        - applied: sets application_date
        - screening/interview: sets first_response_date if not set
        - offer_received: sets offer_date
        - accepted: sets acceptance_date
        - rejected: sets rejection_date

        Args:
            application_id: Application ID
            new_status: New status value
            substatus: Optional substatus
            notes: Optional notes to append

        Returns:
            Updated JobApplication

        Raises:
            ValueError: If application not found or invalid status
        """
        if new_status not in JobApplication.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")

        app = self.get_application(application_id)
        if not app:
            raise ValueError(f"Application {application_id} not found")

        old_status = app.status
        app.status = new_status

        if substatus:
            app.substatus = substatus

        # Auto-set date fields based on status
        today = date.today()

        if new_status == JobApplication.STATUS_APPLIED and not app.application_date:
            app.application_date = today

        if new_status in [JobApplication.STATUS_SCREENING, JobApplication.STATUS_INTERVIEW]:
            if not app.first_response_date:
                app.first_response_date = today
                app.calculate_response_time()

        if new_status == JobApplication.STATUS_OFFER_RECEIVED and not app.offer_date:
            app.offer_date = today

        if new_status == JobApplication.STATUS_ACCEPTED and not app.acceptance_date:
            app.acceptance_date = today
            app.calculate_time_to_outcome()

        if new_status == JobApplication.STATUS_REJECTED and not app.rejection_date:
            app.rejection_date = today
            app.calculate_time_to_outcome()

        # Append notes
        if notes:
            if app.notes:
                app.notes += f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Status: {old_status} → {new_status}\n{notes}"
            else:
                app.notes = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Status: {old_status} → {new_status}\n{notes}"

        self.session.commit()
        self.session.refresh(app)

        return app

    def mark_as_applied(
        self,
        application_id: int,
        application_date: Optional[date] = None,
        application_method: Optional[str] = None,
        notes: Optional[str] = None
    ) -> JobApplication:
        """Mark application as applied.

        Args:
            application_id: Application ID
            application_date: Date applied (default: today)
            application_method: How applied (e.g., "company_site", "linkedin")
            notes: Optional notes

        Returns:
            Updated JobApplication
        """
        app = self.update_status(application_id, JobApplication.STATUS_APPLIED, notes=notes)

        if application_date:
            app.application_date = application_date

        if application_method:
            app.application_method = application_method

        self.session.commit()
        self.session.refresh(app)

        return app

    # ========================================================================
    # Interview Management
    # ========================================================================

    def add_interview(
        self,
        application_id: int,
        interview_date: date,
        interview_type: str = "general",
        notes: str = ""
    ) -> JobApplication:
        """Add an interview to the application.

        Args:
            application_id: Application ID
            interview_date: Date of interview
            interview_type: Type (e.g., "phone_screen", "technical", "onsite")
            notes: Interview notes

        Returns:
            Updated JobApplication

        Raises:
            ValueError: If application not found
        """
        app = self.get_application(application_id)
        if not app:
            raise ValueError(f"Application {application_id} not found")

        # Add interview to JSON array
        app.add_interview(interview_date, interview_type, notes)

        # Update status if not already in interview
        if app.status not in [JobApplication.STATUS_INTERVIEW, JobApplication.STATUS_OFFER_RECEIVED,
                               JobApplication.STATUS_ACCEPTED, JobApplication.STATUS_REJECTED]:
            app.status = JobApplication.STATUS_INTERVIEW

        # Set substatus
        app.substatus = interview_type

        # Set first response date if not set
        if not app.first_response_date:
            app.first_response_date = interview_date
            app.calculate_response_time()

        self.session.commit()
        self.session.refresh(app)

        return app

    def get_upcoming_interviews(
        self,
        profile_id: Optional[int] = None,
        days_ahead: int = 7
    ) -> List[Tuple[JobApplication, Dict[str, Any]]]:
        """Get upcoming interviews.

        Args:
            profile_id: Optional profile ID filter
            days_ahead: Look ahead this many days (default: 7)

        Returns:
            List of (application, interview_dict) tuples
        """
        query = self.session.query(JobApplication).filter(
            ~JobApplication.status.in_([
                JobApplication.STATUS_ACCEPTED,
                JobApplication.STATUS_REJECTED,
                JobApplication.STATUS_WITHDRAWN
            ]),
            JobApplication.interview_dates.isnot(None)
        )

        if profile_id:
            query = query.filter(JobApplication.profile_id == profile_id)

        applications = query.all()

        upcoming = []
        cutoff_date = date.today() + timedelta(days=days_ahead)

        for app in applications:
            interviews = app.get_interviews()
            for interview in interviews:
                try:
                    interview_date = datetime.fromisoformat(interview['date']).date()
                    if date.today() <= interview_date <= cutoff_date:
                        upcoming.append((app, interview))
                except (ValueError, KeyError):
                    continue

        # Sort by interview date
        upcoming.sort(key=lambda x: x[1]['date'])

        return upcoming

    # ========================================================================
    # Contact Management
    # ========================================================================

    def update_contact(
        self,
        application_id: int,
        contact_person: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        recruiter_name: Optional[str] = None,
        recruiter_email: Optional[str] = None,
        last_contact_date: Optional[date] = None
    ) -> JobApplication:
        """Update contact information.

        Args:
            application_id: Application ID
            contact_person: Contact person name
            contact_email: Contact email
            contact_phone: Contact phone
            recruiter_name: Recruiter name
            recruiter_email: Recruiter email
            last_contact_date: Last contact date

        Returns:
            Updated JobApplication
        """
        updates = {}

        if contact_person is not None:
            updates['contact_person'] = contact_person
        if contact_email is not None:
            updates['contact_email'] = contact_email
        if contact_phone is not None:
            updates['contact_phone'] = contact_phone
        if recruiter_name is not None:
            updates['recruiter_name'] = recruiter_name
        if recruiter_email is not None:
            updates['recruiter_email'] = recruiter_email
        if last_contact_date is not None:
            updates['last_contact_date'] = last_contact_date

        return self.update_application(application_id, **updates)

    def schedule_followup(
        self,
        application_id: int,
        followup_date: date,
        notes: Optional[str] = None
    ) -> JobApplication:
        """Schedule a follow-up.

        Args:
            application_id: Application ID
            followup_date: Follow-up date
            notes: Optional notes

        Returns:
            Updated JobApplication
        """
        app = self.get_application(application_id)
        if not app:
            raise ValueError(f"Application {application_id} not found")

        app.next_followup_date = followup_date
        app.follow_up_date = followup_date  # Legacy field

        if notes:
            if app.notes:
                app.notes += f"\n\n[{datetime.now().strftime('%Y-%m-%d')}] Follow-up scheduled for {followup_date}\n{notes}"
            else:
                app.notes = f"[{datetime.now().strftime('%Y-%m-%d')}] Follow-up scheduled for {followup_date}\n{notes}"

        self.session.commit()
        self.session.refresh(app)

        return app

    def get_followups_due(
        self,
        profile_id: Optional[int] = None
    ) -> List[JobApplication]:
        """Get applications with follow-ups due.

        Args:
            profile_id: Optional profile ID filter

        Returns:
            List of applications needing follow-up
        """
        query = self.session.query(JobApplication).filter(
            ~JobApplication.status.in_([
                JobApplication.STATUS_ACCEPTED,
                JobApplication.STATUS_REJECTED,
                JobApplication.STATUS_WITHDRAWN
            ]),
            JobApplication.next_followup_date <= date.today()
        )

        if profile_id:
            query = query.filter(JobApplication.profile_id == profile_id)

        return query.order_by(JobApplication.next_followup_date).all()

    # ========================================================================
    # Querying & Filtering
    # ========================================================================

    def list_applications(
        self,
        profile_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        active_only: bool = False,
        company_name: Optional[str] = None,
        position_title: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        order_by: str = 'updated_at',
        order_direction: str = 'desc'
    ) -> List[JobApplication]:
        """Query applications with filters.

        Args:
            profile_id: Filter by profile ID
            status: Filter by status
            priority: Filter by priority
            active_only: Only active applications
            company_name: Filter by company (partial match)
            position_title: Filter by position (partial match)
            date_from: Filter by application_date >= date_from
            date_to: Filter by application_date <= date_to
            order_by: Field to order by
            order_direction: 'asc' or 'desc'

        Returns:
            List of JobApplication objects
        """
        query = self.session.query(JobApplication)

        # Apply filters
        if profile_id:
            query = query.filter(JobApplication.profile_id == profile_id)

        if status:
            query = query.filter(JobApplication.status == status)

        if priority:
            query = query.filter(JobApplication.priority == priority)

        if active_only:
            query = query.filter(
                ~JobApplication.status.in_([
                    JobApplication.STATUS_ACCEPTED,
                    JobApplication.STATUS_REJECTED,
                    JobApplication.STATUS_WITHDRAWN
                ])
            )

        if company_name:
            query = query.filter(JobApplication.company_name.ilike(f'%{company_name}%'))

        if position_title:
            query = query.filter(JobApplication.position_title.ilike(f'%{position_title}%'))

        if date_from:
            query = query.filter(JobApplication.application_date >= date_from)

        if date_to:
            query = query.filter(JobApplication.application_date <= date_to)

        # Apply ordering
        if hasattr(JobApplication, order_by):
            order_col = getattr(JobApplication, order_by)
            if order_direction.lower() == 'desc':
                query = query.order_by(desc(order_col))
            else:
                query = query.order_by(asc(order_col))

        return query.all()

    def get_by_status(
        self,
        status: str,
        profile_id: Optional[int] = None
    ) -> List[JobApplication]:
        """Get applications by status.

        Args:
            status: Status to filter by
            profile_id: Optional profile ID

        Returns:
            List of applications
        """
        return self.list_applications(profile_id=profile_id, status=status)

    def get_active_applications(
        self,
        profile_id: Optional[int] = None
    ) -> List[JobApplication]:
        """Get all active applications.

        Args:
            profile_id: Optional profile ID

        Returns:
            List of active applications
        """
        return self.list_applications(profile_id=profile_id, active_only=True)

    # ========================================================================
    # Analytics & Metrics
    # ========================================================================

    def get_statistics(
        self,
        profile_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get application statistics.

        Args:
            profile_id: Optional profile ID filter
            date_from: Start date filter
            date_to: End date filter

        Returns:
            Dictionary with statistics
        """
        query = self.session.query(JobApplication)

        if profile_id:
            query = query.filter(JobApplication.profile_id == profile_id)

        if date_from:
            query = query.filter(JobApplication.application_date >= date_from)

        if date_to:
            query = query.filter(JobApplication.application_date <= date_to)

        applications = query.all()

        # Calculate statistics
        total = len(applications)

        # Status breakdown
        status_counts = {}
        for status in JobApplication.VALID_STATUSES:
            status_counts[status] = sum(1 for a in applications if a.status == status)

        # Priority breakdown
        priority_counts = {
            JobApplication.PRIORITY_HIGH: sum(1 for a in applications if a.priority == JobApplication.PRIORITY_HIGH),
            JobApplication.PRIORITY_MEDIUM: sum(1 for a in applications if a.priority == JobApplication.PRIORITY_MEDIUM),
            JobApplication.PRIORITY_LOW: sum(1 for a in applications if a.priority == JobApplication.PRIORITY_LOW),
        }

        # Outcome metrics
        active = sum(1 for a in applications if a.is_active)
        offers = status_counts.get(JobApplication.STATUS_OFFER_RECEIVED, 0)
        accepted = status_counts.get(JobApplication.STATUS_ACCEPTED, 0)
        rejected = status_counts.get(JobApplication.STATUS_REJECTED, 0)

        # Response metrics
        responses = [a for a in applications if a.response_time_days is not None]
        avg_response_time = sum(a.response_time_days for a in responses) / len(responses) if responses else None

        # Time to outcome metrics
        completed = [a for a in applications if a.total_time_to_outcome_days is not None]
        avg_time_to_outcome = sum(a.total_time_to_outcome_days for a in completed) / len(completed) if completed else None

        # Interview metrics
        total_interviews = sum(a.interview_count or 0 for a in applications)
        apps_with_interviews = sum(1 for a in applications if (a.interview_count or 0) > 0)

        return {
            'total_applications': total,
            'active_applications': active,
            'status_breakdown': status_counts,
            'priority_breakdown': priority_counts,
            'offers_received': offers,
            'offers_accepted': accepted,
            'rejections': rejected,
            'offer_rate': (offers / total * 100) if total > 0 else 0,
            'acceptance_rate': (accepted / offers * 100) if offers > 0 else 0,
            'avg_response_time_days': avg_response_time,
            'avg_time_to_outcome_days': avg_time_to_outcome,
            'total_interviews': total_interviews,
            'applications_with_interviews': apps_with_interviews,
            'avg_interviews_per_app': (total_interviews / total) if total > 0 else 0,
        }

    def get_conversion_funnel(
        self,
        profile_id: Optional[int] = None
    ) -> Dict[str, int]:
        """Get conversion funnel showing progression through stages.

        Args:
            profile_id: Optional profile ID

        Returns:
            Dictionary mapping stage to count
        """
        query = self.session.query(JobApplication)

        if profile_id:
            query = query.filter(JobApplication.profile_id == profile_id)

        # Count by status in pipeline order
        funnel = {}
        for status in JobApplication.VALID_STATUSES:
            count = query.filter(JobApplication.status == status).count()
            funnel[status] = count

        return funnel

    def get_top_companies(
        self,
        profile_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """Get top companies by application count.

        Args:
            profile_id: Optional profile ID
            limit: Max companies to return

        Returns:
            List of (company_name, count) tuples
        """
        query = self.session.query(
            JobApplication.company_name,
            func.count(JobApplication.id).label('count')
        ).group_by(JobApplication.company_name)

        if profile_id:
            query = query.filter(JobApplication.profile_id == profile_id)

        query = query.order_by(desc('count')).limit(limit)

        return query.all()


__all__ = ['ApplicationTrackingService']
