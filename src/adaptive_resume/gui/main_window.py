"""Primary PyQt6 window for the Adaptive Resume Generator."""

from __future__ import annotations

__all__ = ["MainWindow"]

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - import guard depends on platform runtime
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QAction
    from PyQt6.QtWidgets import (
        QMenuBar,
        QDialog,
        QHBoxLayout,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSplitter,
        QStatusBar,
        QToolBar,
        QVBoxLayout,
        QWidget,
        QStackedWidget,
    )
except Exception as exc:  # pragma: no cover - handled during runtime import
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.models import Profile, BulletPoint
from adaptive_resume.models.base import DEFAULT_PROFILE_ID
from adaptive_resume.services.job_service import JobService
from adaptive_resume.services.profile_service import ProfileService
from adaptive_resume.services.skill_service import SkillService
from adaptive_resume.services.education_service import EducationService
from adaptive_resume.services.certification_service import CertificationService

from .dialogs import (
    JobDialog,
    ProfileDialog,
    SettingsDialog,
    BulletEnhancementDialog,
    CompanyDialog,
    CompanyData,
    ResumePDFPreviewDialog,
    ResumeImportDialog,
    ResumePreviewDialog,
    EducationDialog,
    SkillDialog,
    RecentlyDeletedDialog,
)
from .widgets import NavigationMenu
from .screens import (
    DashboardScreen,
    ProfileManagementScreen,
    CompaniesRolesScreen,
    GeneralInfoScreen,
    EducationScreen,
    SkillsScreen,
    JobPostingScreen,
    ReviewPrintScreen,
    TailoringResultsScreen,
    ApplicationsScreen,
    ManageJobPostingsScreen,
)


