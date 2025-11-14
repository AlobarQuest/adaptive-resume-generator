"""Profile management screen."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QListWidget,
        QListWidgetItem,
        QFrame,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen


class ProfileManagementScreen(BaseScreen):
    """Screen for managing user profiles."""

    # Signals
    select_profile_requested = pyqtSignal(int)  # profile_id
    add_profile_requested = pyqtSignal()
    edit_profile_requested = pyqtSignal()

    def __init__(
        self,
        profile_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.profile_service = profile_service
        self.current_profile_id: Optional[int] = None
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

        # Add profile button
        add_profile_btn = QPushButton("➕ Add Profile")
        add_profile_btn.clicked.connect(self.add_profile_requested.emit)
        header_layout.addWidget(add_profile_btn)

        # Edit profile button
        edit_profile_btn = QPushButton("✏️ Edit Profile")
        edit_profile_btn.clicked.connect(self.edit_profile_requested.emit)
        header_layout.addWidget(edit_profile_btn)

        layout.addLayout(header_layout)

        # Profile list in a nice frame
        list_frame = QFrame()
        list_frame.setObjectName("panelFrame")
        list_layout = QVBoxLayout(list_frame)

        list_title = QLabel("Your Profiles")
        list_title.setObjectName("panelTitle")
        list_layout.addWidget(list_title)

        self.profile_list = QListWidget()
        self.profile_list.itemDoubleClicked.connect(self._on_profile_double_clicked)
        self.profile_list.currentItemChanged.connect(self._on_profile_selected)
        list_layout.addWidget(self.profile_list)

        select_btn = QPushButton("Select Profile")
        select_btn.setObjectName("primaryButton")
        select_btn.clicked.connect(self._on_select_clicked)
        list_layout.addWidget(select_btn)

        layout.addWidget(list_frame)

        # Current profile info
        info_frame = QFrame()
        info_frame.setObjectName("panelFrame")
        info_layout = QVBoxLayout(info_frame)

        info_title = QLabel("Current Profile")
        info_title.setObjectName("panelTitle")
        info_layout.addWidget(info_title)

        self.current_profile_label = QLabel("No profile selected")
        self.current_profile_label.setWordWrap(True)
        info_layout.addWidget(self.current_profile_label)

        layout.addWidget(info_frame)

    def set_profile(self, profile_id: int) -> None:
        """Set the current profile."""
        self.current_profile_id = profile_id
        self._update_current_profile_display()

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        self._load_profiles()
        self._update_current_profile_display()

    def _load_profiles(self) -> None:
        """Load all profiles into the list."""
        if not self.profile_service:
            return

        self.profile_list.clear()

        from adaptive_resume.models import Profile

        profiles = (
            self.profile_service.session.query(Profile)
            .order_by(Profile.last_name.asc(), Profile.first_name.asc())
            .all()
        )

        for profile in profiles:
            label = f"{profile.first_name} {profile.last_name}"
            if profile.email:
                label += f" ({profile.email})"

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            self.profile_list.addItem(item)

            # Select current profile
            if profile.id == self.current_profile_id:
                self.profile_list.setCurrentItem(item)

    def _update_current_profile_display(self) -> None:
        """Update the current profile info display."""
        if not self.current_profile_id or not self.profile_service:
            self.current_profile_label.setText("No profile selected")
            return

        profile = self.profile_service.get_profile_by_id(self.current_profile_id)
        if profile:
            info_text = f"<b>{profile.first_name} {profile.last_name}</b><br>"
            info_text += f"<b>Email:</b> {profile.email}<br>"
            if profile.phone:
                info_text += f"<b>Phone:</b> {profile.phone}<br>"
            if profile.city and profile.state:
                info_text += f"<b>Location:</b> {profile.city}, {profile.state}<br>"
            if profile.linkedin_url:
                info_text += f"<b>LinkedIn:</b> {profile.linkedin_url}<br>"

            self.current_profile_label.setText(info_text)

    def _on_profile_selected(self, current: Optional[QListWidgetItem]) -> None:
        """Handle profile selection in the list."""
        # Just visual feedback, doesn't change the active profile
        pass

    def _on_profile_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on a profile - select it."""
        profile_id = int(item.data(Qt.ItemDataRole.UserRole))
        self.select_profile_requested.emit(profile_id)

    def _on_select_clicked(self) -> None:
        """Handle Select Profile button click."""
        current_item = self.profile_list.currentItem()
        if current_item:
            profile_id = int(current_item.data(Qt.ItemDataRole.UserRole))
            self.select_profile_requested.emit(profile_id)


__all__ = ["ProfileManagementScreen"]
