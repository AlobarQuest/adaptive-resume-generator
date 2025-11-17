"""Unit tests for ApplicationTrackingService."""

import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from adaptive_resume.models.base import Base
from adaptive_resume.models.profile import Profile
from adaptive_resume.models.job_application import JobApplication
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.services.application_tracking_service import ApplicationTrackingService


@pytest.fixture
def session():
    """Create in-memory database session for testing."""
    engine = create_engine('sqlite:///:memory:')
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
        email="test@example.com"
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@pytest.fixture
def job_posting(session, profile):
    """Create a test job posting."""
    posting = JobPosting(
        profile_id=profile.id,
        company_name="Test Company",
        job_title="Software Engineer",
        raw_text="Full job description..."
    )
    session.add(posting)
    session.commit()
    session.refresh(posting)
    return posting


@pytest.fixture
def service(session):
    """Create ApplicationTrackingService."""
    return ApplicationTrackingService(session)


class TestApplicationCRUD:
    """Tests for application CRUD operations."""

    def test_create_application(self, service, profile):
        """Test creating an application."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Google",
            position_title="Senior Engineer",
            job_description="Great job",
            job_url="https://google.com/careers/123"
        )

        assert app.id is not None
        assert app.company_name == "Google"
        assert app.position_title == "Senior Engineer"
        assert app.status == JobApplication.STATUS_DISCOVERED
        assert app.priority == JobApplication.PRIORITY_MEDIUM
        assert app.discovered_date == date.today()

    def test_create_from_job_posting(self, service, profile, job_posting):
        """Test creating application from job posting."""
        app = service.create_from_job_posting(
            profile_id=profile.id,
            job_posting=job_posting
        )

        assert app.company_name == job_posting.company_name
        assert app.position_title == job_posting.job_title
        assert app.job_posting_id == job_posting.id
        assert app.status == JobApplication.STATUS_INTERESTED

    def test_get_application(self, service, profile):
        """Test getting an application by ID."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Microsoft",
            position_title="Engineer"
        )

        retrieved = service.get_application(app.id)
        assert retrieved is not None
        assert retrieved.id == app.id
        assert retrieved.company_name == "Microsoft"

    def test_get_nonexistent_application(self, service):
        """Test getting nonexistent application returns None."""
        app = service.get_application(9999)
        assert app is None

    def test_update_application(self, service, profile):
        """Test updating application fields."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Apple",
            position_title="Engineer"
        )

        updated = service.update_application(
            app.id,
            company_name="Apple Inc.",
            position_title="Senior Engineer",
            salary_range="$150k-$200k"
        )

        assert updated.company_name == "Apple Inc."
        assert updated.position_title == "Senior Engineer"
        assert updated.salary_range == "$150k-$200k"

    def test_update_nonexistent_application_raises(self, service):
        """Test updating nonexistent application raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            service.update_application(9999, company_name="Test")

    def test_delete_application(self, service, profile):
        """Test deleting an application."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Amazon",
            position_title="Engineer"
        )

        assert service.delete_application(app.id) is True
        assert service.get_application(app.id) is None

    def test_delete_nonexistent_application(self, service):
        """Test deleting nonexistent application returns False."""
        assert service.delete_application(9999) is False


class TestStatusManagement:
    """Tests for status management."""

    def test_update_status(self, service, profile):
        """Test updating application status."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Netflix",
            position_title="Engineer"
        )

        updated = service.update_status(
            app.id,
            JobApplication.STATUS_APPLIED,
            notes="Submitted via website"
        )

        assert updated.status == JobApplication.STATUS_APPLIED
        assert "Submitted via website" in updated.notes

    def test_update_status_sets_application_date(self, service, profile):
        """Test updating to 'applied' sets application_date."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Uber",
            position_title="Engineer"
        )

        updated = service.update_status(app.id, JobApplication.STATUS_APPLIED)

        assert updated.application_date == date.today()

    def test_update_status_sets_response_date(self, service, profile):
        """Test updating to screening/interview sets first_response_date."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Lyft",
            position_title="Engineer",
            status=JobApplication.STATUS_APPLIED
        )

        # Set application date to past
        app.application_date = date.today() - timedelta(days=5)
        service.session.commit()

        updated = service.update_status(app.id, JobApplication.STATUS_SCREENING)

        assert updated.first_response_date == date.today()
        assert updated.response_time_days == 5

    def test_update_status_sets_offer_date(self, service, profile):
        """Test updating to offer_received sets offer_date."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Airbnb",
            position_title="Engineer"
        )

        updated = service.update_status(app.id, JobApplication.STATUS_OFFER_RECEIVED)

        assert updated.offer_date == date.today()

    def test_update_status_sets_acceptance_date(self, service, profile):
        """Test updating to accepted sets acceptance_date."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Stripe",
            position_title="Engineer",
            status=JobApplication.STATUS_APPLIED
        )

        # Set application date
        app.application_date = date.today() - timedelta(days=30)
        service.session.commit()

        updated = service.update_status(app.id, JobApplication.STATUS_ACCEPTED)

        assert updated.acceptance_date == date.today()
        assert updated.total_time_to_outcome_days == 30

    def test_update_status_sets_rejection_date(self, service, profile):
        """Test updating to rejected sets rejection_date."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Snap",
            position_title="Engineer",
            status=JobApplication.STATUS_APPLIED
        )

        app.application_date = date.today() - timedelta(days=20)
        service.session.commit()

        updated = service.update_status(app.id, JobApplication.STATUS_REJECTED)

        assert updated.rejection_date == date.today()
        assert updated.total_time_to_outcome_days == 20

    def test_update_status_invalid_status_raises(self, service, profile):
        """Test updating with invalid status raises ValueError."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Twitter",
            position_title="Engineer"
        )

        with pytest.raises(ValueError, match="Invalid status"):
            service.update_status(app.id, "invalid_status")

    def test_mark_as_applied(self, service, profile):
        """Test marking application as applied."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Meta",
            position_title="Engineer"
        )

        updated = service.mark_as_applied(
            app.id,
            application_method="linkedin"
        )

        assert updated.status == JobApplication.STATUS_APPLIED
        assert updated.application_method == "linkedin"
        assert updated.application_date == date.today()


class TestInterviewManagement:
    """Tests for interview management."""

    def test_add_interview(self, service, profile):
        """Test adding an interview."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Salesforce",
            position_title="Engineer"
        )

        interview_date = date.today() + timedelta(days=7)
        updated = service.add_interview(
            app.id,
            interview_date,
            interview_type="phone_screen",
            notes="With hiring manager"
        )

        assert updated.interview_count == 1
        assert updated.status == JobApplication.STATUS_INTERVIEW

        interviews = updated.get_interviews()
        assert len(interviews) == 1
        assert interviews[0]['type'] == "phone_screen"
        assert interviews[0]['notes'] == "With hiring manager"

    def test_add_multiple_interviews(self, service, profile):
        """Test adding multiple interviews."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Oracle",
            position_title="Engineer"
        )

        # Add first interview
        service.add_interview(app.id, date.today() + timedelta(days=5), "phone_screen")

        # Add second interview
        service.add_interview(app.id, date.today() + timedelta(days=10), "technical")

        # Add third interview
        updated = service.add_interview(app.id, date.today() + timedelta(days=15), "onsite")

        assert updated.interview_count == 3

        interviews = updated.get_interviews()
        assert len(interviews) == 3
        assert interviews[0]['type'] == "phone_screen"
        assert interviews[1]['type'] == "technical"
        assert interviews[2]['type'] == "onsite"

    def test_add_interview_sets_first_response_date(self, service, profile):
        """Test adding interview sets first_response_date if not set."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Adobe",
            position_title="Engineer",
            status=JobApplication.STATUS_APPLIED
        )

        app.application_date = date.today() - timedelta(days=7)
        service.session.commit()

        interview_date = date.today()
        updated = service.add_interview(app.id, interview_date)

        assert updated.first_response_date == interview_date
        assert updated.response_time_days == 7

    def test_get_upcoming_interviews(self, service, profile):
        """Test getting upcoming interviews."""
        # Create application with upcoming interview
        app1 = service.create_application(
            profile_id=profile.id,
            company_name="IBM",
            position_title="Engineer"
        )
        service.add_interview(app1.id, date.today() + timedelta(days=3), "phone_screen")

        # Create application with past interview
        app2 = service.create_application(
            profile_id=profile.id,
            company_name="Intel",
            position_title="Engineer"
        )
        service.add_interview(app2.id, date.today() - timedelta(days=5), "onsite")

        # Create application with interview far in future
        app3 = service.create_application(
            profile_id=profile.id,
            company_name="AMD",
            position_title="Engineer"
        )
        service.add_interview(app3.id, date.today() + timedelta(days=20), "final")

        # Get upcoming interviews (next 7 days)
        upcoming = service.get_upcoming_interviews(profile_id=profile.id, days_ahead=7)

        assert len(upcoming) == 1
        assert upcoming[0][0].id == app1.id


