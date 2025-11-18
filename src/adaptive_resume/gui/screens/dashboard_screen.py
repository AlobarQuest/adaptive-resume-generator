"""Dashboard screen for the Adaptive Resume Generator."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QGridLayout,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from adaptive_resume.models.base import DEFAULT_PROFILE_ID


class DashboardScreen(BaseScreen):
    """Dashboard screen showing overview and quick actions."""

    # Signals
    navigate_to_upload = pyqtSignal()
    navigate_to_companies = pyqtSignal()
    navigate_to_general = pyqtSignal()
    navigate_to_profile_creation = pyqtSignal()
    import_resume_requested = pyqtSignal()

    def __init__(
        self,
        profile_service=None,
        job_service=None,
        skill_service=None,
        education_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.profile_service = profile_service
        self.job_service = job_service
        self.skill_service = skill_service
        self.education_service = education_service
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the dashboard UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Hero section
        hero_frame = QFrame()
        hero_frame.setObjectName("heroFrame")
        hero_frame.setMinimumHeight(200)
        hero_layout = QVBoxLayout(hero_frame)

        hero_label = QLabel("Welcome to Adaptive Resume Generator")
        hero_label.setObjectName("heroTitle")
        hero_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(hero_label)

        # Current profile display
        self.current_profile_label = QLabel("No profile selected")
        self.current_profile_label.setObjectName("currentProfileLabel")
        self.current_profile_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_profile_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #4a90e2; "
            "padding: 10px; margin: 10px 0;"
        )
        hero_layout.addWidget(self.current_profile_label)

        layout.addWidget(hero_frame)

        # Stats panel
        stats_label = QLabel("Profile Stats")
        stats_label.setObjectName("sectionTitle")
        layout.addWidget(stats_label)

        # Use HBoxLayout instead of GridLayout for better scaling
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        # Create stat cards
        self.stat_widgets = {}
        stat_items = [
            ("companies", "Companies", "🏢"),
            ("roles", "Roles", "💼"),
            ("skills", "Skills", "🎯"),
            ("education", "Education", "🎓"),
            ("accomplishments", "Accomplishments", "⭐"),
        ]

        for key, label, icon in stat_items:
            stat_widget = self._create_stat_card(icon, "0", label)
            self.stat_widgets[key] = stat_widget
            stats_layout.addWidget(stat_widget)

        layout.addLayout(stats_layout)

        # Bottom section - Quick action panels
        bottom_layout = QHBoxLayout()

        # Upload Resume panel
        upload_resume_frame = QFrame()
        upload_resume_frame.setObjectName("panelFrame")
        upload_resume_layout = QVBoxLayout(upload_resume_frame)

        upload_resume_title = QLabel("📄 Upload Existing Resume")
        upload_resume_title.setObjectName("panelTitle")
        upload_resume_layout.addWidget(upload_resume_title)

        upload_resume_desc = QLabel(
            "Import your existing resume to automatically populate your profile "
            "with work experience, education, skills, and accomplishments."
        )
        upload_resume_desc.setWordWrap(True)
        upload_resume_desc.setStyleSheet("color: #888; padding: 10px 0;")
        upload_resume_layout.addWidget(upload_resume_desc)

        upload_resume_layout.addStretch()

        upload_resume_btn = QPushButton("📤 Upload Resume")
        upload_resume_btn.setObjectName("primaryButton")
        upload_resume_btn.setMinimumHeight(45)
        upload_resume_btn.clicked.connect(self.import_resume_requested.emit)
        upload_resume_layout.addWidget(upload_resume_btn)

        bottom_layout.addWidget(upload_resume_frame)

        # Add Job Posting panel
        add_job_frame = QFrame()
        add_job_frame.setObjectName("panelFrame")
        add_job_layout = QVBoxLayout(add_job_frame)

        add_job_title = QLabel("💼 Add Job Posting")
        add_job_title.setObjectName("panelTitle")
        add_job_layout.addWidget(add_job_title)

        add_job_desc = QLabel(
            "Upload or paste a job posting to analyze requirements and generate "
            "a tailored resume with your best-matching accomplishments."
        )
        add_job_desc.setWordWrap(True)
        add_job_desc.setStyleSheet("color: #888; padding: 10px 0;")
        add_job_layout.addWidget(add_job_desc)

        add_job_layout.addStretch()

        add_job_btn = QPushButton("➕ Add Job Posting")
        add_job_btn.setObjectName("primaryButton")
        add_job_btn.setMinimumHeight(45)
        add_job_btn.clicked.connect(self.navigate_to_upload.emit)
        add_job_layout.addWidget(add_job_btn)

        bottom_layout.addWidget(add_job_frame)

        layout.addLayout(bottom_layout)
        layout.addStretch()

    def _create_stat_card(self, icon: str, value: str, label: str) -> QWidget:
        """Create a stat card widget."""
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(120)
        card.setMinimumWidth(150)

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(5)

        icon_label = QLabel(icon)
        icon_label.setObjectName("statIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setWordWrap(False)
        card_layout.addWidget(icon_label)

        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setWordWrap(False)
        card_layout.addWidget(value_label)

        label_widget = QLabel(label)
        label_widget.setObjectName("statLabel")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_widget.setWordWrap(True)  # Allow wrapping for long labels
        card_layout.addWidget(label_widget)

        # Store value label for updates
        card.value_label = value_label

        return card



    def _update_stats(self) -> None:
        """Update the statistics display."""
        if not self.job_service:
            return

        # Get counts from services
        jobs = self.job_service.get_jobs_for_profile(DEFAULT_PROFILE_ID)

        # Count unique companies
        companies = set(job.company_name for job in jobs)

        # Count total bullets
        total_bullets = sum(
            len(self.job_service.get_bullet_points_for_job(job.id))
            for job in jobs
        )

        # Update stat cards
        self.stat_widgets["companies"].value_label.setText(str(len(companies)))
        self.stat_widgets["roles"].value_label.setText(str(len(jobs)))
        self.stat_widgets["accomplishments"].value_label.setText(str(total_bullets))

        # Get skills count if service available
        if self.skill_service:
            skills = self.skill_service.list_skills_for_profile(DEFAULT_PROFILE_ID)
            self.stat_widgets["skills"].value_label.setText(str(len(skills)))

        # Get education count if service available
        if self.education_service:
            education = self.education_service.list_education_for_profile(DEFAULT_PROFILE_ID)
            self.stat_widgets["education"].value_label.setText(str(len(education)))

    def _update_profile_info(self) -> None:
        """Update the profile info display."""
        if not self.profile_service:
            self.current_profile_label.setText("No profile selected")
            return

        profile = self.profile_service.get_profile_by_id(DEFAULT_PROFILE_ID)
        if profile:
            # Update hero section current profile label
            profile_name = f"{profile.first_name} {profile.last_name}"
            self.current_profile_label.setText(f"Current Profile: {profile_name}")
        else:
            self.current_profile_label.setText("No profile selected")

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        self._update_stats()
        self._update_profile_info()


__all__ = ["DashboardScreen"]
