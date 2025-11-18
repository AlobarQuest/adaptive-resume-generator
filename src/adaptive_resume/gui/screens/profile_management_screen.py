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
        QTabWidget,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.models.base import DEFAULT_PROFILE_ID
from .base_screen import BaseScreen
from ..widgets import SkillsPanel, EducationPanel


class ProfileManagementScreen(BaseScreen):
    """Screen for viewing and managing the user profile (single-profile mode)."""

    # Signals
    edit_profile_requested = pyqtSignal()
    import_resume_requested = pyqtSignal()
    # Skills signals
    add_skill_requested = pyqtSignal()
    edit_skill_requested = pyqtSignal(int)  # skill_id
    delete_skill_requested = pyqtSignal(int)  # skill_id
    # Education signals
    add_education_requested = pyqtSignal()
    edit_education_requested = pyqtSignal(int)  # education_id
    delete_education_requested = pyqtSignal(int)  # education_id

    def __init__(
        self,
        profile_service=None,
        skill_service=None,
        education_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.profile_service = profile_service
        self.skill_service = skill_service
        self.education_service = education_service
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the profile management screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header with action buttons
        header_layout = QHBoxLayout()

        header = QLabel("Profile Management")
        header.setObjectName("screenTitle")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # Import resume button
        import_resume_btn = QPushButton("📄 Import/Update from Resume")
        import_resume_btn.setToolTip("Import or update your profile from an existing resume")
        import_resume_btn.setMinimumWidth(230)
        import_resume_btn.setMinimumHeight(40)
        import_resume_btn.clicked.connect(self.import_resume_requested.emit)
        header_layout.addWidget(import_resume_btn)

        # Edit profile button
        edit_profile_btn = QPushButton("✏️ Edit Profile")
        edit_profile_btn.setObjectName("primaryButton")
        edit_profile_btn.setMinimumWidth(230)
        edit_profile_btn.setMinimumHeight(40)
        edit_profile_btn.clicked.connect(self.edit_profile_requested.emit)
        header_layout.addWidget(edit_profile_btn)

        layout.addLayout(header_layout)

        # Tabbed interface for Profile, Skills, Education
        self.tabs = QTabWidget()

        # Tab 1: Profile Information
        profile_tab = self._create_profile_tab()
        self.tabs.addTab(profile_tab, "👤 Profile Info")

        # Tab 2: Skills Management
        skills_tab = self._create_skills_tab()
        self.tabs.addTab(skills_tab, "🎯 Skills")

        # Tab 3: Education Management
        education_tab = self._create_education_tab()
        self.tabs.addTab(education_tab, "🎓 Education")

        layout.addWidget(self.tabs)

    def _create_profile_tab(self) -> QWidget:
        """Create the profile information tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

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
        tab_layout.addWidget(info_frame)
        tab_layout.addStretch()

        return tab

    def _create_skills_tab(self) -> QWidget:
        """Create the skills management tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        add_btn = QPushButton("➕ Add Skill")
        add_btn.clicked.connect(self.add_skill_requested.emit)
        actions_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Edit Skill")
        edit_btn.clicked.connect(self._on_edit_skill_clicked)
        actions_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Delete Skill")
        delete_btn.clicked.connect(self._on_delete_skill_clicked)
        actions_layout.addWidget(delete_btn)

        tab_layout.addLayout(actions_layout)

        # Skills panel
        if self.skill_service:
            self.skills_panel = SkillsPanel(self.skill_service)
            # Connect double-click to edit (Issue 3)
            self.skills_panel.skill_list.itemDoubleClicked.connect(self._on_skill_double_clicked)
            tab_layout.addWidget(self.skills_panel)
        else:
            tab_layout.addWidget(QLabel("Skill service not available"))

        return tab

    def _create_education_tab(self) -> QWidget:
        """Create the education management tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        add_btn = QPushButton("➕ Add Education")
        add_btn.clicked.connect(self.add_education_requested.emit)
        actions_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Edit Education")
        edit_btn.clicked.connect(self._on_edit_education_clicked)
        actions_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Delete Education")
        delete_btn.clicked.connect(self._on_delete_education_clicked)
        actions_layout.addWidget(delete_btn)

        tab_layout.addLayout(actions_layout)

        # Education panel
        if self.education_service:
            self.education_panel = EducationPanel(self.education_service)
            # Connect double-click to edit (Issue 3)
            self.education_panel.education_list.itemDoubleClicked.connect(self._on_education_double_clicked)
            tab_layout.addWidget(self.education_panel)
        else:
            tab_layout.addWidget(QLabel("Education service not available"))

        return tab

    def _on_skill_double_clicked(self, item) -> None:
        """Handle double-click on skill item."""
        skill_id = item.data(Qt.ItemDataRole.UserRole)
        if skill_id:
            self.edit_skill_requested.emit(skill_id)

    def _on_education_double_clicked(self, item) -> None:
        """Handle double-click on education item."""
        education_id = item.data(Qt.ItemDataRole.UserRole)
        if education_id:
            self.edit_education_requested.emit(education_id)

    def _on_edit_skill_clicked(self) -> None:
        """Handle edit skill button click."""
        selected_skill_id = self._get_selected_skill_id()
        if selected_skill_id:
            self.edit_skill_requested.emit(selected_skill_id)

    def _on_delete_skill_clicked(self) -> None:
        """Handle delete skill button click."""
        selected_skill_id = self._get_selected_skill_id()
        if selected_skill_id:
            self.delete_skill_requested.emit(selected_skill_id)

    def _on_edit_education_clicked(self) -> None:
        """Handle edit education button click."""
        selected_education_id = self._get_selected_education_id()
        if selected_education_id:
            self.edit_education_requested.emit(selected_education_id)

    def _on_delete_education_clicked(self) -> None:
        """Handle delete education button click."""
        selected_education_id = self._get_selected_education_id()
        if selected_education_id:
            self.delete_education_requested.emit(selected_education_id)

    def _get_selected_skill_id(self) -> Optional[int]:
        """Get the ID of the currently selected skill."""
        if not hasattr(self, 'skills_panel'):
            return None
        current_item = self.skills_panel.skill_list.currentItem()
        if current_item is None:
            return None
        return int(current_item.data(Qt.ItemDataRole.UserRole))

    def _get_selected_education_id(self) -> Optional[int]:
        """Get the ID of the currently selected education entry."""
        if not hasattr(self, 'education_panel'):
            return None
        current_item = self.education_panel.education_list.currentItem()
        if current_item is None:
            return None
        return int(current_item.data(Qt.ItemDataRole.UserRole))

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        self._load_profile_data()
        self._load_skills_data()
        self._load_education_data()

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

    def _load_skills_data(self) -> None:
        """Load skills for the current profile."""
        if hasattr(self, 'skills_panel') and self.skills_panel:
            self.skills_panel.load_skills(DEFAULT_PROFILE_ID)

    def _load_education_data(self) -> None:
        """Load education for the current profile."""
        if hasattr(self, 'education_panel') and self.education_panel:
            self.education_panel.load_education(DEFAULT_PROFILE_ID)


__all__ = ["ProfileManagementScreen"]