class MainWindow(QMainWindow):
    """Top-level window with navigation menu and screen-based interface."""

    def __init__(
        self,
        profile_service: ProfileService,
        job_service: JobService,
        skill_service: Optional[SkillService] = None,
        education_service: Optional[EducationService] = None,
        certification_service: Optional[CertificationService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.profile_service = profile_service
        self.job_service = job_service
        self.skill_service = skill_service or SkillService(profile_service.session)
        self.education_service = education_service or EducationService(profile_service.session)
        self.certification_service = certification_service or CertificationService(profile_service.session)
        # Single-profile architecture: always use DEFAULT_PROFILE_ID
        self.current_profile_id: int = DEFAULT_PROFILE_ID
        self.current_tailored_resume_id: Optional[int] = None

        self.resize(1200, 720)

        # Ensure profile exists, create if needed
        self._ensure_profile()

        self._setup_ui()
        self._update_window_title()

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        """Setup the main UI with navigation menu and stacked screens."""
        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left navigation menu
        self.nav_menu = NavigationMenu()
        self.nav_menu.screen_changed.connect(self._on_screen_changed)
        layout.addWidget(self.nav_menu)

        # Right side - stacked screens
        self.stacked_widget = QStackedWidget()

        # Create all screens
        self.dashboard_screen = DashboardScreen(
            profile_service=self.profile_service,
            job_service=self.job_service,
            skill_service=self.skill_service,
            education_service=self.education_service,
        )
        self.dashboard_screen.navigate_to_upload.connect(lambda: self._navigate_to("upload"))
        self.dashboard_screen.navigate_to_companies.connect(lambda: self._navigate_to("companies"))
        self.dashboard_screen.navigate_to_general.connect(lambda: self._navigate_to("general"))
        self.dashboard_screen.navigate_to_profile_creation.connect(self._edit_profile)  # Changed to edit existing profile

        self.profile_screen = ProfileManagementScreen(
            profile_service=self.profile_service,
        )
        # Note: ProfileManagementScreen will be repurposed to just show/edit current profile
        self.profile_screen.edit_profile_requested.connect(self._edit_profile)
        self.profile_screen.import_resume_requested.connect(self._import_resume)

        self.companies_screen = CompaniesRolesScreen(
            job_service=self.job_service,
        )

        self.general_screen = GeneralInfoScreen(
            skill_service=self.skill_service,
            education_service=self.education_service,
        )

        self.education_screen = EducationScreen(
            education_service=self.education_service,
        )
        self.education_screen.add_education_requested.connect(self._add_education)
        self.education_screen.edit_education_requested.connect(self._edit_education)
        self.education_screen.delete_education_requested.connect(self._delete_education)

        self.skills_screen = SkillsScreen(
            skill_service=self.skill_service,
        )
        self.skills_screen.add_skill_requested.connect(self._add_skill)
        self.skills_screen.edit_skill_requested.connect(self._edit_skill)
        self.skills_screen.delete_skill_requested.connect(self._delete_skill)

        self.upload_screen = JobPostingScreen(
            profile_service=self.profile_service,
            job_service=self.job_service,
        )
        self.upload_screen.tailored_resume_ready.connect(self._on_tailored_resume_ready)

        self.results_screen = TailoringResultsScreen()
        self.results_screen.generate_pdf_requested.connect(self._generate_pdf_resume)
        self.results_screen.start_over_requested.connect(lambda: self._navigate_to("upload"))

        self.review_screen = ReviewPrintScreen()

        self.applications_screen = ApplicationsScreen()
        self.applications_screen.application_selected.connect(self._on_application_selected)

        self.manage_postings_screen = ManageJobPostingsScreen()

        # Add screens to stacked widget
        self.screens = {
            "dashboard": self.dashboard_screen,
            "profile": self.profile_screen,
            "companies": self.companies_screen,
            "general": self.general_screen,
            "education": self.education_screen,
            "skills": self.skills_screen,
            "upload": self.upload_screen,
            "manage_postings": self.manage_postings_screen,
            "applications": self.applications_screen,
            "results": self.results_screen,
            "review": self.review_screen,
        }

        for screen in self.screens.values():
            self.stacked_widget.addWidget(screen)

        layout.addWidget(self.stacked_widget)

        central.setLayout(layout)
        self.setCentralWidget(central)

        # Connect signals from companies screen (for job/bullet management)
        jobs_view = self.companies_screen.get_jobs_view()
        jobs_view.job_selected.connect(self._on_job_selected)
        jobs_view.bullet_enhance_requested.connect(self._on_enhance_bullet)
        self.companies_screen.add_job_requested.connect(self._add_job)
        self.companies_screen.edit_job_requested.connect(self._edit_job)
        self.companies_screen.delete_job_requested.connect(self._delete_job)
        self.companies_screen.view_recently_deleted_requested.connect(self._view_recently_deleted)

        # Connect signals for company management
        self.companies_screen.edit_company_requested.connect(self._edit_company)
        self.companies_screen.delete_company_requested.connect(self._delete_company)

        # Hide menu bar completely - navigation only
        self.menuBar().hide()

        # Status bar only
        self.setStatusBar(QStatusBar(self))

        # Set initial screen
        self._navigate_to("dashboard")


    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _navigate_to(self, screen_id: str, update_nav: bool = True) -> None:
        """Navigate to a screen.

        Args:
            screen_id: The ID of the screen to navigate to
            update_nav: Whether to update the navigation menu (False when called from nav menu)
        """
        if screen_id == "settings":
            self._open_settings()
            return

        if screen_id in self.screens:
            screen = self.screens[screen_id]
            self.stacked_widget.setCurrentWidget(screen)
            if update_nav:
                # Only update nav menu if not already coming from nav menu click
                # Temporarily disconnect to avoid recursion
                self.nav_menu.screen_changed.disconnect(self._on_screen_changed)
                self.nav_menu.set_current_screen(screen_id)
                self.nav_menu.screen_changed.connect(self._on_screen_changed)
            screen.on_screen_shown()

    def _on_screen_changed(self, screen_id: str) -> None:
        """Handle screen change from navigation menu."""
        self._navigate_to(screen_id, update_nav=False)

    def _on_tailored_resume_ready(self, tailored_resume) -> None:
        """Handle when tailored resume is ready from job posting analysis."""
        # The tailored_resume from ProcessingWorker is a TailoredResume dataclass
        # We need to persist it to the database to get an ID for PDF generation, etc.
        import json
        from adaptive_resume.models.tailored_resume import TailoredResumeModel
        from adaptive_resume.models.job_posting import JobPosting
        from adaptive_resume.gui.database_manager import DatabaseManager

        session = DatabaseManager.get_session()

        # First, save the JobPosting if it doesn't exist
        job_posting_id = tailored_resume.job_posting_id
        if job_posting_id is None:
            # Create and save a new job posting with all metadata
            job_posting = JobPosting(
                profile_id=tailored_resume.profile_id,
                company_name=tailored_resume.company_name or "Unknown Company",
                job_title=tailored_resume.job_title or "Unknown Position",
                raw_text=tailored_resume.raw_job_text or "",
                location=tailored_resume.location or None,
                salary_range=tailored_resume.salary_range or None,
                application_url=tailored_resume.application_url or None,
                notes=tailored_resume.notes or None,
                requirements_json="{}",
                source=tailored_resume.source or "paste",
            )
            session.add(job_posting)
            session.commit()
            session.refresh(job_posting)
            job_posting_id = job_posting.id

            logger.info(f"Created new JobPosting: id={job_posting.id}, company={job_posting.company_name}, title={job_posting.job_title}, location={job_posting.location}")

        # Create TailoredResumeModel from the dataclass
        selected_ids = [acc.bullet_id for acc in tailored_resume.selected_accomplishments]

        # Serialize full accomplishment data for later PDF generation
        accomplishments_data = []
        for acc in tailored_resume.selected_accomplishments:
            accomplishments_data.append({
                'bullet_id': acc.bullet_id,
                'job_id': acc.job_id,
                'text': acc.text,
                'skill_match_score': acc.skill_match_score,
                'semantic_score': acc.semantic_score,
                'recency_score': acc.recency_score,
                'metrics_score': acc.metrics_score,
                'total_score': acc.total_score,
                'matched_skills': acc.matched_skills,
                'relevance_explanation': acc.relevance_explanation
            })

        resume_model = TailoredResumeModel(
            profile_id=tailored_resume.profile_id,
            job_posting_id=job_posting_id,
            selected_accomplishment_ids=json.dumps(selected_ids),
            selected_accomplishments_json=json.dumps(accomplishments_data),
            skill_coverage_json=json.dumps(tailored_resume.skill_coverage),
            coverage_percentage=tailored_resume.coverage_percentage,
            gaps_json=json.dumps(tailored_resume.gaps),
            recommendations_json=json.dumps(tailored_resume.recommendations),
            match_score=getattr(tailored_resume, 'match_score', None),
        )

        session.add(resume_model)
        session.commit()
        session.refresh(resume_model)

        logger.info(f"Created TailoredResumeModel: id={resume_model.id}, job_posting_id={job_posting_id}, accomplishments={len(selected_ids)}")

        # Update the dataclass with database IDs for use in results screen
        tailored_resume.job_posting_id = job_posting_id
        tailored_resume.id = resume_model.id

        self.current_tailored_resume_id = resume_model.id
        self.results_screen.display_results(tailored_resume)
        self._navigate_to("results")

    def _refresh_current_screen(self) -> None:
        """Refresh the current screen."""
        current_screen = self.stacked_widget.currentWidget()
        if hasattr(current_screen, 'on_screen_shown'):
            current_screen.on_screen_shown()

    # ------------------------------------------------------------------
    # Profile management (single-profile mode)
    # ------------------------------------------------------------------
    def _ensure_profile(self) -> None:
        """Ensure a default profile exists, creating one if needed."""
        profile = self.profile_service.get_default_profile()

        if profile is None:
            # No profile exists - check if this is first run
            # The welcome wizard will handle profile creation
            # For now, create a minimal placeholder
            profile = self.profile_service.ensure_profile_exists()

            # Show welcome dialog to complete profile setup
            QMessageBox.information(
                self,
                "Welcome!",
                "Welcome to Adaptive Resume Generator!\n\n"
                "Let's get started by setting up your profile.",
                QMessageBox.StandardButton.Ok
            )
            # Open profile edit dialog
            self._edit_profile()

    def _update_window_title(self) -> None:
        """Update window title with current profile name."""
        try:
            profile = self.profile_service.get_default_profile()
            if profile and profile.first_name and profile.last_name:
                self.setWindowTitle(
                    f"Adaptive Resume Generator - {profile.first_name} {profile.last_name}"
                )
            else:
                self.setWindowTitle("Adaptive Resume Generator")
        except Exception:
            self.setWindowTitle("Adaptive Resume Generator")

    # ------------------------------------------------------------------
    # Dialog helpers
    # ------------------------------------------------------------------
    # Removed _add_profile() - single-profile mode doesn't allow creating new profiles

    def _edit_profile(self) -> None:
        """Edit the current profile."""
        profile = self.profile_service.get_default_profile()
        if not profile:
            QMessageBox.warning(self, "Error", "Unable to load profile.")
            return
        dialog = ProfileDialog(
            self,
            profile={
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "email": profile.email,
                "phone": profile.phone or "",
                "city": profile.city or "",
                "state": profile.state or "",
                "linkedin_url": profile.linkedin_url or "",
                "portfolio_url": profile.portfolio_url or "",
                "professional_summary": profile.professional_summary or "",
            },
        )
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()
            try:
                self.profile_service.update_profile(
                    profile_id=DEFAULT_PROFILE_ID,
                    first_name=data.first_name,
                    last_name=data.last_name,
                    email=data.email,
                    phone=data.phone or None,
                    city=data.city or None,
                    state=data.state or None,
                    linkedin_url=data.linkedin_url or None,
                    portfolio_url=data.portfolio_url or None,
                    professional_summary=data.professional_summary or None,
                )
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", str(exc))
                return

            self._update_window_title()
            self._refresh_current_screen()
            self.statusBar().showMessage("Profile updated successfully", 3000)

    def _import_resume(self) -> None:
        """Import resume to create or update a profile."""
        # Check if AI is enabled in settings
        use_ai = self.settings.ai_enabled if hasattr(self.settings, 'ai_enabled') else False

        # Step 1: Open the import dialog to select and extract resume
        import_dialog = ResumeImportDialog(parent=self, use_ai=use_ai)
        if import_dialog.exec() != int(QDialog.DialogCode.Accepted):
            return  # User cancelled

        # Step 2: Get the extracted resume data
        extracted_resume = import_dialog.get_extracted_resume()
        if not extracted_resume:
            QMessageBox.warning(self, "Import Failed", "No resume data was extracted.")
            return

        # Step 3: Open preview dialog to review and import the data
        preview_dialog = ResumePreviewDialog(
            extracted_resume=extracted_resume,
            profile_id=1,  # Default profile ID for desktop app
            parent=self
        )
        if preview_dialog.exec() == int(QDialog.DialogCode.Accepted):
            # After successful import, refresh all screens
            self._update_window_title()
            self._refresh_current_screen()
            self.statusBar().showMessage("Resume imported successfully!", 3000)
            # Navigate to profile screen to show the results
            self._navigate_to("profile")

    def _add_job(self) -> None:
        """Add a new job."""
        dialog = JobDialog(self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()
            try:
                job = self.job_service.create_job(
                    company_name=data.company_name,
                    job_title=data.job_title,
                    start_date=data.start_date,
                    end_date=data.end_date,
                    is_current=data.is_current,
                    location=data.location or None,
                    description=data.description or None,
                    display_order=0,
                )
                self._sync_bullets(job.id, data.bullets)
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", str(exc))
                return

            # Navigate to companies screen and refresh
            self._navigate_to("companies")
            self.companies_screen.on_screen_shown()
            self.statusBar().showMessage("Job created successfully", 3000)

    def _edit_job(self) -> None:
        """Edit the selected job."""
        # Get current job from companies screen
        jobs_view = self.companies_screen.get_jobs_view()
        job_id = jobs_view.current_job_id()
        if job_id is None:
            QMessageBox.information(self, "No Job Selected", "Please select a job to edit.")
            return

        job = self.job_service.get_job_by_id(job_id)
        bullets = self.job_service.get_bullet_points_for_job(job_id)
        dialog = JobDialog(
            self,
            job={
                "company_name": job.company_name,
                "job_title": job.job_title,
                "location": job.location or "",
                "start_date": job.start_date,
                "end_date": job.end_date,
                "description": job.description or "",
                "bullets": [bullet.content for bullet in bullets],
            },
        )
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()
            try:
                self.job_service.update_job(
                    job_id=job_id,
                    company_name=data.company_name,
                    job_title=data.job_title,
                    location=data.location or None,
                    start_date=data.start_date,
                    end_date=data.end_date,
                    is_current=data.is_current,
                    description=data.description or None,
                )
                self._sync_bullets(job_id, data.bullets)
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", str(exc))
                return

            self.companies_screen.on_screen_shown()
            self._on_job_selected(job_id)
            self.statusBar().showMessage("Job updated successfully", 3000)

    def _delete_job(self) -> None:
        """Delete the selected job/role."""
        # Get current job from companies screen
        jobs_view = self.companies_screen.get_jobs_view()
        job_id = jobs_view.current_job_id()
        if job_id is None:
            QMessageBox.information(self, "No Role Selected", "Please select a role to delete.")
            return

        # Get job details for confirmation
        job = self.job_service.get_job_by_id(job_id)

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the role '{job.job_title}' at '{job.company_name}'?\n\n"
            f"This will also delete all associated accomplishments.\n\n"
            f"You can restore deleted items within 30 days using the 'Recently Deleted' button.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.job_service.delete_job(job_id)
                self.companies_screen.on_screen_shown()
                self.statusBar().showMessage("Role deleted successfully", 3000)
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", f"Failed to delete role: {str(exc)}")

    def _view_recently_deleted(self) -> None:
        """Open the recently deleted items dialog."""
        dialog = RecentlyDeletedDialog(self.job_service, DEFAULT_PROFILE_ID, self)
        dialog.exec()

        # Refresh the companies screen in case items were restored
        self.companies_screen.on_screen_shown()

    def _edit_company(self) -> None:
        """Edit a company's information."""
        # Get selected company from companies screen
        if not hasattr(self.companies_screen, 'selected_company') or not self.companies_screen.selected_company:
            QMessageBox.information(self, "No Company Selected", "Please select a company to edit.")
            return

        company_name = self.companies_screen.selected_company

        # Get the first job for this company to get location info
        jobs_for_company = [
            job for job in self.companies_screen.all_jobs
            if job.company_name == company_name
        ]

        if not jobs_for_company:
            QMessageBox.warning(self, "Error", "No jobs found for this company.")
            return

        current_location = jobs_for_company[0].location or ""

        dialog = CompanyDialog(
            self,
            company_name=company_name,
            company_location=current_location,
        )

        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()

            # Update all jobs for this company with new name and location
            try:
                for job in jobs_for_company:
                    self.job_service.update_job(
                        job_id=job.id,
                        company_name=data.name,
                        location=data.location or None,
                    )

                self.companies_screen.on_screen_shown()
                self.statusBar().showMessage(f"Company '{data.name}' updated successfully", 3000)
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to update company: {str(exc)}")

    def _delete_company(self) -> None:
        """Delete a company and all its associated jobs."""
        # Get selected company from companies screen
        if not hasattr(self.companies_screen, 'selected_company') or not self.companies_screen.selected_company:
            QMessageBox.information(self, "No Company Selected", "Please select a company to delete.")
            return

        company_name = self.companies_screen.selected_company

        # Get all jobs for this company
        jobs_for_company = [
            job for job in self.companies_screen.all_jobs
            if job.company_name == company_name
        ]

        if not jobs_for_company:
            QMessageBox.warning(self, "Error", "No jobs found for this company.")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete company '{company_name}' and all {len(jobs_for_company)} associated role(s)?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                for job in jobs_for_company:
                    # Delete all bullets for this job first
                    bullets = self.job_service.get_bullet_points_for_job(job.id)
                    for bullet in bullets:
                        self.job_service.delete_bullet_point(bullet.id)

                    # Delete the job
                    self.job_service.delete_job(job.id)

                self.companies_screen.on_screen_shown()
                self.statusBar().showMessage(f"Company '{company_name}' and all roles deleted", 3000)
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to delete company: {str(exc)}")

    def _add_education(self) -> None:
        """Add a new education entry."""
        dialog = EducationDialog(self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()
            try:
                self.education_service.create_education(
                    institution=data.institution,
                    degree=data.degree,
                    field_of_study=data.field_of_study,
                    start_date=data.start_date,
                    end_date=data.end_date,
                    gpa=data.gpa,
                    honors=data.honors,
                    relevant_coursework=data.relevant_coursework,
                    display_order=0,
                )
                self.education_screen.on_screen_shown()
                self.statusBar().showMessage("Education added successfully", 3000)
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", str(exc))

    def _edit_education(self) -> None:
        """Edit the selected education entry."""
        education_id = self.education_screen.get_selected_education_id()
        if education_id is None:
            QMessageBox.information(self, "No Education Selected", "Please select an education entry to edit.")
            return

        education = self.education_service.get_education_by_id(education_id)
        dialog = EducationDialog(
            self,
            education={
                "institution": education.institution,
                "degree": education.degree,
                "field_of_study": education.field_of_study or "",
                "start_date": education.start_date,
                "end_date": education.end_date,
                "gpa": education.gpa,
                "honors": education.honors or "",
                "relevant_coursework": education.relevant_coursework or "",
            },
        )
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()
            try:
                self.education_service.update_education(
                    education_id=education_id,
                    institution=data.institution,
                    degree=data.degree,
                    field_of_study=data.field_of_study,
                    start_date=data.start_date,
                    end_date=data.end_date,
                    gpa=data.gpa,
                    honors=data.honors,
                    relevant_coursework=data.relevant_coursework,
                )
                self.education_screen.on_screen_shown()
                self.statusBar().showMessage("Education updated successfully", 3000)
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", str(exc))

    def _delete_education(self) -> None:
        """Delete the selected education entry."""
        education_id = self.education_screen.get_selected_education_id()
        if education_id is None:
            QMessageBox.information(self, "No Education Selected", "Please select an education entry to delete.")
            return

        education = self.education_service.get_education_by_id(education_id)

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{education.degree}' from '{education.institution}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.education_service.delete_education(education_id)
                self.education_screen.on_screen_shown()
                self.statusBar().showMessage("Education deleted successfully", 3000)
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", f"Failed to delete education: {str(exc)}")

    def _add_skill(self) -> None:
        """Add a new skill."""
        dialog = SkillDialog(self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()
            try:
                self.skill_service.create_skill(
                    skill_name=data.skill_name,
                    category=data.category,
                    proficiency_level=data.proficiency_level,
                    years_experience=data.years_experience,
                    display_order=0,
                )
                self.skills_screen.on_screen_shown()
                self.statusBar().showMessage("Skill added successfully", 3000)
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", str(exc))

    def _edit_skill(self) -> None:
        """Edit the selected skill."""
        skill_id = self.skills_screen.get_selected_skill_id()
        if skill_id is None:
            QMessageBox.information(self, "No Skill Selected", "Please select a skill to edit.")
            return

        skill = self.skill_service.get_skill_by_id(skill_id)
        dialog = SkillDialog(
            self,
            skill={
                "skill_name": skill.skill_name,
                "category": skill.category or "",
                "proficiency_level": skill.proficiency_level or "",
                "years_experience": skill.years_experience,
            },
        )
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()
            try:
                self.skill_service.update_skill(
                    skill_id=skill_id,
                    skill_name=data.skill_name,
                    category=data.category,
                    proficiency_level=data.proficiency_level,
                    years_experience=data.years_experience,
                )
                self.skills_screen.on_screen_shown()
                self.statusBar().showMessage("Skill updated successfully", 3000)
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", str(exc))

    def _delete_skill(self) -> None:
        """Delete the selected skill."""
        skill_id = self.skills_screen.get_selected_skill_id()
        if skill_id is None:
            QMessageBox.information(self, "No Skill Selected", "Please select a skill to delete.")
            return

        skill = self.skill_service.get_skill_by_id(skill_id)

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the skill '{skill.skill_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.skill_service.delete_skill(skill_id)
                self.skills_screen.on_screen_shown()
                self.statusBar().showMessage("Skill deleted successfully", 3000)
            except Exception as exc:  # pragma: no cover
                QMessageBox.critical(self, "Error", f"Failed to delete skill: {str(exc)}")

    def _sync_bullets(self, job_id: int, bullets: list[str]) -> None:
        """Sync bullet points for a job."""
        existing = self.job_service.get_bullet_points_for_job(job_id)
        for bullet in existing:
            self.job_service.delete_bullet_point(bullet.id)

        for order, content in enumerate(bullets, start=1):
            if len(content.strip()) < 10:
                continue
            self.job_service.create_bullet_point(
                job_id=job_id,
                content=content.strip(),
                display_order=order,
            )

    def _open_settings(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def _generate_pdf_resume(self) -> None:
        """Open PDF preview dialog for current tailored resume."""
        if not self.current_tailored_resume_id:
            QMessageBox.warning(
                self,
                "No Resume Ready",
                "Please analyze a job posting first to generate a tailored resume."
            )
            return

        try:
            dialog = ResumePDFPreviewDialog(
                tailored_resume_id=self.current_tailored_resume_id,
                parent=self
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self,
                "PDF Generation Error",
                f"An error occurred while opening the PDF preview:\n\n{str(e)}"
            )

    def _on_enhance_bullet(self, bullet_id: int) -> None:
        """Open bullet enhancement dialog."""
        # Get the bullet point
        bullet = None
        for bp in self.job_service.session.query(BulletPoint).filter_by(id=bullet_id).all():
            bullet = bp
            break

        if bullet is None:
            QMessageBox.warning(self, "Error", "Could not find bullet point.")
            return

        # Open enhancement dialog
        dialog = BulletEnhancementDialog(bullet.content, self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            enhanced_text = dialog.get_enhanced_text()
            if enhanced_text:
                # Update the bullet
                bullet.content = enhanced_text
                self.job_service.session.commit()

                # Refresh the display
                job_id = bullet.job_id
                self._on_job_selected(job_id)
                self.statusBar().showMessage("Bullet enhanced successfully", 3000)

    def _on_job_selected(self, job_id: int) -> None:
        """Handle job selection."""
        if job_id <= 0:
            return

        jobs_view = self.companies_screen.get_jobs_view()
        job = self.job_service.get_job_by_id(job_id)
        bullets = self.job_service.get_bullet_points_for_job(job_id)
        jobs_view.show_job_details(job, bullets)

    def _on_application_selected(self, application_id: int) -> None:
        """Handle application selection.

        Note: The ApplicationsScreen handles opening the detail dialog internally,
        so this handler is primarily for future use (e.g., cross-screen navigation).
        """
        # Currently, ApplicationsScreen handles detail view internally
        # This is a placeholder for future functionality
        pass


__all__ = ["MainWindow"]
