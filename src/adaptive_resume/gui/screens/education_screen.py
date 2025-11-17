"""Education management screen."""

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
from ..widgets import EducationPanel
from adaptive_resume.models.base import DEFAULT_PROFILE_ID


class EducationScreen(BaseScreen):
    """Screen for managing education entries."""

    # Signals
    add_education_requested = pyqtSignal()
    edit_education_requested = pyqtSignal()
    delete_education_requested = pyqtSignal()

    def __init__(
        self,
        education_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.education_service = education_service
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the education screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header with action buttons
        header_layout = QHBoxLayout()

        header = QLabel("Manage Education")
        header.setObjectName("screenTitle")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # Add education button
        add_btn = QPushButton("➕ Add Education")
        add_btn.clicked.connect(self.add_education_requested.emit)
        header_layout.addWidget(add_btn)

        # Edit education button
        edit_btn = QPushButton("✏️ Edit Education")
        edit_btn.clicked.connect(self.edit_education_requested.emit)
        header_layout.addWidget(edit_btn)

        # Delete education button
        delete_btn = QPushButton("🗑️ Delete Education")
        delete_btn.clicked.connect(self.delete_education_requested.emit)
        header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # Education panel
        self.education_panel = EducationPanel(self.education_service)
        layout.addWidget(self.education_panel)

    def _load_data(self) -> None:
        """Load education for the current profile."""
        self.education_panel.load_education(DEFAULT_PROFILE_ID)

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        self._load_data()

    def get_selected_education_id(self) -> Optional[int]:
        """Get the ID of the currently selected education entry."""
        current_item = self.education_panel.education_list.currentItem()
        if current_item is None:
            return None
        return int(current_item.data(Qt.ItemDataRole.UserRole))


__all__ = ["EducationScreen"]
