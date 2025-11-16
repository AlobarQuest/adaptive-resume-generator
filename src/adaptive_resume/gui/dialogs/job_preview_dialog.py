"""Dialog for previewing and editing imported job data."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QTextEdit,
        QGroupBox,
        QFormLayout,
    )
    from PyQt6.QtCore import Qt
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.services import ImportedJob


class JobPreviewDialog(QDialog):
    """Dialog for previewing and editing imported job data.

    Allows users to review automatically extracted job information
    and make corrections before saving to the database.
    """

    def __init__(self, job: ImportedJob, parent: Optional[QDialog] = None):
        """Initialize the preview dialog.

        Args:
            job: Imported job data to preview/edit
            parent: Parent widget
        """
        super().__init__(parent)
        self.job = job

        self.setWindowTitle("Preview Imported Job")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self._build_ui()
        self._populate_fields()

    def _build_ui(self):
        """Build the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Preview Imported Job")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "Review the automatically extracted information and make any necessary corrections."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        # Source info
        if self.job.source_platform:
            source_label = QLabel(f"Source: {self.job.source_platform.title()}")
            source_label.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 10px;")
            layout.addWidget(source_label)

        # Job details form
        details_group = QGroupBox("Job Details")
        form_layout = QFormLayout()

        # Company name
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("Company name")
        form_layout.addRow("Company:", self.company_input)

        # Job title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Job title")
        form_layout.addRow("Job Title:*", self.title_input)

        # Location
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Location (e.g., San Francisco, CA)")
        form_layout.addRow("Location:", self.location_input)

        # Salary
        self.salary_input = QLineEdit()
        self.salary_input.setPlaceholderText("Salary range (if provided)")
        form_layout.addRow("Salary:", self.salary_input)

        # Application URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Application URL")
        form_layout.addRow("Application URL:", self.url_input)

        details_group.setLayout(form_layout)
        layout.addWidget(details_group)

        # Job description
        desc_group = QGroupBox("Job Description*")
        desc_layout = QVBoxLayout()

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Full job description and requirements...")
        self.description_input.setMinimumHeight(200)
        desc_layout.addWidget(self.description_input)

        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)

        # Required field note
        required_note = QLabel("* Required fields")
        required_note.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        layout.addWidget(required_note)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save Job")
        save_button.setObjectName("primaryButton")
        save_button.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        save_button.clicked.connect(self._validate_and_accept)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

    def _populate_fields(self):
        """Populate form fields with imported job data."""
        if self.job.company_name:
            self.company_input.setText(self.job.company_name)

        if self.job.job_title:
            self.title_input.setText(self.job.job_title)

        if self.job.location:
            self.location_input.setText(self.job.location)

        if self.job.salary:
            self.salary_input.setText(self.job.salary)

        if self.job.application_url:
            self.url_input.setText(self.job.application_url)

        if self.job.description:
            self.description_input.setPlainText(self.job.description)

    def _validate_and_accept(self):
        """Validate required fields and accept dialog."""
        # Check required fields
        description = self.description_input.toPlainText().strip()

        if not description:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Missing Information",
                "Job description is required. Please enter the job description."
            )
            self.description_input.setFocus()
            return

        # Accept dialog
        self.accept()

    def get_edited_job(self) -> ImportedJob:
        """Get the edited job data.

        Returns:
            ImportedJob with user edits applied
        """
        # Create new ImportedJob with edited data
        edited_job = ImportedJob(
            company_name=self.company_input.text().strip() or None,
            job_title=self.title_input.text().strip() or None,
            location=self.location_input.text().strip() or None,
            salary=self.salary_input.text().strip() or None,
            description=self.description_input.toPlainText().strip(),
            application_url=self.url_input.text().strip() or None,
            source_platform=self.job.source_platform
        )

        return edited_job


__all__ = ['JobPreviewDialog']
