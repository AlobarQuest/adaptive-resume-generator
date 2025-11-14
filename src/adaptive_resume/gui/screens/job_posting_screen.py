"""Job posting upload screen (Phase 4 placeholder)."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QComboBox,
        QHBoxLayout,
        QScrollArea,
    )
    from PyQt6.QtCore import Qt
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from adaptive_resume.models import Profile


class JobPostingScreen(BaseScreen):
    """Screen for uploading and analyzing job postings."""

    def __init__(
        self,
        profile_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.profile_service = profile_service
        self.current_profile_id: Optional[int] = None
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the job posting screen UI."""
        # Main layout for the screen
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header = QLabel("Upload Job Posting")
        header.setObjectName("screenTitle")
        layout.addWidget(header)

        # Description
        description = QLabel(
            "Upload a job posting to automatically match your experience and generate a tailored resume."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #ccc; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(description)

        # Profile selector
        profile_section = QFrame()
        profile_section.setObjectName("settingsCard")
        profile_layout = QVBoxLayout(profile_section)

        profile_label = QLabel("Select Profile:")
        profile_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        profile_layout.addWidget(profile_label)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumHeight(40)
        profile_layout.addWidget(self.profile_combo)

        layout.addWidget(profile_section)

        # Upload area
        upload_frame = QFrame()
        upload_frame.setObjectName("uploadFrame")
        upload_frame.setMinimumHeight(250)

        upload_layout = QVBoxLayout(upload_frame)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.setSpacing(15)

        upload_icon = QLabel("📄")
        upload_icon.setStyleSheet("font-size: 48px;")
        upload_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(upload_icon)

        upload_title = QLabel("Upload Job Posting")
        upload_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        upload_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(upload_title)

        upload_text = QLabel("Drag & Drop your file here\nor")
        upload_text.setStyleSheet("color: #999; font-size: 14px;")
        upload_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(upload_text)

        # Buttons in horizontal layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        browse_btn = QPushButton("📁 Browse Files")
        browse_btn.setEnabled(False)
        browse_btn.setMinimumHeight(40)
        browse_btn.setStyleSheet("padding: 10px 20px;")
        button_layout.addWidget(browse_btn)

        paste_btn = QPushButton("📋 Paste Text")
        paste_btn.setEnabled(False)
        paste_btn.setMinimumHeight(40)
        paste_btn.setStyleSheet("padding: 10px 20px;")
        button_layout.addWidget(paste_btn)

        upload_layout.addLayout(button_layout)

        supported_label = QLabel("Supported formats: .txt, .pdf, .docx, or plain text")
        supported_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        supported_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        upload_layout.addWidget(supported_label)

        layout.addWidget(upload_frame)

        # Process button
        process_btn = QPushButton("🚀 Analyze & Generate Tailored Resume")
        process_btn.setObjectName("primaryButton")
        process_btn.setMinimumHeight(50)
        process_btn.setEnabled(False)
        process_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(process_btn)

        # Coming soon message
        coming_soon_frame = QFrame()
        coming_soon_frame.setStyleSheet(
            "background-color: #2a3f5f; "
            "border: 2px solid #4a90e2; "
            "border-radius: 8px; "
            "padding: 20px;"
        )
        coming_soon_layout = QVBoxLayout(coming_soon_frame)

        coming_soon_icon = QLabel("🚧")
        coming_soon_icon.setStyleSheet("font-size: 24px;")
        coming_soon_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon_layout.addWidget(coming_soon_icon)

        coming_soon_title = QLabel("Coming in Phase 4")
        coming_soon_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a90e2;")
        coming_soon_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon_layout.addWidget(coming_soon_title)

        coming_soon_text = QLabel(
            "This feature will use AI to analyze job postings and automatically:\n"
            "• Extract required skills and qualifications\n"
            "• Match them with your experience\n"
            "• Generate a tailored resume highlighting relevant accomplishments\n"
            "• Suggest skills to emphasize or add"
        )
        coming_soon_text.setWordWrap(True)
        coming_soon_text.setStyleSheet("color: #ccc; font-size: 12px;")
        coming_soon_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon_layout.addWidget(coming_soon_text)

        layout.addWidget(coming_soon_frame)

        layout.addStretch()

        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)

        # Add scroll area to main layout
        main_layout.addWidget(scroll)

    def set_profile(self, profile_id: int) -> None:
        """Set the current profile."""
        self.current_profile_id = profile_id
        self._update_profile_combo()

    def _update_profile_combo(self) -> None:
        """Update the profile dropdown with all available profiles."""
        if not self.profile_service:
            return

        self.profile_combo.clear()

        # Load all profiles
        profiles = (
            self.profile_service.session.query(Profile)
            .order_by(Profile.last_name.asc(), Profile.first_name.asc())
            .all()
        )

        if not profiles:
            self.profile_combo.addItem("No profiles available")
            return

        # Add each profile
        for profile in profiles:
            display_name = f"{profile.first_name} {profile.last_name}"
            self.profile_combo.addItem(display_name, profile.id)

        # Select current profile if set
        if self.current_profile_id:
            for i in range(self.profile_combo.count()):
                if self.profile_combo.itemData(i) == self.current_profile_id:
                    self.profile_combo.setCurrentIndex(i)
                    break

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        self._update_profile_combo()


__all__ = ["JobPostingScreen"]
