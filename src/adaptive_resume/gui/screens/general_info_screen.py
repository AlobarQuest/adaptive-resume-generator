"""General info (Skills & Education) management screen."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QSplitter,
    )
    from PyQt6.QtCore import Qt
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from ..widgets import SkillsPanel, EducationPanel


class GeneralInfoScreen(BaseScreen):
    """Screen for managing skills and education."""

    def __init__(
        self,
        skill_service=None,
        education_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.skill_service = skill_service
        self.education_service = education_service
        self.current_profile_id: Optional[int] = None
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the general info screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header
        header = QLabel("General Info")
        header.setObjectName("screenTitle")
        layout.addWidget(header)

        # Splitter for skills and education
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Skills panel
        self.skills_panel = SkillsPanel(self.skill_service)
        splitter.addWidget(self.skills_panel)

        # Education panel
        self.education_panel = EducationPanel(self.education_service)
        splitter.addWidget(self.education_panel)

        # Set initial sizes (50/50 split)
        splitter.setSizes([400, 400])

        layout.addWidget(splitter)

    def set_profile(self, profile_id: int) -> None:
        """Set the current profile and load data."""
        self.current_profile_id = profile_id
        self._load_data()

    def _load_data(self) -> None:
        """Load skills and education for the current profile."""
        if not self.current_profile_id:
            return

        self.skills_panel.load_skills(self.current_profile_id)
        self.education_panel.load_education(self.current_profile_id)

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        if self.current_profile_id:
            self._load_data()


__all__ = ["GeneralInfoScreen"]
