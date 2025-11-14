"""Dialog for previewing and editing extracted resume data before import."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QFormLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QTextEdit,
        QGroupBox,
        QScrollArea,
        QWidget,
        QCheckBox,
        QMessageBox,
        QProgressDialog,
    )
    from PyQt6.QtCore import Qt
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.services import (
    ExtractedResume,
    ResumeImporter,
    ResumeImportError
)
from adaptive_resume.gui.database_manager import DatabaseManager


class ResumePreviewDialog(QDialog):
    """Dialog for previewing and confirming resume import.

    Shows extracted data organized by section:
    - Contact Information (editable)
    - Work Experience (with checkboxes)
    - Education (with checkboxes)
    - Skills (with checkboxes)
    - Certifications (with checkboxes)

    Allows users to:
    - Edit contact information
    - Select which items to import
    - See confidence scores
    - Import selected data into the system
    """

    def __init__(
        self,
        extracted_resume: ExtractedResume,
        profile_id: Optional[int] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.extracted = extracted_resume
        self.profile_id = profile_id
        self.import_successful = False

        self.setWindowTitle("Review Resume Data")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Review Extracted Resume Data")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Subtitle with confidence score
        subtitle_text = "Review and edit the extracted information before importing."
        if self.extracted.confidence_score > 0:
            confidence = int(self.extracted.confidence_score * 100)
            subtitle_text += f"\nExtraction confidence: {confidence}%"
        if self.extracted.extraction_method:
            method = self.extracted.extraction_method.title()
            subtitle_text += f" (Method: {method})"

        subtitle = QLabel(subtitle_text)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Contact Information Section
        contact_group = self._build_contact_section()
        content_layout.addWidget(contact_group)

        # Work Experience Section
        if self.extracted.jobs:
            jobs_group = self._build_jobs_section()
            content_layout.addWidget(jobs_group)

        # Education Section
        if self.extracted.education:
            edu_group = self._build_education_section()
            content_layout.addWidget(edu_group)

        # Skills Section
        if self.extracted.skills:
            skills_group = self._build_skills_section()
            content_layout.addWidget(skills_group)

        # Certifications Section
        if self.extracted.certifications:
            certs_group = self._build_certifications_section()
            content_layout.addWidget(certs_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        import_button = QPushButton("Import Resume Data")
        import_button.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        import_button.clicked.connect(self._import_resume)
        button_layout.addWidget(import_button)

        layout.addLayout(button_layout)

    def _build_contact_section(self) -> QGroupBox:
        """Build the contact information section."""
        group = QGroupBox("Contact Information")
        layout = QFormLayout()

        self.first_name_edit = QLineEdit(self.extracted.first_name or "")
        self.last_name_edit = QLineEdit(self.extracted.last_name or "")
        self.email_edit = QLineEdit(self.extracted.email or "")
        self.phone_edit = QLineEdit(self.extracted.phone or "")
        self.location_edit = QLineEdit(self.extracted.location or "")
        self.linkedin_edit = QLineEdit(self.extracted.linkedin_url or "")
        self.github_edit = QLineEdit(self.extracted.github_url or "")
        self.website_edit = QLineEdit(self.extracted.website_url or "")

        layout.addRow("First Name*:", self.first_name_edit)
        layout.addRow("Last Name*:", self.last_name_edit)
        layout.addRow("Email*:", self.email_edit)
        layout.addRow("Phone:", self.phone_edit)
        layout.addRow("Location:", self.location_edit)
        layout.addRow("LinkedIn:", self.linkedin_edit)
        layout.addRow("GitHub:", self.github_edit)
        layout.addRow("Website:", self.website_edit)

        required_label = QLabel("* Required fields")
        required_label.setStyleSheet("color: #999; font-size: 11px;")
        layout.addRow("", required_label)

        group.setLayout(layout)
        return group

    def _build_jobs_section(self) -> QGroupBox:
        """Build the work experience section."""
        group = QGroupBox(f"Work Experience ({len(self.extracted.jobs)} found)")
        layout = QVBoxLayout()

        self.job_checkboxes = []

        for i, job in enumerate(self.extracted.jobs):
            job_widget = QWidget()
            job_layout = QVBoxLayout(job_widget)
            job_layout.setContentsMargins(0, 5, 0, 5)

            # Checkbox with job title and company
            job_text = f"{job.job_title} at {job.company_name}"
            if job.start_date:
                job_text += f" ({job.start_date}"
                if job.is_current:
                    job_text += " - Present)"
                elif job.end_date:
                    job_text += f" - {job.end_date})"
                else:
                    job_text += ")"

            checkbox = QCheckBox(job_text)
            checkbox.setChecked(True)
            self.job_checkboxes.append(checkbox)
            job_layout.addWidget(checkbox)

            # Location
            if job.location:
                location_label = QLabel(f"  Location: {job.location}")
                location_label.setStyleSheet("color: #666; font-size: 12px;")
                job_layout.addWidget(location_label)

            # Bullet points
            if job.bullet_points:
                bullets_label = QLabel(f"  {len(job.bullet_points)} bullet points")
                bullets_label.setStyleSheet("color: #666; font-size: 12px;")
                job_layout.addWidget(bullets_label)

            # Confidence
            if job.confidence_score > 0:
                confidence = int(job.confidence_score * 100)
                conf_label = QLabel(f"  Confidence: {confidence}%")
                conf_label.setStyleSheet("color: #999; font-size: 11px;")
                job_layout.addWidget(conf_label)

            layout.addWidget(job_widget)

            # Separator
            if i < len(self.extracted.jobs) - 1:
                separator = QLabel()
                separator.setStyleSheet("border-bottom: 1px solid #ddd;")
                separator.setMaximumHeight(1)
                layout.addWidget(separator)

        group.setLayout(layout)
        return group

    def _build_education_section(self) -> QGroupBox:
        """Build the education section."""
        group = QGroupBox(f"Education ({len(self.extracted.education)} found)")
        layout = QVBoxLayout()

        self.edu_checkboxes = []

        for i, edu in enumerate(self.extracted.education):
            edu_text = f"{edu.degree_type or 'Degree'}"
            if edu.major:
                edu_text += f" in {edu.major}"
            edu_text += f" - {edu.school_name}"
            if edu.graduation_date:
                edu_text += f" ({edu.graduation_date})"

            checkbox = QCheckBox(edu_text)
            checkbox.setChecked(True)
            self.edu_checkboxes.append(checkbox)
            layout.addWidget(checkbox)

            # GPA
            if edu.gpa:
                gpa_label = QLabel(f"  GPA: {edu.gpa}")
                gpa_label.setStyleSheet("color: #666; font-size: 12px; margin-left: 20px;")
                layout.addWidget(gpa_label)

        group.setLayout(layout)
        return group

    def _build_skills_section(self) -> QGroupBox:
        """Build the skills section."""
        group = QGroupBox(f"Skills ({len(self.extracted.skills)} found)")
        layout = QVBoxLayout()

        # Select All / Deselect All buttons
        button_layout = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_all.clicked.connect(lambda: self._toggle_all_skills(True))
        button_layout.addWidget(select_all)

        deselect_all = QPushButton("Deselect All")
        deselect_all.clicked.connect(lambda: self._toggle_all_skills(False))
        button_layout.addWidget(deselect_all)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Skills as checkboxes (in a grid-like layout)
        skills_widget = QWidget()
        skills_layout = QVBoxLayout(skills_widget)
        self.skill_checkboxes = []

        row_layout = None
        for i, skill in enumerate(self.extracted.skills):
            if i % 3 == 0:  # 3 skills per row
                row_layout = QHBoxLayout()
                skills_layout.addLayout(row_layout)

            checkbox = QCheckBox(skill)
            checkbox.setChecked(True)
            self.skill_checkboxes.append(checkbox)
            row_layout.addWidget(checkbox)

        # Fill remaining cells in last row
        if row_layout:
            remaining = len(self.extracted.skills) % 3
            if remaining > 0:
                for _ in range(3 - remaining):
                    row_layout.addStretch()

        layout.addWidget(skills_widget)
        group.setLayout(layout)
        return group

    def _build_certifications_section(self) -> QGroupBox:
        """Build the certifications section."""
        group = QGroupBox(f"Certifications ({len(self.extracted.certifications)} found)")
        layout = QVBoxLayout()

        self.cert_checkboxes = []

        for cert in self.extracted.certifications:
            cert_text = cert.name
            if cert.issuing_organization:
                cert_text += f" - {cert.issuing_organization}"
            if cert.issue_date:
                cert_text += f" ({cert.issue_date})"

            checkbox = QCheckBox(cert_text)
            checkbox.setChecked(True)
            self.cert_checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        group.setLayout(layout)
        return group

    def _toggle_all_skills(self, checked: bool):
        """Toggle all skill checkboxes."""
        for checkbox in self.skill_checkboxes:
            checkbox.setChecked(checked)

    def _import_resume(self):
        """Import the selected resume data."""
        # Update extracted resume with edited contact info
        self.extracted.first_name = self.first_name_edit.text().strip()
        self.extracted.last_name = self.last_name_edit.text().strip()
        self.extracted.email = self.email_edit.text().strip()
        self.extracted.phone = self.phone_edit.text().strip()
        self.extracted.location = self.location_edit.text().strip()
        self.extracted.linkedin_url = self.linkedin_edit.text().strip()
        self.extracted.github_url = self.github_edit.text().strip()
        self.extracted.website_url = self.website_edit.text().strip()

        # Validate required fields
        if not self.extracted.first_name or not self.extracted.last_name:
            QMessageBox.warning(
                self,
                "Missing Information",
                "First name and last name are required."
            )
            return

        if not self.extracted.email:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Email is required."
            )
            return

        # Filter selected items
        selected_jobs = [
            job for i, job in enumerate(self.extracted.jobs)
            if i < len(self.job_checkboxes) and self.job_checkboxes[i].isChecked()
        ]

        selected_edu = [
            edu for i, edu in enumerate(self.extracted.education)
            if i < len(self.edu_checkboxes) and self.edu_checkboxes[i].isChecked()
        ]

        selected_skills = [
            skill for i, skill in enumerate(self.extracted.skills)
            if i < len(self.skill_checkboxes) and self.skill_checkboxes[i].isChecked()
        ]

        selected_certs = [
            cert for i, cert in enumerate(self.extracted.certifications)
            if i < len(self.cert_checkboxes) and self.cert_checkboxes[i].isChecked()
        ]

        # Update extracted resume with selections
        self.extracted.jobs = selected_jobs
        self.extracted.education = selected_edu
        self.extracted.skills = selected_skills
        self.extracted.certifications = selected_certs

        # Show progress dialog
        progress = QProgressDialog("Importing resume data...", None, 0, 0, self)
        progress.setWindowTitle("Importing")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        try:
            # Import using ResumeImporter service
            session = DatabaseManager.get_session()
            importer = ResumeImporter(session)

            profile, stats = importer.import_resume(
                self.extracted,
                profile_id=self.profile_id,
                create_new_profile=(self.profile_id is None)
            )

            progress.close()

            # Show success message
            success_msg = f"Successfully imported resume data!\n\n"
            success_msg += f"Profile: {profile.full_name}\n"
            success_msg += f"Jobs: {stats['jobs_created']}\n"
            success_msg += f"Bullet Points: {stats['bullet_points_created']}\n"
            success_msg += f"Education: {stats['education_created']}\n"
            success_msg += f"Skills: {stats['skills_created']}\n"
            success_msg += f"Certifications: {stats['certifications_created']}\n"

            if stats['errors']:
                success_msg += f"\nWarnings: {len(stats['errors'])} items had issues"

            QMessageBox.information(
                self,
                "Import Successful",
                success_msg
            )

            self.import_successful = True
            self.accept()

        except ResumeImportError as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import resume data:\n\n{str(e)}"
            )
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Import Failed",
                f"An unexpected error occurred:\n\n{str(e)}"
            )

    def was_successful(self) -> bool:
        """Return whether the import was successful."""
        return self.import_successful
