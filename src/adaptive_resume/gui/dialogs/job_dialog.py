"""Dialog for creating or editing job entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QHBoxLayout,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QTextEdit,
        QWidget,
        QVBoxLayout,
        QMessageBox,
        QDateEdit,
        QCheckBox,
    )
    from PyQt6.QtCore import QDate
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .bullet_enhancement_dialog import BulletEnhancementDialog


@dataclass
class JobDialogResult:
    """Return payload describing job data from the dialog."""

    company_name: str
    job_title: str
    location: str
    start_date: date
    end_date: Optional[date]
    is_current: bool
    description: str
    bullets: List[str]


class JobDialog(QDialog):
    """Dialog used to gather job information and bullet highlights."""

    def __init__(self, parent: Optional[QWidget] = None, job: Optional[dict] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Job")
        self._build_form()
        if job:
            self._load_job(job)

    def _build_form(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.company_name = QLineEdit()
        self.job_title = QLineEdit()
        self.location = QLineEdit()

        # Date fields with US format (MM-dd-yyyy)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("MM-dd-yyyy")
        self.start_date.setDate(QDate.currentDate())

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("MM-dd-yyyy")
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setSpecialValueText("Present")  # Show "Present" when cleared

        # "Currently working here" checkbox
        self.is_current_checkbox = QCheckBox("Currently working here")
        self.is_current_checkbox.stateChanged.connect(self._on_current_changed)

        self.description = QTextEdit()
        self.description.setMaximumHeight(120)

        form.addRow("Company", self.company_name)
        form.addRow("Title", self.job_title)
        form.addRow("Location", self.location)
        form.addRow("Start Date", self.start_date)
        form.addRow("End Date", self.end_date)
        form.addRow("", self.is_current_checkbox)
        form.addRow("Role Description", self.description)

        layout.addLayout(form)

        bullets_header = QHBoxLayout()
        self.bullets = QListWidget()
        add_button = QPushButton("Add Accomplishment")
        enhance_button = QPushButton("Enhance Accomplishment")
        remove_button = QPushButton("Remove Accomplishment")
        add_button.clicked.connect(self._add_bullet)
        enhance_button.clicked.connect(self._enhance_bullet)
        remove_button.clicked.connect(self._remove_bullet)

        bullets_header.addWidget(add_button)
        bullets_header.addWidget(enhance_button)
        bullets_header.addWidget(remove_button)

        layout.addLayout(bullets_header)
        layout.addWidget(self.bullets)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _on_current_changed(self, state: int) -> None:
        """Handle the 'currently working here' checkbox state change."""
        # Disable end date if currently working
        self.end_date.setEnabled(state == 0)

    def _load_job(self, job: dict) -> None:
        self.company_name.setText(job.get("company_name", ""))
        self.job_title.setText(job.get("job_title", ""))
        self.location.setText(job.get("location", ""))

        # Load start date
        if job.get("start_date"):
            start = job["start_date"]
            self.start_date.setDate(QDate(start.year, start.month, start.day))

        # Load end date and set checkbox
        if job.get("end_date"):
            end = job["end_date"]
            self.end_date.setDate(QDate(end.year, end.month, end.day))
            self.is_current_checkbox.setChecked(False)
        else:
            # No end date means current position
            self.is_current_checkbox.setChecked(True)
            self.end_date.setEnabled(False)

        self.description.setPlainText(job.get("description", ""))
        for bullet in job.get("bullets", []):
            self.bullets.addItem(QListWidgetItem(bullet))

    def _add_bullet(self) -> None:
        text = QTextEdit()
        text.setPlaceholderText("Enter accomplishment (min 10 characters)")
        text.setFixedHeight(80)
        dialog = QDialog(self)
        dialog.setWindowTitle("New Accomplishment")
        inner_layout = QVBoxLayout(dialog)
        inner_layout.addWidget(text)

        # Add button layout with Enhance button
        button_layout = QHBoxLayout()
        enhance_btn = QPushButton("✨ Enhance")
        enhance_btn.setToolTip("Enhance this accomplishment before saving")
        enhance_btn.clicked.connect(lambda: self._enhance_inline_text(text))
        button_layout.addWidget(enhance_btn)
        button_layout.addStretch()
        inner_layout.addLayout(button_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        inner_layout.addWidget(button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            content = text.toPlainText().strip()
            if content:
                self.bullets.addItem(QListWidgetItem(content))
        dialog.deleteLater()

    def _remove_bullet(self) -> None:
        row = self.bullets.currentRow()
        if row >= 0:
            item = self.bullets.takeItem(row)
            del item

    def _enhance_inline_text(self, text_edit: QTextEdit) -> None:
        """Enhance text in a QTextEdit widget (for inline enhancement in dialogs)."""
        original_text = text_edit.toPlainText().strip()
        if not original_text:
            QMessageBox.information(
                self,
                "No Text",
                "Please enter some text before enhancing."
            )
            return

        # Open enhancement dialog
        dialog = BulletEnhancementDialog(original_text, self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            enhanced_text = dialog.get_enhanced_text()
            if enhanced_text:
                text_edit.setPlainText(enhanced_text)

    def _enhance_bullet(self) -> None:
        """Enhance the selected bullet using templates or AI."""
        row = self.bullets.currentRow()
        if row < 0:
            QMessageBox.information(
                self,
                "No Accomplishment Selected",
                "Please select an accomplishment to enhance."
            )
            return

        # Get current bullet text
        current_item = self.bullets.item(row)
        original_text = current_item.text()

        # Open enhancement dialog
        dialog = BulletEnhancementDialog(original_text, self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            enhanced_text = dialog.get_enhanced_text()
            if enhanced_text:
                # Replace the bullet with enhanced version
                current_item.setText(enhanced_text)

    def _validate_and_accept(self) -> None:
        """Validate form fields before accepting the dialog."""
        # Validate required fields
        if not self.company_name.text().strip():
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a company name."
            )
            self.company_name.setFocus()
            return

        if not self.job_title.text().strip():
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a job title."
            )
            self.job_title.setFocus()
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

    def get_result(self) -> JobDialogResult:
        """Return the captured job data."""
        # Convert QDate to Python date
        start_qdate = self.start_date.date()
        start = date(start_qdate.year(), start_qdate.month(), start_qdate.day())

        # End date is None if currently working
        end = None
        if not self.is_current_checkbox.isChecked():
            end_qdate = self.end_date.date()
            end = date(end_qdate.year(), end_qdate.month(), end_qdate.day())

        return JobDialogResult(
            company_name=self.company_name.text().strip(),
            job_title=self.job_title.text().strip(),
            location=self.location.text().strip(),
            start_date=start,
            end_date=end,
            is_current=self.is_current_checkbox.isChecked(),
            description=self.description.toPlainText().strip(),
            bullets=[self.bullets.item(i).text() for i in range(self.bullets.count())],
        )
