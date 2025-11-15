"""Skills management screen."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from ..widgets import SkillsPanel


class SkillsScreen(BaseScreen):
    """Screen for managing skills."""

    # Signals
    add_skill_requested = pyqtSignal()
    edit_skill_requested = pyqtSignal()
    delete_skill_requested = pyqtSignal()

    def __init__(
        self,
        skill_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.skill_service = skill_service
        self.current_profile_id: Optional[int] = None
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the skills screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header with action buttons
        header_layout = QHBoxLayout()

        header = QLabel("Manage Skills")
        header.setObjectName("screenTitle")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # Add skill button
        add_btn = QPushButton("➕ Add Skill")
        add_btn.clicked.connect(self.add_skill_requested.emit)
        header_layout.addWidget(add_btn)

        # Edit skill button
        edit_btn = QPushButton("✏️ Edit Skill")
        edit_btn.clicked.connect(self.edit_skill_requested.emit)
        header_layout.addWidget(edit_btn)

        # Delete skill button
        delete_btn = QPushButton("🗑️ Delete Skill")
        delete_btn.clicked.connect(self.delete_skill_requested.emit)
        header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # Skills panel
        self.skills_panel = SkillsPanel(self.skill_service)
        layout.addWidget(self.skills_panel)

    def set_profile(self, profile_id: int) -> None:
        """Set the current profile and load data."""
        self.current_profile_id = profile_id
        self._load_data()

    def _load_data(self) -> None:
        """Load skills for the current profile."""
        if not self.current_profile_id:
            return

        self.skills_panel.load_skills(self.current_profile_id)

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        if self.current_profile_id:
            self._load_data()

    def get_selected_skill_id(self) -> Optional[int]:
        """Get the ID of the currently selected skill."""
        current_item = self.skills_panel.skills_list.currentItem()
        if current_item is None:
            return None
        return int(current_item.data(Qt.ItemDataRole.UserRole))


__all__ = ["SkillsScreen"]
