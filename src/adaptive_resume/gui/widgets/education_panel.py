"""Education management panel for the GUI."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QLabel
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.models import Education

if TYPE_CHECKING:
    from adaptive_resume.services.education_service import EducationService


class EducationPanel(QWidget):
    """Display ordered education history for the active profile."""

    def __init__(self, education_service: "EducationService", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.education_service = education_service
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QLabel("Education")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(header)

        self.education_list = QListWidget()
        layout.addWidget(self.education_list)

    def load_education(self, profile_id: Optional[int]) -> None:
        """Refresh the list of education entries for the given profile."""
        self.education_list.clear()
        if profile_id is None:
            return

        entries = self.education_service.list_education_for_profile(profile_id)

        for education in entries:
            label = f"{education.degree or 'Education'} — {education.institution}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, education.id)
            self.education_list.addItem(item)
