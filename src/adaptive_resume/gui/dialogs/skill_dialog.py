"""Dialog for creating or editing skill entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLineEdit,
        QComboBox,
        QDoubleSpinBox,
        QVBoxLayout,
        QMessageBox,
    )
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc


@dataclass
class SkillDialogResult:
    """Return payload describing skill data from the dialog."""

    skill_name: str
    category: Optional[str]
    proficiency_level: Optional[str]
    years_experience: Optional[Decimal]


class SkillDialog(QDialog):
    """Dialog used to gather skill information."""

    PROFICIENCY_LEVELS = ['', 'Beginner', 'Intermediate', 'Advanced', 'Expert']

    # Common skill categories
    CATEGORIES = [
        '',
        'Programming Languages',
        'Frameworks & Libraries',
        'Databases',
        'Cloud & DevOps',
        'Tools & Platforms',
        'Soft Skills',
        'Other',
    ]

    def __init__(self, parent=None, skill: Optional[dict] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Skill")
        self.setMinimumWidth(400)
        self._build_form()
        if skill:
            self._load_skill(skill)

    def _build_form(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Skill name (required)
        self.skill_name = QLineEdit()
        self.skill_name.setPlaceholderText("e.g., Python, Leadership, AWS")

        # Category (optional, dropdown)
        self.category = QComboBox()
        self.category.setEditable(True)  # Allow custom categories
        self.category.addItems(self.CATEGORIES)
        self.category.setPlaceholderText("Select or type a category")

        # Proficiency level (optional, dropdown)
        self.proficiency_level = QComboBox()
        self.proficiency_level.addItems(self.PROFICIENCY_LEVELS)

        # Years of experience (optional)
        self.years_experience = QDoubleSpinBox()
        self.years_experience.setRange(0.0, 50.0)
        self.years_experience.setDecimals(1)
        self.years_experience.setSingleStep(0.5)
        self.years_experience.setSpecialValueText("N/A")
        self.years_experience.setValue(0.0)  # Will show as "N/A"

        # Add to form
        form.addRow("Skill Name *", self.skill_name)
        form.addRow("Category", self.category)
        form.addRow("Proficiency Level", self.proficiency_level)
        form.addRow("Years of Experience", self.years_experience)

        layout.addLayout(form)

        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _load_skill(self, skill: dict) -> None:
        """Load existing skill data into the form."""
        self.skill_name.setText(skill.get("skill_name", ""))

        category = skill.get("category", "")
        if category:
            index = self.category.findText(category)
            if index >= 0:
                self.category.setCurrentIndex(index)
            else:
                self.category.setEditText(category)

        proficiency = skill.get("proficiency_level", "")
        if proficiency:
            index = self.proficiency_level.findText(proficiency)
            if index >= 0:
                self.proficiency_level.setCurrentIndex(index)

        if skill.get("years_experience") is not None:
            self.years_experience.setValue(float(skill["years_experience"]))

    def _validate_and_accept(self) -> None:
        """Validate form fields before accepting the dialog."""
        # Validate required fields
        if not self.skill_name.text().strip():
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a skill name."
            )
            self.skill_name.setFocus()
            return

        # All validation passed, accept the dialog
        self.accept()

    def get_result(self) -> SkillDialogResult:
        """Return the captured skill data."""
        # Years experience is None if 0.0 (special value)
        years_exp = None
        if self.years_experience.value() > 0.0:
            years_exp = Decimal(str(self.years_experience.value()))

        # Get category text (whether from dropdown or custom)
        category_text = self.category.currentText().strip() or None

        # Get proficiency level
        proficiency = self.proficiency_level.currentText().strip() or None

        return SkillDialogResult(
            skill_name=self.skill_name.text().strip(),
            category=category_text,
            proficiency_level=proficiency,
            years_experience=years_exp,
        )
