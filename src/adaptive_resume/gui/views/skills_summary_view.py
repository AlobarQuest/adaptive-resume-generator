"""Summary view for skills grouped by category."""

from __future__ import annotations

from typing import Iterable, Optional

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QLabel
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.models import Skill


class SkillsSummaryView(QWidget):
    """Display aggregated skills grouped by category."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QLabel("Skill Overview")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(header)

        self.skill_list = QListWidget()
        layout.addWidget(self.skill_list)

    def set_skills(self, skills: Iterable[Skill]) -> None:
        """Populate the view with the given skill rows."""
        categories: dict[str, list[Skill]] = {}
        for skill in skills:
            categories.setdefault(skill.category or "Uncategorised", []).append(skill)

        self.skill_list.clear()
        for category, items in sorted(categories.items()):
            item = QListWidgetItem(f"{category} ({len(items)})")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.skill_list.addItem(item)
            for skill in items:
                detail = f"  • {skill.skill_name} — {skill.proficiency_level or 'N/A'}"
                detail_item = QListWidgetItem(detail)
                detail_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.skill_list.addItem(detail_item)
