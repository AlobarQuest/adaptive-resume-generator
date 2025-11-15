"""Dialog for creating or editing education entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional
from decimal import Decimal

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLineEdit,
        QTextEdit,
        QVBoxLayout,
        QMessageBox,
        QDateEdit,
        QCheckBox,
        QDoubleSpinBox,
    )
    from PyQt6.QtCore import QDate
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc


@dataclass
class EducationDialogResult:
    """Return payload describing education data from the dialog."""

    institution: str
    degree: str
    field_of_study: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    gpa: Optional[Decimal]
    honors: Optional[str]
    relevant_coursework: Optional[str]


class EducationDialog(QDialog):
    """Dialog used to gather education information."""

    def __init__(self, parent=None, education: Optional[dict] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Education")
        self.setMinimumWidth(500)
        self._build_form()
        if education:
            self._load_education(education)

    def _build_form(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Required fields
        self.institution = QLineEdit()
        self.institution.setPlaceholderText("e.g., Stanford University")
        self.degree = QLineEdit()
        self.degree.setPlaceholderText("e.g., Bachelor of Science")

        # Optional fields
        self.field_of_study = QLineEdit()
        self.field_of_study.setPlaceholderText("e.g., Computer Science")

        # Date fields with US format (MM-dd-yyyy)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("MM-dd-yyyy")
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setSpecialValueText("Not specified")

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("MM-dd-yyyy")
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setSpecialValueText("Not specified")

        # "Currently enrolled" checkbox
        self.is_current_checkbox = QCheckBox("Currently enrolled")
        self.is_current_checkbox.stateChanged.connect(self._on_current_changed)

        # GPA (0.0-4.0)
        self.gpa = QDoubleSpinBox()
        self.gpa.setRange(0.0, 4.0)
        self.gpa.setDecimals(2)
        self.gpa.setSingleStep(0.01)
        self.gpa.setSpecialValueText("N/A")
        self.gpa.setValue(0.0)  # Will show as "N/A"

        # Multi-line fields
        self.honors = QLineEdit()
        self.honors.setPlaceholderText("e.g., Summa Cum Laude, Dean's List")

        self.relevant_coursework = QTextEdit()
        self.relevant_coursework.setPlaceholderText("List relevant courses...")
        self.relevant_coursework.setMaximumHeight(80)

        # Add to form
        form.addRow("Institution *", self.institution)
        form.addRow("Degree *", self.degree)
        form.addRow("Field of Study", self.field_of_study)
        form.addRow("Start Date", self.start_date)
        form.addRow("End Date", self.end_date)
        form.addRow("", self.is_current_checkbox)
        form.addRow("GPA (0.0-4.0)", self.gpa)
        form.addRow("Honors/Awards", self.honors)
        form.addRow("Relevant Coursework", self.relevant_coursework)

        layout.addLayout(form)

        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _on_current_changed(self, state: int) -> None:
        """Handle the 'currently enrolled' checkbox state change."""
        # Disable end date if currently enrolled
        self.end_date.setEnabled(state == 0)

    def _load_education(self, education: dict) -> None:
        """Load existing education data into the form."""
        self.institution.setText(education.get("institution", ""))
        self.degree.setText(education.get("degree", ""))
        self.field_of_study.setText(education.get("field_of_study", ""))

        # Load start date
        if education.get("start_date"):
            start = education["start_date"]
            self.start_date.setDate(QDate(start.year, start.month, start.day))

        # Load end date and set checkbox
        if education.get("end_date"):
            end = education["end_date"]
            self.end_date.setDate(QDate(end.year, end.month, end.day))
            self.is_current_checkbox.setChecked(False)
        else:
            # No end date means currently enrolled
            self.is_current_checkbox.setChecked(True)
            self.end_date.setEnabled(False)

        # Load GPA
        if education.get("gpa") is not None:
            self.gpa.setValue(float(education["gpa"]))

        self.honors.setText(education.get("honors", ""))
        self.relevant_coursework.setPlainText(education.get("relevant_coursework", ""))

    def _validate_and_accept(self) -> None:
        """Validate form fields before accepting the dialog."""
        # Validate required fields
        if not self.institution.text().strip():
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter an institution name."
            )
            self.institution.setFocus()
            return

        if not self.degree.text().strip():
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a degree."
            )
            self.degree.setFocus()
            return

        # Dates are always valid with QDateEdit, just check logical consistency
        if not self.is_current_checkbox.isChecked():
            start_qdate = self.start_date.date()
            end_qdate = self.end_date.date()
            if end_qdate < start_qdate:
                QMessageBox.warning(
                    self,
                    "Invalid Dates",
                    "End date cannot be before start date."
                )
                self.end_date.setFocus()
                return

        # All validation passed, accept the dialog
        self.accept()

    def get_result(self) -> EducationDialogResult:
        """Return the captured education data."""
        # Convert QDate to Python date (if not special value)
        start = None
        if self.start_date.text() != "Not specified":
            start_qdate = self.start_date.date()
            start = date(start_qdate.year(), start_qdate.month(), start_qdate.day())

        # End date is None if currently enrolled
        end = None
        if not self.is_current_checkbox.isChecked() and self.end_date.text() != "Not specified":
            end_qdate = self.end_date.date()
            end = date(end_qdate.year(), end_qdate.month(), end_qdate.day())

        # GPA is None if 0.0 (special value)
        gpa_value = None
        if self.gpa.value() > 0.0:
            gpa_value = Decimal(str(self.gpa.value()))

        return EducationDialogResult(
            institution=self.institution.text().strip(),
            degree=self.degree.text().strip(),
            field_of_study=self.field_of_study.text().strip() or None,
            start_date=start,
            end_date=end,
            gpa=gpa_value,
            honors=self.honors.text().strip() or None,
            relevant_coursework=self.relevant_coursework.toPlainText().strip() or None,
        )
