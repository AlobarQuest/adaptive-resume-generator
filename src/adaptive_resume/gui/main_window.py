"""Primary PyQt6 window for the Adaptive Resume Generator."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QAction,
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
    )
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.models import Profile
from adaptive_resume.services.job_service import JobService
from adaptive_resume.services.profile_service import ProfileService
from adaptive_resume.services.skill_service import SkillService
from adaptive_resume.services.education_service import EducationService
from adaptive_resume.services.certification_service import CertificationService

from .dialogs import JobDialog, ProfileDialog
from .views import JobsView, SkillsSummaryView, ApplicationsView
from .widgets import SkillsPanel, EducationPanel


class MainWindow(QMainWindow):
    """Top-level window coordinating navigation between resume editors."""

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

        self.setWindowTitle("Adaptive Resume Generator")
        self.resize(1200, 720)

        self._setup_ui()
        self._load_profiles()

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        central = QWidget(self)
        layout = QHBoxLayout(central)

        self.profile_list = QListWidget()
        self.profile_list.currentItemChanged.connect(self._on_profile_selected)

        left_panel = QVBoxLayout()
        left_panel.addWidget(self.profile_list)

        profile_buttons = QHBoxLayout()
        self.add_profile_button = QPushButton("Add Profile")
        self.edit_profile_button = QPushButton("Edit Profile")
        self.add_profile_button.clicked.connect(self._add_profile)
        self.edit_profile_button.clicked.connect(self._edit_profile)
        profile_buttons.addWidget(self.add_profile_button)
        profile_buttons.addWidget(self.edit_profile_button)
        left_panel.addLayout(profile_buttons)

        layout.addLayout(left_panel, 1)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)

        self.jobs_view = JobsView()
        self.jobs_view.job_selected.connect(self._on_job_selected)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.addWidget(self.jobs_view)

        details_splitter = QSplitter()
        details_splitter.setOrientation(Qt.Orientation.Horizontal)

        self.skills_panel = SkillsPanel(self.skill_service)
        self.education_panel = EducationPanel(self.education_service)
        self.skills_summary_view = SkillsSummaryView()
        self.applications_view = ApplicationsView()

        details_splitter.addWidget(self.skills_panel)
        details_splitter.addWidget(self.education_panel)
        details_splitter.addWidget(self.skills_summary_view)

        right_layout.addWidget(details_splitter)
        right_layout.addWidget(self.applications_view)

        splitter.addWidget(self.jobs_view)
        splitter.addWidget(right_container)

        layout.addWidget(splitter, 3)

        central.setLayout(layout)
        self.setCentralWidget(central)

        self._build_toolbars()
        self.setStatusBar(QStatusBar(self))

    def _build_toolbars(self) -> None:
        toolbar = QToolBar("Resume Actions", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        add_job_action = QAction("Add Job", self)
        add_job_action.triggered.connect(self._add_job)
        toolbar.addAction(add_job_action)

        edit_job_action = QAction("Edit Job", self)
        edit_job_action.triggered.connect(self._edit_job)
        toolbar.addAction(edit_job_action)

        toolbar.addSeparator()

        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._refresh_current_profile)
        toolbar.addAction(refresh_action)

    # ------------------------------------------------------------------
    # Data loading helpers
    # ------------------------------------------------------------------
    def _load_profiles(self) -> None:
        self.profile_list.clear()
        profiles = (
            self.profile_service.session.query(Profile)
            .order_by(Profile.last_name.asc(), Profile.first_name.asc())
            .all()
        )
        for profile in profiles:
            label = f"{profile.first_name} {profile.last_name}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            self.profile_list.addItem(item)

        if profiles:
            self.profile_list.setCurrentRow(0)
        else:
            self.current_profile_id = None
            self.jobs_view.set_jobs([])
            self.skills_panel.load_skills(None)
            self.education_panel.load_education(None)
            self.skills_summary_view.set_skills([])

    def _refresh_current_profile(self) -> None:
        if self.current_profile_id is not None:
            self._load_profile_details(self.current_profile_id)

    def _on_profile_selected(self, current: Optional[QListWidgetItem]) -> None:
        if current is None:
            self.current_profile_id = None
            return

        profile_id = int(current.data(Qt.ItemDataRole.UserRole))
        self.current_profile_id = profile_id
        self._load_profile_details(profile_id)
        self.statusBar().showMessage(f"Loaded profile #{profile_id}", 3000)

    def _load_profile_details(self, profile_id: int) -> None:
        jobs = self.job_service.get_jobs_for_profile(profile_id)
        self.jobs_view.set_jobs(jobs)
        self.skills_panel.load_skills(profile_id)
        self.education_panel.load_education(profile_id)

        skills = self.skill_service.list_skills_for_profile(profile_id)
        self.skills_summary_view.set_skills(skills)

    def _on_job_selected(self, job_id: int) -> None:
        if job_id <= 0:
            self.jobs_view.show_job_details(None, [])
            return

        job = self.job_service.get_job_by_id(job_id)
        bullets = self.job_service.get_bullet_points_for_job(job_id)
        self.jobs_view.show_job_details(job, bullets)

    # ------------------------------------------------------------------
    # Dialog helpers
    # ------------------------------------------------------------------
    def _add_profile(self) -> None:
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
            except Exception as exc:  # pragma: no cover - relies on PyQt runtime
                QMessageBox.critical(self, "Error", str(exc))
                return

            self._load_profiles()
            self._select_profile(profile.id)

    def _edit_profile(self) -> None:
        profile_id = self.current_profile_id
        if profile_id is None:
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
            except Exception as exc:  # pragma: no cover - relies on PyQt runtime
                QMessageBox.critical(self, "Error", str(exc))
                return

            self._load_profiles()
            self._select_profile(profile_id)

    def _add_job(self) -> None:
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

            self._load_profile_details(self.current_profile_id)
            self._select_job(job.id)

    def _edit_job(self) -> None:
        profile_id = self.current_profile_id
        job_id = self.jobs_view.current_job_id()
        if profile_id is None or job_id is None:
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

            self._load_profile_details(profile_id)
            self._select_job(job_id)

    def _sync_bullets(self, job_id: int, bullets: list[str]) -> None:
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

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _select_profile(self, profile_id: int) -> None:
        for index in range(self.profile_list.count()):
            item = self.profile_list.item(index)
            if int(item.data(Qt.ItemDataRole.UserRole)) == profile_id:
                self.profile_list.setCurrentRow(index)
                return

    def _select_job(self, job_id: int) -> None:
        for index in range(self.jobs_view.job_list.count()):
            item = self.jobs_view.job_list.item(index)
            if int(item.data(Qt.ItemDataRole.UserRole)) == job_id:
                self.jobs_view.job_list.setCurrentRow(index)
                return


__all__ = ["MainWindow"]
