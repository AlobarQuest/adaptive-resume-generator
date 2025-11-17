"""Profile management screen - Single profile mode."""

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
    from PyQt6.QtCore import pyqtSignal
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.models.base import DEFAULT_PROFILE_ID
from .base_screen import BaseScreen


class ProfileManagementScreen(BaseScreen):
    """Screen for viewing and managing the user profile (single-profile mode)."""

    # Signals
    edit_profile_requested = pyqtSignal()
    import_resume_requested = pyqtSignal()

    def __init__(
        self,
        profile_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.profile_service = profile_service
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the profile management screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header with action buttons
        header_layout = QHBoxLayout()

        header = QLabel("Profile")
        header.setObjectName("screenTitle")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # Import resume button
        import_resume_btn = QPushButton("📄 Import/Update from Resume")
        import_resume_btn.setToolTip("Import or update your profile from an existing resume")
        import_resume_btn.clicked.connect(self.import_resume_requested.emit)
        header_layout.addWidget(import_resume_btn)

        # Edit profile button
        edit_profile_btn = QPushButton("✏️ Edit Profile")
        edit_profile_btn.setObjectName("primaryButton")
        edit_profile_btn.clicked.connect(self.edit_profile_requested.emit)
        header_layout.addWidget(edit_profile_btn)

        layout.addLayout(header_layout)

        # Profile info display
        info_frame = QFrame()
        info_frame.setObjectName("panelFrame")
        info_layout = QVBoxLayout(info_frame)

        info_title = QLabel("Profile Information")
        info_title.setObjectName("panelTitle")
        info_layout.addWidget(info_title)

        # Grid layout for profile details
        details_layout = QGridLayout()
        details_layout.setColumnStretch(1, 1)
        details_layout.setHorizontalSpacing(15)
        details_layout.setVerticalSpacing(10)

        # Create labels for all profile fields
        self.name_value = QLabel("")
        self.name_value.setWordWrap(True)

        self.email_value = QLabel("")
        self.email_value.setWordWrap(True)

        self.phone_value = QLabel("")
        self.phone_value.setWordWrap(True)

        self.location_value = QLabel("")
        self.location_value.setWordWrap(True)

        self.linkedin_value = QLabel("")
        self.linkedin_value.setWordWrap(True)
        self.linkedin_value.setOpenExternalLinks(True)

        self.portfolio_value = QLabel("")
        self.portfolio_value.setWordWrap(True)
        self.portfolio_value.setOpenExternalLinks(True)

        self.summary_value = QLabel("")
        self.summary_value.setWordWrap(True)

        # Add to grid
        row = 0
        details_layout.addWidget(QLabel("<b>Name:</b>"), row, 0)
        details_layout.addWidget(self.name_value, row, 1)

        row += 1
        details_layout.addWidget(QLabel("<b>Email:</b>"), row, 0)
        details_layout.addWidget(self.email_value, row, 1)

        row += 1
        details_layout.addWidget(QLabel("<b>Phone:</b>"), row, 0)
        details_layout.addWidget(self.phone_value, row, 1)

        row += 1
        details_layout.addWidget(QLabel("<b>Location:</b>"), row, 0)
        details_layout.addWidget(self.location_value, row, 1)

        row += 1
        details_layout.addWidget(QLabel("<b>LinkedIn:</b>"), row, 0)
        details_layout.addWidget(self.linkedin_value, row, 1)

        row += 1
        details_layout.addWidget(QLabel("<b>Portfolio:</b>"), row, 0)
        details_layout.addWidget(self.portfolio_value, row, 1)

        row += 1
        details_layout.addWidget(QLabel("<b>Professional Summary:</b>"), row, 0)
        details_layout.addWidget(self.summary_value, row, 1)

        info_layout.addLayout(details_layout)
        layout.addWidget(info_frame)

        layout.addStretch()

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        self._load_profile_data()

    def _load_profile_data(self) -> None:
        """Load and display the default profile data."""
        if not self.profile_service:
            self.name_value.setText("Profile service not available")
            return

        profile = self.profile_service.get_default_profile()
        if not profile:
            self.name_value.setText("No profile found")
            self.email_value.setText("Please create a profile")
            self.phone_value.setText("-")
            self.location_value.setText("-")
            self.linkedin_value.setText("-")
            self.portfolio_value.setText("-")
            self.summary_value.setText("-")
            return

        # Update all fields
        self.name_value.setText(f"{profile.first_name} {profile.last_name}")
        self.email_value.setText(profile.email or "-")
        self.phone_value.setText(profile.phone or "-")

        # Location
        if profile.city and profile.state:
            self.location_value.setText(f"{profile.city}, {profile.state}")
        elif profile.city:
            self.location_value.setText(profile.city)
        elif profile.state:
            self.location_value.setText(profile.state)
        else:
            self.location_value.setText("-")

        # LinkedIn URL with clickable link
        if profile.linkedin_url:
            self.linkedin_value.setText(f'<a href="{profile.linkedin_url}">{profile.linkedin_url}</a>')
        else:
            self.linkedin_value.setText("-")

        # Portfolio URL with clickable link
        if profile.portfolio_url:
            self.portfolio_value.setText(f'<a href="{profile.portfolio_url}">{profile.portfolio_url}</a>')
        else:
            self.portfolio_value.setText("-")

        # Professional summary
        if profile.professional_summary:
            self.summary_value.setText(profile.professional_summary)
        else:
            self.summary_value.setText("-")


__all__ = ["ProfileManagementScreen"]
