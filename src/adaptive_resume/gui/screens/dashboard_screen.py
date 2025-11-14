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


class DashboardScreen(BaseScreen):
    """Dashboard screen showing overview and quick actions."""

    # Signals
    navigate_to_upload = pyqtSignal()
    navigate_to_companies = pyqtSignal()
    navigate_to_general = pyqtSignal()

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
        self.current_profile_id: Optional[int] = None
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

        upload_btn = QPushButton("📄 Upload Job Posting")
        upload_btn.setObjectName("primaryButton")
        upload_btn.setMinimumHeight(50)
        upload_btn.clicked.connect(self.navigate_to_upload.emit)
        hero_layout.addWidget(upload_btn, 0, Qt.AlignmentFlag.AlignCenter)

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

        # Bottom section - two panels
        bottom_layout = QHBoxLayout()

        # Quick manage companies/roles panel
        quick_manage_frame = QFrame()
        quick_manage_frame.setObjectName("panelFrame")
        quick_manage_layout = QVBoxLayout(quick_manage_frame)

        quick_title = QLabel("Quick Manage")
        quick_title.setObjectName("panelTitle")
        quick_manage_layout.addWidget(quick_title)

        self.recent_jobs_label = QLabel("Recent jobs will appear here")
        self.recent_jobs_label.setWordWrap(True)
        quick_manage_layout.addWidget(self.recent_jobs_label)

        quick_manage_layout.addStretch()

        manage_btn = QPushButton("Manage Companies & Roles")
        manage_btn.clicked.connect(self.navigate_to_companies.emit)
        quick_manage_layout.addWidget(manage_btn)

        bottom_layout.addWidget(quick_manage_frame)

        # Profile info panel
        profile_frame = QFrame()
        profile_frame.setObjectName("panelFrame")
        profile_layout = QVBoxLayout(profile_frame)

        profile_title = QLabel("Profile Info")
        profile_title.setObjectName("panelTitle")
        profile_layout.addWidget(profile_title)

        self.profile_info_label = QLabel("Select a profile to view info")
        self.profile_info_label.setWordWrap(True)
        profile_layout.addWidget(self.profile_info_label)

        profile_layout.addStretch()

        profile_btn = QPushButton("Update General Info")
        profile_btn.clicked.connect(self.navigate_to_general.emit)
        profile_layout.addWidget(profile_btn)

        bottom_layout.addWidget(profile_frame)

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

    def set_profile(self, profile_id: int) -> None:
        """Set the current profile and update stats."""
        self.current_profile_id = profile_id
        self._update_stats()
        self._update_profile_info()
        self._update_recent_jobs()

    def _update_stats(self) -> None:
        """Update the statistics display."""
        if not self.current_profile_id or not self.job_service:
            return

        # Get counts from services
        jobs = self.job_service.get_jobs_for_profile(self.current_profile_id)

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
            skills = self.skill_service.list_skills_for_profile(self.current_profile_id)
            self.stat_widgets["skills"].value_label.setText(str(len(skills)))

        # Get education count if service available
        if self.education_service:
            education = self.education_service.list_education_for_profile(self.current_profile_id)
            self.stat_widgets["education"].value_label.setText(str(len(education)))

    def _update_profile_info(self) -> None:
        """Update the profile info panel."""
        if not self.current_profile_id or not self.profile_service:
            return

        profile = self.profile_service.get_profile_by_id(self.current_profile_id)
        if profile:
            info_text = f"<b>{profile.first_name} {profile.last_name}</b><br>"
            info_text += f"{profile.email}<br>"
            if profile.phone:
                info_text += f"{profile.phone}<br>"
            if profile.city and profile.state:
                info_text += f"{profile.city}, {profile.state}"

            self.profile_info_label.setText(info_text)

    def _update_recent_jobs(self) -> None:
        """Update the recent jobs display."""
        if not self.current_profile_id or not self.job_service:
            return

        jobs = self.job_service.get_jobs_for_profile(self.current_profile_id)

        if not jobs:
            self.recent_jobs_label.setText("No jobs added yet. Add your first job!")
            return

        # Show most recent 3 jobs
        recent_jobs = sorted(jobs, key=lambda j: j.start_date, reverse=True)[:3]

        jobs_text = "<b>Recent Jobs:</b><br><br>"
        for job in recent_jobs:
            jobs_text += f"• {job.job_title} at {job.company_name}<br>"

        self.recent_jobs_label.setText(jobs_text)

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        if self.current_profile_id:
            self._update_stats()
            self._update_profile_info()
            self._update_recent_jobs()


__all__ = ["DashboardScreen"]
