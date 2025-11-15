"""Smoke tests for PyQt6 dialog components."""

import pytest

PyQt6 = pytest.importorskip("PyQt6")  # noqa: F401  # pragma: no cover
try:  # pragma: no cover - platform-dependent import guard
    from PyQt6.QtWidgets import QApplication
except Exception as exc:  # pragma: no cover
    pytest.skip(f"PyQt6 GUI dependencies unavailable: {exc}", allow_module_level=True)

from adaptive_resume.gui.dialogs import JobDialog, ProfileDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_profile_dialog_returns_data(qapp):
    dialog = ProfileDialog(
        profile={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "city": "Atlanta",
        }
    )
    result = dialog.get_result()
    assert result.first_name == "Jane"
    assert result.email == "jane@example.com"
    dialog.close()


def test_job_dialog_returns_data(qapp):
    from PyQt6.QtCore import QDate

    dialog = JobDialog()
    dialog.company_name.setText("TechCorp")
    dialog.job_title.setText("Manager")
    dialog.location.setText("Remote")
    dialog.start_date.setDate(QDate(2020, 1, 1))
    dialog.description.setPlainText("Led a distributed engineering team.")
    dialog.bullets.addItem("Increased retention by 20% through mentorship programs")

    result = dialog.get_result()
    assert result.company_name == "TechCorp"
    assert result.start_date.year == 2020
    assert result.bullets
    dialog.close()