class TestContactManagement:
    """Tests for contact management."""

    def test_update_contact(self, service, profile):
        """Test updating contact information."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="Tesla",
            position_title="Engineer"
        )

        updated = service.update_contact(
            app.id,
            contact_person="John Doe",
            contact_email="john@tesla.com",
            recruiter_name="Jane Smith"
        )

        assert updated.contact_person == "John Doe"
        assert updated.contact_email == "john@tesla.com"
        assert updated.recruiter_name == "Jane Smith"

    def test_schedule_followup(self, service, profile):
        """Test scheduling a follow-up."""
        app = service.create_application(
            profile_id=profile.id,
            company_name="SpaceX",
            position_title="Engineer"
        )

        followup_date = date.today() + timedelta(days=14)
        updated = service.schedule_followup(
            app.id,
            followup_date,
            notes="Follow up on application status"
        )

        assert updated.next_followup_date == followup_date
        assert "Follow up on application status" in updated.notes

    def test_get_followups_due(self, service, profile):
        """Test getting follow-ups that are due."""
        # Create app with follow-up due today
        app1 = service.create_application(
            profile_id=profile.id,
            company_name="Rivian",
            position_title="Engineer"
        )
        service.schedule_followup(app1.id, date.today())

        # Create app with follow-up due in past
        app2 = service.create_application(
            profile_id=profile.id,
            company_name="Lucid",
            position_title="Engineer"
        )
        service.schedule_followup(app2.id, date.today() - timedelta(days=3))

        # Create app with follow-up in future
        app3 = service.create_application(
            profile_id=profile.id,
            company_name="Nio",
            position_title="Engineer"
        )
        service.schedule_followup(app3.id, date.today() + timedelta(days=7))

        # Get follow-ups due
        due = service.get_followups_due(profile_id=profile.id)

        assert len(due) == 2
        assert {app.id for app in due} == {app1.id, app2.id}


class TestQueryingFiltering:
    """Tests for querying and filtering applications."""

    def test_list_applications_all(self, service, profile):
        """Test listing all applications."""
        service.create_application(profile.id, "Company1", "Position1")
        service.create_application(profile.id, "Company2", "Position2")
        service.create_application(profile.id, "Company3", "Position3")

        apps = service.list_applications(profile_id=profile.id)

        assert len(apps) == 3

    def test_list_applications_by_status(self, service, profile):
        """Test filtering by status."""
        app1 = service.create_application(profile.id, "Company1", "Position1")
        app2 = service.create_application(profile.id, "Company2", "Position2")
        service.update_status(app2.id, JobApplication.STATUS_APPLIED)

        discovered = service.list_applications(
            profile_id=profile.id,
            status=JobApplication.STATUS_DISCOVERED
        )

        assert len(discovered) == 1
        assert discovered[0].id == app1.id

    def test_list_applications_by_priority(self, service, profile):
        """Test filtering by priority."""
        app1 = service.create_application(
            profile.id, "Company1", "Position1", priority=JobApplication.PRIORITY_HIGH
        )
        app2 = service.create_application(
            profile.id, "Company2", "Position2", priority=JobApplication.PRIORITY_LOW
        )

        high_priority = service.list_applications(
            profile_id=profile.id,
            priority=JobApplication.PRIORITY_HIGH
        )

        assert len(high_priority) == 1
        assert high_priority[0].id == app1.id

    def test_list_applications_active_only(self, service, profile):
        """Test filtering active applications only."""
        app1 = service.create_application(profile.id, "Company1", "Position1")
        app2 = service.create_application(profile.id, "Company2", "Position2")
        service.update_status(app2.id, JobApplication.STATUS_REJECTED)

        active = service.list_applications(profile_id=profile.id, active_only=True)

        assert len(active) == 1
        assert active[0].id == app1.id

    def test_list_applications_by_company(self, service, profile):
        """Test filtering by company name."""
        service.create_application(profile.id, "Google", "Engineer")
        service.create_application(profile.id, "Microsoft", "Engineer")
        service.create_application(profile.id, "Google Inc", "Manager")

        google_apps = service.list_applications(
            profile_id=profile.id,
            company_name="Google"
        )

        assert len(google_apps) == 2

    def test_get_by_status(self, service, profile):
        """Test get_by_status convenience method."""
        app1 = service.create_application(profile.id, "Company1", "Position1")
        service.create_application(profile.id, "Company2", "Position2")
        service.mark_as_applied(app1.id)

        applied = service.get_by_status(
            JobApplication.STATUS_APPLIED,
            profile_id=profile.id
        )

        assert len(applied) == 1
        assert applied[0].id == app1.id

    def test_get_active_applications(self, service, profile):
        """Test get_active_applications convenience method."""
        app1 = service.create_application(profile.id, "Company1", "Position1")
        app2 = service.create_application(profile.id, "Company2", "Position2")
        service.update_status(app2.id, JobApplication.STATUS_WITHDRAWN)

        active = service.get_active_applications(profile_id=profile.id)

        assert len(active) == 1
        assert active[0].id == app1.id


class TestAnalyticsMetrics:
    """Tests for analytics and metrics."""

    def test_get_statistics_basic(self, service, profile):
        """Test getting basic statistics."""
        service.create_application(profile.id, "Company1", "Position1")
        service.create_application(profile.id, "Company2", "Position2")

        stats = service.get_statistics(profile_id=profile.id)

        assert stats['total_applications'] == 2
        assert stats['active_applications'] == 2

    def test_get_statistics_status_breakdown(self, service, profile):
        """Test status breakdown in statistics."""
        app1 = service.create_application(profile.id, "Company1", "Position1")
        app2 = service.create_application(profile.id, "Company2", "Position2")
        service.mark_as_applied(app1.id)
        service.update_status(app2.id, JobApplication.STATUS_INTERVIEW)

        stats = service.get_statistics(profile_id=profile.id)

        assert stats['status_breakdown'][JobApplication.STATUS_APPLIED] == 1
        assert stats['status_breakdown'][JobApplication.STATUS_INTERVIEW] == 1

    def test_get_statistics_offer_rate(self, service, profile):
        """Test offer rate calculation."""
        # Create 5 applications
        for i in range(5):
            service.create_application(profile.id, f"Company{i}", "Engineer")

        # Get 2 offers
        app1 = service.create_application(profile.id, "Company5", "Engineer")
        app2 = service.create_application(profile.id, "Company6", "Engineer")
        service.update_status(app1.id, JobApplication.STATUS_OFFER_RECEIVED)
        service.update_status(app2.id, JobApplication.STATUS_OFFER_RECEIVED)

        stats = service.get_statistics(profile_id=profile.id)

        assert stats['total_applications'] == 7
        assert stats['offers_received'] == 2
        assert stats['offer_rate'] == pytest.approx(2/7 * 100, rel=0.01)

    def test_get_statistics_avg_response_time(self, service, profile):
        """Test average response time calculation."""
        # App 1: 5 days to response
        app1 = service.create_application(profile.id, "Company1", "Engineer")
        app1.application_date = date.today() - timedelta(days=10)
        app1.first_response_date = date.today() - timedelta(days=5)
        app1.calculate_response_time()
        service.session.commit()

        # App 2: 10 days to response
        app2 = service.create_application(profile.id, "Company2", "Engineer")
        app2.application_date = date.today() - timedelta(days=15)
        app2.first_response_date = date.today() - timedelta(days=5)
        app2.calculate_response_time()
        service.session.commit()

        stats = service.get_statistics(profile_id=profile.id)

        assert stats['avg_response_time_days'] == pytest.approx(7.5, rel=0.01)

    def test_get_conversion_funnel(self, service, profile):
        """Test conversion funnel calculation."""
        # Create apps at different stages
        service.create_application(profile.id, "C1", "E1")  # discovered
        app2 = service.create_application(profile.id, "C2", "E2")
        service.mark_as_applied(app2.id)  # applied
        app3 = service.create_application(profile.id, "C3", "E3")
        service.update_status(app3.id, JobApplication.STATUS_INTERVIEW)  # interview

        funnel = service.get_conversion_funnel(profile_id=profile.id)

        assert funnel[JobApplication.STATUS_DISCOVERED] == 1
        assert funnel[JobApplication.STATUS_APPLIED] == 1
        assert funnel[JobApplication.STATUS_INTERVIEW] == 1

    def test_get_top_companies(self, service, profile):
        """Test getting top companies by application count."""
        # Create multiple applications to same companies
        service.create_application(profile.id, "Google", "Engineer 1")
        service.create_application(profile.id, "Google", "Engineer 2")
        service.create_application(profile.id, "Google", "Manager")
        service.create_application(profile.id, "Microsoft", "Engineer")
        service.create_application(profile.id, "Microsoft", "Senior Engineer")
        service.create_application(profile.id, "Amazon", "Engineer")

        top_companies = service.get_top_companies(profile_id=profile.id, limit=2)

        assert len(top_companies) == 2
        assert top_companies[0][0] == "Google"
        assert top_companies[0][1] == 3
        assert top_companies[1][0] == "Microsoft"
        assert top_companies[1][1] == 2
