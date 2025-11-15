"""Smoke tests for the PyQt6 main window."""

import pytest
from datetime import date

PyQt6 = pytest.importorskip("PyQt6")  # noqa: F401  # pragma: no cover
try:  # pragma: no cover - platform-dependent import guard
    from PyQt6.QtWidgets import QApplication
except Exception as exc:  # pragma: no cover
    pytest.skip(f"PyQt6 GUI dependencies unavailable: {exc}", allow_module_level=True)

from adaptive_resume.gui.main_window import MainWindow
from adaptive_resume.services.job_service import JobService
from adaptive_resume.services.profile_service import ProfileService
from adaptive_resume.models import Skill, Education


@pytest.fixture(scope="module")
def qapp():
    """Provide a shared QApplication instance for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_loads_profile_data(qapp, session):
    profile_service = ProfileService(session)
    job_service = JobService(session)

    profile = profile_service.create_profile(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="555-000-1234",
        city="Atlanta",
        state="GA",
        professional_summary="Experienced leader",
    )

    job = job_service.create_job(
        profile_id=profile.id,
        company_name="TechCorp",
        job_title="Program Manager",
        start_date=date(2020, 1, 1),
        end_date=None,
        is_current=True,
        location="Remote",
        description="Led strategic initiatives.",
    )
    job_service.create_bullet_point(
        job_id=job.id,
        content="Delivered a 25% revenue increase through cross-functional delivery.",
        display_order=1,
    )

    session.add(
        Skill(
            profile_id=profile.id,
            skill_name="Leadership",
            category="Soft Skills",
            proficiency_level="Advanced",
            years_experience=12,
            display_order=1,
        )
    )
    session.add(
        Education(
            profile_id=profile.id,
            institution="Georgia Tech",
            degree="BS Computer Science",
            field_of_study="Computer Science",
            start_date=date(2005, 8, 1),
            end_date=date(2009, 5, 1),
            display_order=1,
        )
    )
    session.commit()

    window = MainWindow(profile_service, job_service)
    try:
        # Smoke test: verify window can be instantiated with data
        assert window is not None
        assert "Adaptive Resume Generator" in window.windowTitle()
        # Verify the window has basic components
        assert hasattr(window, 'nav_menu')
        assert hasattr(window, 'stacked_widget')
    finally:
        window.close()
