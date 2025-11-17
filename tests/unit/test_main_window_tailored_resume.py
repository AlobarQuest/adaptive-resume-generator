"""Unit tests for MainWindow._on_tailored_resume_ready method."""

import json
import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock

PyQt6 = pytest.importorskip("PyQt6")  # noqa: F401  # pragma: no cover
try:  # pragma: no cover - platform-dependent import guard
    from PyQt6.QtWidgets import QApplication
except Exception as exc:  # pragma: no cover
    pytest.skip(f"PyQt6 GUI dependencies unavailable: {exc}", allow_module_level=True)

from adaptive_resume.gui.main_window import MainWindow
from adaptive_resume.services.resume_generator import TailoredResume
from adaptive_resume.services.matching_engine import ScoredAccomplishment
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.models.tailored_resume import TailoredResumeModel
from adaptive_resume.services.profile_service import ProfileService
from adaptive_resume.services.job_service import JobService


@pytest.fixture(scope="module")
def qapp():
    """Provide a shared QApplication instance for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp, session):
    """Create a MainWindow instance for testing."""
    profile_service = ProfileService(session)
    job_service = JobService(session)

    # Create a profile for testing
    profile = profile_service.create_profile(
        first_name="Test",
        last_name="User",
        email="test@example.com",
    )
    session.commit()

    # Patch DatabaseManager.get_session at the module level
    patcher = patch('adaptive_resume.gui.database_manager.DatabaseManager.get_session')
    mock_get_session = patcher.start()
    mock_get_session.return_value = session

    window = MainWindow(profile_service, job_service)

    yield window

    patcher.stop()
    window.close()


@pytest.fixture
def sample_tailored_resume():
    """Create a sample TailoredResume dataclass for testing."""
    accomplishments = [
        ScoredAccomplishment(
            bullet_id=1,
            bullet_text="Built scalable APIs with Python",
            job_title="Software Engineer",
            company_name="TechCorp",
            final_score=0.85,
            skill_match_score=0.9,
            semantic_score=0.8,
            recency_score=0.9,
            metrics_score=0.8,
            matched_skills=["Python", "API"],
            reasons=["Strong skill match", "Recent experience"],
            job_start_date=date(2020, 1, 1),
            is_current=True,
        ),
        ScoredAccomplishment(
            bullet_id=5,
            bullet_text="Reduced latency by 40%",
            job_title="Senior Engineer",
            company_name="TechCorp",
            final_score=0.75,
            skill_match_score=0.7,
            semantic_score=0.8,
            recency_score=0.7,
            metrics_score=0.8,
            matched_skills=["Performance"],
            reasons=["Quantified achievement"],
            job_start_date=date(2022, 1, 1),
            is_current=False,
        ),
    ]

    return TailoredResume(
        profile_id=1,
        job_posting_id=None,  # Will test both None and existing ID
        selected_accomplishments=accomplishments,
        skill_coverage={"Python": True, "AWS": False, "Docker": True},
        coverage_percentage=0.67,
        gaps=["AWS", "Kubernetes"],
        recommendations=["Add AWS experience", "Highlight Docker usage"],
        created_at=datetime.now(),
        job_title="Senior Python Developer",
        company_name="NewCorp",
    )


def test_on_tailored_resume_ready_creates_job_posting_when_none_exists(
    main_window, session, sample_tailored_resume
):
    """Test that a new JobPosting is created when job_posting_id is None."""
    # Ensure job_posting_id is None
    sample_tailored_resume.job_posting_id = None

    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Verify JobPosting was created
    job_posting = session.query(JobPosting).filter_by(
        company_name="NewCorp",
        job_title="Senior Python Developer"
    ).first()

    assert job_posting is not None
    assert job_posting.company_name == "NewCorp"
    assert job_posting.job_title == "Senior Python Developer"
    assert job_posting.profile_id == 1
    assert job_posting.raw_text == ""
    assert job_posting.requirements_json == "{}"

    # Verify TailoredResumeModel was created
    resume_model = session.query(TailoredResumeModel).filter_by(
        job_posting_id=job_posting.id
    ).first()

    assert resume_model is not None
    assert resume_model.profile_id == 1
    assert resume_model.job_posting_id == job_posting.id


def test_on_tailored_resume_ready_uses_existing_job_posting(
    main_window, session, sample_tailored_resume
):
    """Test that existing JobPosting is used when job_posting_id is provided."""
    # Create a job posting first
    job_posting = JobPosting(
        profile_id=1,
        company_name="ExistingCorp",
        job_title="Existing Position",
        raw_text="Original job posting text",
        requirements_json='{"skills": ["Python"]}',
    )
    session.add(job_posting)
    session.commit()
    session.refresh(job_posting)

    # Set the job_posting_id in the tailored resume
    sample_tailored_resume.job_posting_id = job_posting.id

    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Count existing job postings
    initial_count = session.query(JobPosting).count()

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Verify no new JobPosting was created
    final_count = session.query(JobPosting).count()
    assert final_count == initial_count

    # Verify TailoredResumeModel uses the existing job posting
    resume_model = session.query(TailoredResumeModel).filter_by(
        job_posting_id=job_posting.id
    ).first()

    assert resume_model is not None
    assert resume_model.job_posting_id == job_posting.id


def test_on_tailored_resume_ready_correctly_serializes_accomplishment_ids(
    main_window, session, sample_tailored_resume
):
    """Test that accomplishment IDs are correctly extracted and serialized."""
    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Get the created resume model
    resume_model = session.query(TailoredResumeModel).first()

    # Verify selected_accomplishment_ids is correctly serialized
    selected_ids = json.loads(resume_model.selected_accomplishment_ids)
    assert selected_ids == [1, 5]  # bullet_ids from sample data


def test_on_tailored_resume_ready_correctly_serializes_skill_coverage(
    main_window, session, sample_tailored_resume
):
    """Test that skill coverage is correctly serialized as JSON."""
    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Get the created resume model
    resume_model = session.query(TailoredResumeModel).first()

    # Verify skill_coverage_json is correctly serialized
    skill_coverage = json.loads(resume_model.skill_coverage_json)
    assert skill_coverage == {"Python": True, "AWS": False, "Docker": True}

    # Verify coverage_percentage is stored correctly
    assert resume_model.coverage_percentage == 0.67


def test_on_tailored_resume_ready_correctly_serializes_gaps_and_recommendations(
    main_window, session, sample_tailored_resume
):
    """Test that gaps and recommendations are correctly serialized."""
    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Get the created resume model
    resume_model = session.query(TailoredResumeModel).first()

    # Verify gaps_json is correctly serialized
    gaps = json.loads(resume_model.gaps_json)
    assert gaps == ["AWS", "Kubernetes"]

    # Verify recommendations_json is correctly serialized
    recommendations = json.loads(resume_model.recommendations_json)
    assert recommendations == ["Add AWS experience", "Highlight Docker usage"]


def test_on_tailored_resume_ready_sets_current_tailored_resume_id(
    main_window, session, sample_tailored_resume
):
    """Test that current_tailored_resume_id is set on the window."""
    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Verify attribute doesn't exist initially or is None
    assert not hasattr(main_window, 'current_tailored_resume_id') or \
           main_window.current_tailored_resume_id is None

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Verify current_tailored_resume_id is set
    assert hasattr(main_window, 'current_tailored_resume_id')
    assert main_window.current_tailored_resume_id is not None
    assert isinstance(main_window.current_tailored_resume_id, int)

    # Verify it matches the created resume model
    resume_model = session.query(TailoredResumeModel).first()
    assert main_window.current_tailored_resume_id == resume_model.id


def test_on_tailored_resume_ready_displays_results_and_navigates(
    main_window, session, sample_tailored_resume
):
    """Test that results are displayed and navigation occurs."""
    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Verify display_results was called with the tailored resume
    main_window.results_screen.display_results.assert_called_once_with(
        sample_tailored_resume
    )

    # Verify navigation to results screen
    main_window._navigate_to.assert_called_once_with("results")


def test_on_tailored_resume_ready_handles_empty_accomplishments(
    main_window, session
):
    """Test that empty accomplishments list is handled correctly."""
    # Create tailored resume with no accomplishments
    empty_resume = TailoredResume(
        profile_id=1,
        job_posting_id=None,
        selected_accomplishments=[],  # Empty list
        skill_coverage={},
        coverage_percentage=0.0,
        gaps=["Python", "AWS"],
        recommendations=["Add relevant experience"],
        job_title="Developer",
        company_name="TestCorp",
    )

    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(empty_resume)

    # Verify resume model was created
    resume_model = session.query(TailoredResumeModel).first()
    assert resume_model is not None

    # Verify empty list is serialized correctly
    selected_ids = json.loads(resume_model.selected_accomplishment_ids)
    assert selected_ids == []


def test_on_tailored_resume_ready_handles_none_company_and_title(
    main_window, session
):
    """Test that None values for company and title are handled with defaults."""
    # Create tailored resume with None values
    resume = TailoredResume(
        profile_id=1,
        job_posting_id=None,
        selected_accomplishments=[],
        skill_coverage={},
        coverage_percentage=0.0,
        gaps=[],
        recommendations=[],
        job_title="",  # Empty string
        company_name="",  # Empty string
    )

    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(resume)

    # Verify JobPosting was created with default values
    job_posting = session.query(JobPosting).first()
    assert job_posting is not None
    assert job_posting.company_name == "Unknown Company"
    assert job_posting.job_title == "Unknown Position"


def test_on_tailored_resume_ready_handles_match_score_when_present(
    main_window, session, sample_tailored_resume
):
    """Test that match_score is stored when present in the dataclass."""
    # Add match_score to the tailored resume (using setattr since it's not in __init__)
    sample_tailored_resume.match_score = 0.82

    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Verify match_score is stored
    resume_model = session.query(TailoredResumeModel).first()
    assert resume_model.match_score == 0.82


def test_on_tailored_resume_ready_handles_match_score_when_absent(
    main_window, session, sample_tailored_resume
):
    """Test that match_score is None when not present in the dataclass."""
    # Ensure match_score doesn't exist (it's optional)
    if hasattr(sample_tailored_resume, 'match_score'):
        delattr(sample_tailored_resume, 'match_score')

    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Verify match_score is None
    resume_model = session.query(TailoredResumeModel).first()
    assert resume_model.match_score is None


def test_on_tailored_resume_ready_persists_data_to_database(
    main_window, session, sample_tailored_resume
):
    """Test that data is properly persisted to the database."""
    # Mock the results screen and navigation
    main_window.results_screen = Mock()
    main_window._navigate_to = Mock()

    # Call the method
    main_window._on_tailored_resume_ready(sample_tailored_resume)

    # Verify data was persisted
    resume_model = session.query(TailoredResumeModel).first()
    assert resume_model is not None
    assert resume_model.profile_id == 1
