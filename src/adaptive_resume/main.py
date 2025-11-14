"""
Main Application Entry Point.

Starts the Adaptive Resume Generator desktop application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from adaptive_resume.gui.main_window import MainWindow
from adaptive_resume.gui.database_manager import DatabaseManager
from adaptive_resume.gui.styles import get_stylesheet
from adaptive_resume.services.profile_service import ProfileService
from adaptive_resume.services.job_service import JobService


def main():
    """Main application entry point."""
    # Initialize database
    DatabaseManager.initialize()
    session = DatabaseManager.get_session()

    # Create services
    profile_service = ProfileService(session)
    job_service = JobService(session)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Adaptive Resume Generator")
    app.setOrganizationName("AlobarQuest")

    # Apply stylesheet
    app.setStyleSheet(get_stylesheet())

    # Create and show main window with services
    window = MainWindow(
        profile_service=profile_service,
        job_service=job_service
    )
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
