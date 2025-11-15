"""Primary PyQt6 window for the Adaptive Resume Generator."""

from __future__ import annotations

__all__ = ["MainWindow"]

from typing import Optional

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
        self.current_profile_id: Optional[int] = None
        self.current_tailored_resume_id: Optional[int] = None

        self.setWindowTitle("Adaptive Resume Generator")
        self.resize(1200, 720)

        self._setup_ui()
        self._load_initial_profile()

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

        self.profile_screen = ProfileManagementScreen(
            profile_service=self.profile_service,
        )
        self.profile_screen.select_profile_requested.connect(self._set_current_profile)
        self.profile_screen.add_profile_requested.connect(self._add_profile)
        self.profile_screen.edit_profile_requested.connect(self._edit_profile)

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

        self.skills_screen = SkillsScreen(
            skill_service=self.skill_service,
        )

        self.upload_screen = JobPostingScreen(
            profile_service=self.profile_service,
            job_service=self.job_service,
        )
        self.upload_screen.tailored_resume_ready.connect(self._on_tailored_resume_ready)

        self.results_screen = TailoringResultsScreen()
        self.results_screen.generate_pdf_requested.connect(self._generate_pdf_resume)
        self.results_screen.start_over_requested.connect(lambda: self._navigate_to("upload"))

        self.review_screen = ReviewPrintScreen()

        # Add screens to stacked widget
        self.screens = {
            "dashboard": self.dashboard_screen,
            "profile": self.profile_screen,
            "companies": self.companies_screen,
            "general": self.general_screen,
            "education": self.education_screen,
            "skills": self.skills_screen,
            "upload": self.upload_screen,
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
        self.current_tailored_resume_id = tailored_resume.id
        self.results_screen.display_results(tailored_resume)
        self._navigate_to("results")

    def _refresh_current_screen(self) -> None:
        """Refresh the current screen."""
        current_screen = self.stacked_widget.currentWidget()
        if hasattr(current_screen, 'on_screen_shown'):
            current_screen.on_screen_shown()

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------
    def _load_initial_profile(self) -> None:
        """Load the first available profile or create one."""
        profiles = (
            self.profile_service.session.query(Profile)
            .order_by(Profile.last_name.asc(), Profile.first_name.asc())
            .all()
        )

        if profiles:
            self._set_current_profile(profiles[0].id)
        else:
            self.current_profile_id = None
            self._update_window_title()

    def _show_profile_selector(self) -> None:
        """Show profile selector dialog."""
        # Create a simple profile selector dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Profile")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(300)

        layout = QVBoxLayout(dialog)

        # Profile list
        profile_list = QListWidget()
        profiles = (
            self.profile_service.session.query(Profile)
            .order_by(Profile.last_name.asc(), Profile.first_name.asc())
            .all()
        )

        for profile in profiles:
            label = f"{profile.first_name} {profile.last_name}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            profile_list.addItem(item)

            if profile.id == self.current_profile_id:
                profile_list.setCurrentItem(item)

        layout.addWidget(profile_list)

        # Buttons
        button_layout = QHBoxLayout()

        select_btn = QPushButton("Select")
        select_btn.setDefault(True)
        select_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(select_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_item = profile_list.currentItem()
            if current_item:
                profile_id = int(current_item.data(Qt.ItemDataRole.UserRole))
                self._set_current_profile(profile_id)

    def _set_current_profile(self, profile_id: int) -> None:
        """Set the current profile and update all screens."""
        self.current_profile_id = profile_id
        self._update_window_title()

        # Update all screens with the new profile
        for screen in self.screens.values():
            if hasattr(screen, 'set_profile'):
                screen.set_profile(profile_id)

        # Refresh current screen
        self._refresh_current_screen()

        self.statusBar().showMessage(f"Loaded profile #{profile_id}", 3000)

    def _update_window_title(self) -> None:
        """Update window title with current profile name."""
        if self.current_profile_id:
            profile = self.profile_service.get_profile_by_id(self.current_profile_id)
            if profile:
                self.setWindowTitle(
                    f"Adaptive Resume Generator - {profile.first_name} {profile.last_name}"
                )
        else:
            self.setWindowTitle("Adaptive Resume Generator")

    # ------------------------------------------------------------------
    # Dialog helpers
    # ------------------------------------------------------------------
    def _add_profile(self) -> None:
        """Add a new profile."""
        dialog = ProfileDialog(self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()
            try:
                profile = self.profile_service.create_profile(
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

            self._set_current_profile(profile.id)
            self.statusBar().showMessage("Profile created successfully", 3000)

    def _edit_profile(self) -> None:
        """Edit the current profile."""
        profile_id = self.current_profile_id
        if profile_id is None:
            QMessageBox.information(self, "No Profile", "Please select a profile first.")
            return

        profile = self.profile_service.get_profile_by_id(profile_id)
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
                    profile_id=profile_id,
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

    def _add_job(self) -> None:
        """Add a new job."""
        if self.current_profile_id is None:
            QMessageBox.information(self, "Select Profile", "Please choose a profile first.")
            return

        dialog = JobDialog(self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            data = dialog.get_result()
            try:
                job = self.job_service.create_job(
                    profile_id=self.current_profile_id,
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
        profile_id = self.current_profile_id
        if profile_id is None:
            QMessageBox.information(self, "Select Profile", "Please choose a profile first.")
            return

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


__all__ = ["MainWindow"]
