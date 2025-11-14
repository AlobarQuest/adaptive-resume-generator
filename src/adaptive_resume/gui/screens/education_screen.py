"""Education management screen."""

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
from ..widgets import EducationPanel


class EducationScreen(BaseScreen):
    """Screen for managing education entries."""

    def __init__(
        self,
        education_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.education_service = education_service
        self.current_profile_id: Optional[int] = None
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the education screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header
        header = QLabel("Manage Education")
        header.setObjectName("screenTitle")
        layout.addWidget(header)

        # Education panel
        self.education_panel = EducationPanel(self.education_service)
        layout.addWidget(self.education_panel)

    def set_profile(self, profile_id: int) -> None:
        """Set the current profile and load data."""
        self.current_profile_id = profile_id
        self._load_data()

    def _load_data(self) -> None:
        """Load education for the current profile."""
        if not self.current_profile_id:
            return

        self.education_panel.load_education(self.current_profile_id)

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        if self.current_profile_id:
            self._load_data()


__all__ = ["EducationScreen"]
