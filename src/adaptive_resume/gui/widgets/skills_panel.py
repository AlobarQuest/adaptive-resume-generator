"""Skills management panel for the GUI."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QLabel
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.models import Skill

if TYPE_CHECKING:
    from adaptive_resume.services.skill_service import SkillService


class SkillsPanel(QWidget):
    """Display ordered skills for the active profile."""

    def __init__(self, skill_service: "SkillService", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.skill_service = skill_service
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QLabel("Skills")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(header)

        self.skill_list = QListWidget()
        layout.addWidget(self.skill_list)

    def load_skills(self, profile_id: Optional[int]) -> None:
        """Refresh the list of skills for the given profile."""
        self.skill_list.clear()
        if profile_id is None:
            return

        skills = self.skill_service.list_skills_for_profile(profile_id)

        for skill in skills:
            label = f"{skill.skill_name} ({skill.proficiency_level or 'Unknown'})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, skill.id)
            self.skill_list.addItem(item)
