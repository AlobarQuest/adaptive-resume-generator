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

from adaptive_resume.services.skill_database_service import SkillDatabaseService
from adaptive_resume.gui.widgets import SkillAutocompleteWidget


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

    def __init__(self, parent=None, skill: Optional[dict] = None, use_autocomplete: bool = True) -> None:
        super().__init__(parent)
        self.setWindowTitle("Skill")
        self.setMinimumWidth(400)
        self.use_autocomplete = use_autocomplete
        self._selected_skill_id = None  # Track selected skill from database

        # Initialize skill database service for autocomplete
        self._skill_db_service = None
        if self.use_autocomplete:
            try:
                self._skill_db_service = SkillDatabaseService()
            except Exception:
                # Fallback to regular input if skill database fails
                self.use_autocomplete = False

        self._build_form()
        if skill:
            self._load_skill(skill)

    def _build_form(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Skill name (required) - use autocomplete if available
        if self.use_autocomplete and self._skill_db_service:
            self.skill_name_autocomplete = SkillAutocompleteWidget(
                skill_service=self._skill_db_service,
                placeholder="Type to search skills... (e.g., Python, Leadership, AWS)"
            )
            self.skill_name_autocomplete.skill_selected.connect(self._on_skill_selected)
            # Create a simple QLineEdit for compatibility (will be hidden)
            self.skill_name = QLineEdit()
            self.skill_name.setVisible(False)
            form.addRow("Skill Name *", self.skill_name_autocomplete)
        else:
            # Fallback to regular input
            self.skill_name = QLineEdit()
            self.skill_name.setPlaceholderText("e.g., Python, Leadership, AWS")
            self.skill_name_autocomplete = None
            form.addRow("Skill Name *", self.skill_name)

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

    def _on_skill_selected(self, skill_name: str, skill_id: Optional[int]) -> None:
        """
        Handle skill selection from autocomplete.

        Auto-populates category if skill is from database.
        """
        # Store the selected skill ID
        self._selected_skill_id = skill_id

        # Update the hidden skill_name field for compatibility
        self.skill_name.setText(skill_name)

        # If skill is from database, auto-populate category
        if skill_id is not None and self._skill_db_service:
            skill_details = self._skill_db_service.get_skill_details(skill_id)
            if skill_details:
                # Set category
                category = skill_details.category
                index = self.category.findText(category)
                if index >= 0:
                    self.category.setCurrentIndex(index)
                else:
                    # Add category if not in list
                    self.category.setEditText(category)

    def _load_skill(self, skill: dict) -> None:
        """Load existing skill data into the form."""
        skill_name = skill.get("skill_name", "")

        # Set skill name based on which widget is active
        if self.skill_name_autocomplete:
            self.skill_name_autocomplete.set_text(skill_name)
        else:
            self.skill_name.setText(skill_name)

        # Always update hidden field
        self.skill_name.setText(skill_name)

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
        # Get skill name from appropriate widget
        if self.skill_name_autocomplete:
            skill_text = self.skill_name_autocomplete.text().strip()
        else:
            skill_text = self.skill_name.text().strip()

        # Validate required fields
        if not skill_text:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a skill name."
            )
            if self.skill_name_autocomplete:
                self.skill_name_autocomplete.focusInEvent(None)
            else:
                self.skill_name.setFocus()
            return

        # Update hidden field if using autocomplete
        if self.skill_name_autocomplete:
            self.skill_name.setText(skill_text)

        # All validation passed, accept the dialog
        self.accept()

    def get_result(self) -> SkillDialogResult:
        """Return the captured skill data."""
        # Get skill name from appropriate widget
        if self.skill_name_autocomplete:
            skill_text = self.skill_name_autocomplete.text().strip()
        else:
            skill_text = self.skill_name.text().strip()

        # Years experience is None if 0.0 (special value)
        years_exp = None
        if self.years_experience.value() > 0.0:
            years_exp = Decimal(str(self.years_experience.value()))

        # Get category text (whether from dropdown or custom)
        category_text = self.category.currentText().strip() or None

        # Get proficiency level
        proficiency = self.proficiency_level.currentText().strip() or None

        return SkillDialogResult(
            skill_name=skill_text,
            category=category_text,
            proficiency_level=proficiency,
            years_experience=years_exp,
        )
