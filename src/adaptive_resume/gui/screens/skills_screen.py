"""Skills management screen."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
    )
    from PyQt6.QtCore import Qt
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from ..widgets import SkillsPanel


class SkillsScreen(BaseScreen):
    """Screen for managing skills."""

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

        # Header
        header = QLabel("Manage Skills")
        header.setObjectName("screenTitle")
        layout.addWidget(header)

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


__all__ = ["SkillsScreen"]
