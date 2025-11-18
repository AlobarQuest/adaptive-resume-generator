"""Dialog for quickly adding a new job application.

This dialog provides a streamlined interface for adding new job applications
with essential fields only. For comprehensive editing, use ApplicationDetailDialog.
"""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QTextEdit,
        QComboBox,
        QMessageBox,
        QRadioButton,
        QButtonGroup,
        QGroupBox,
        QWidget,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.gui.database_manager import DatabaseManager
from adaptive_resume.services.application_tracking_service import ApplicationTrackingService
from adaptive_resume.models.job_application import JobApplication
from adaptive_resume.models.job_posting import JobPosting


class AddApplicationDialog(QDialog):
    """Dialog for quickly adding a new job application.

    Features:
    - Essential fields only (company, position, URL, status, priority)
    - Optional job description
    - Optional link to JobPosting
    - Quick add with sensible defaults
    """

    application_created = pyqtSignal(int)  # Emits new application_id

    def __init__(
        self,
        profile_id: int,
        job_posting: Optional[JobPosting] = None,
        parent: Optional[QDialog] = None
    ):
        """Initialize the dialog.

        Args:
            profile_id: Profile ID for the new application
            job_posting: Optional JobPosting to pre-fill data
            parent: Parent widget
        """
        super().__init__(parent)
        self.profile_id = profile_id
        self.job_posting = job_posting
        self.session = DatabaseManager.get_session()
        self.service = ApplicationTrackingService(self.session)

        self.setWindowTitle("Add Job Application")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._build_ui()

        # Pre-fill if job posting provided
        if job_posting:
            self._prefill_from_posting()

    def _build_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("<h2>Add New Job Application</h2>")
        layout.addWidget(title)

        subtitle = QLabel(
            "Choose to track an existing job posting or create a new application."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #888; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        # Mode selection
        mode_group = QGroupBox("Application Source")
        mode_layout = QVBoxLayout()

        self.button_group = QButtonGroup()

        self.existing_radio = QRadioButton("Select from Existing Job Postings")
        self.existing_radio.setToolTip("Choose a job posting you've already imported/uploaded")
        self.button_group.addButton(self.existing_radio, 1)
        mode_layout.addWidget(self.existing_radio)

        self.new_radio = QRadioButton("Create New Application (Manual Entry)")
        self.new_radio.setToolTip("Manually enter job details for a new application")
        self.button_group.addButton(self.new_radio, 2)
        mode_layout.addWidget(self.new_radio)

        # Default to existing if we have postings, otherwise new
        self.existing_radio.setChecked(True)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Connect radio buttons to update UI
        self.existing_radio.toggled.connect(self._on_mode_changed)

        # Container for existing posting selector
        self.existing_container = self._build_existing_selector()
        layout.addWidget(self.existing_container)

        # Container for manual entry form
        self.manual_container = self._build_manual_form()
        layout.addWidget(self.manual_container)

        # Initialize mode
        self._on_mode_changed()

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Create button
        create_button = QPushButton("Create Application")
        create_button.setObjectName("primaryButton")
        create_button.setMinimumHeight(40)
        create_button.setStyleSheet("font-weight: bold; padding: 0 20px;")
        create_button.clicked.connect(self._create_application)
        button_layout.addWidget(create_button)

        # Create and view button
        create_view_button = QPushButton("Create && View Details")
        create_view_button.setMinimumHeight(40)
        create_view_button.clicked.connect(lambda: self._create_application(view_after=True))
        button_layout.addWidget(create_view_button)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def _build_existing_selector(self) -> QWidget:
        """Build the existing job posting selector UI."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info label
        info_label = QLabel(
            "Select a job posting you've previously imported or uploaded. "
            "The application will be pre-filled with job details."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Job posting dropdown
        form = QFormLayout()

        self.posting_combo = QComboBox()
        self.posting_combo.setMinimumHeight(40)

        # Load job postings
        self._load_job_postings()

        form.addRow("Job Posting*:", self.posting_combo)

        # Status and Priority for selected posting
        status_priority_layout = QHBoxLayout()

        # Status
        status_label = QLabel("Status:")
        status_priority_layout.addWidget(status_label)

        self.existing_status_combo = QComboBox()
        for status in JobApplication.VALID_STATUSES:
            self.existing_status_combo.addItem(status.replace('_', ' ').title(), status)

        # Default to "interested" for existing postings
        status_index = self.existing_status_combo.findData(JobApplication.STATUS_INTERESTED)
        if status_index >= 0:
            self.existing_status_combo.setCurrentIndex(status_index)

        status_priority_layout.addWidget(self.existing_status_combo)

        # Priority
        priority_label = QLabel("Priority:")
        status_priority_layout.addWidget(priority_label)

        self.existing_priority_combo = QComboBox()
        for priority in JobApplication.VALID_PRIORITIES:
            self.existing_priority_combo.addItem(priority.title(), priority)

        # Default to "medium"
        priority_index = self.existing_priority_combo.findData(JobApplication.PRIORITY_MEDIUM)
        if priority_index >= 0:
            self.existing_priority_combo.setCurrentIndex(priority_index)

        status_priority_layout.addWidget(self.existing_priority_combo)

        form.addRow("", status_priority_layout)

        layout.addLayout(form)

        # Preview label showing selected posting details
        self.preview_label = QLabel("")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet(
            "background: #2a3a4a; padding: 10px; border-radius: 4px; color: #ccc; margin-top: 10px;"
        )
        self.preview_label.setMinimumHeight(80)
        layout.addWidget(self.preview_label)

        # Connect combo box to update preview
        self.posting_combo.currentIndexChanged.connect(self._update_posting_preview)
        self._update_posting_preview()

        layout.addStretch()

        return widget

    def _build_manual_form(self) -> QWidget:
        """Build the manual entry form UI."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info label
        info_label = QLabel(
            "Enter essential information about the job application. "
            "You can add more details later."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Form
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Company name (required)
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("e.g., Google")
        form.addRow("Company*:", self.company_input)

        # Position title (required)
        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("e.g., Senior Software Engineer")
        form.addRow("Position*:", self.position_input)

        # Job URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        form.addRow("Job URL:", self.url_input)

        # Status
        self.status_combo = QComboBox()
        for status in JobApplication.VALID_STATUSES:
            self.status_combo.addItem(status.replace('_', ' ').title(), status)

        # Default to "discovered"
        default_status = JobApplication.STATUS_DISCOVERED
        status_index = self.status_combo.findData(default_status)
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)

        form.addRow("Status:", self.status_combo)

        # Priority
        self.priority_combo = QComboBox()
        for priority in JobApplication.VALID_PRIORITIES:
            self.priority_combo.addItem(priority.title(), priority)

        # Default to "medium"
        priority_index = self.priority_combo.findData(JobApplication.PRIORITY_MEDIUM)
        if priority_index >= 0:
            self.priority_combo.setCurrentIndex(priority_index)

        form.addRow("Priority:", self.priority_combo)

        # Location (optional)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g., San Francisco, CA or Remote")
        form.addRow("Location:", self.location_input)

        # Salary range (optional)
        self.salary_input = QLineEdit()
        self.salary_input.setPlaceholderText("e.g., $120k-$150k")
        form.addRow("Salary Range:", self.salary_input)

        layout.addLayout(form)

        # Job description (optional)
        desc_label = QLabel("Job Description (optional):")
        layout.addWidget(desc_label)

        self.description_text = QTextEdit()
        self.description_text.setPlaceholderText(
            "Paste the job description here...\n\n"
            "You can copy directly from the job posting."
        )
        self.description_text.setMinimumHeight(150)
        layout.addWidget(self.description_text)

        # Required fields note
        note = QLabel("* Required fields")
        note.setStyleSheet("color: #888; font-size: 11px; margin-top: 10px;")
        layout.addWidget(note)

        return widget

    def _load_job_postings(self):
        """Load available job postings from database."""
        try:
            postings = self.session.query(JobPosting).filter_by(
                profile_id=self.profile_id
            ).order_by(JobPosting.uploaded_at.desc()).all()

            self.posting_combo.clear()
            self.posting_combo.addItem("-- Select a Job Posting --", None)

            for posting in postings:
                display_text = f"{posting.company_name} - {posting.job_title}"
                if posting.location:
                    display_text += f" ({posting.location})"

                self.posting_combo.addItem(display_text, posting.id)

            # If no postings, disable the existing radio button and select manual entry
            if len(postings) == 0:
                self.existing_radio.setEnabled(False)
                self.new_radio.setChecked(True)
                info_text = "No job postings available. Please use manual entry or upload a job posting first."
                self.posting_combo.setToolTip(info_text)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load job postings:\n{str(e)}"
            )

    def _update_posting_preview(self):
        """Update the preview label with selected posting details."""
        posting_id = self.posting_combo.currentData()

        if not posting_id:
            self.preview_label.setText("No job posting selected")
            return

        try:
            posting = self.session.query(JobPosting).filter_by(id=posting_id).first()

            if not posting:
                self.preview_label.setText("Job posting not found")
                return

            preview_text = f"<b>{posting.company_name} - {posting.job_title}</b><br/>"

            if posting.location:
                preview_text += f"📍 {posting.location}<br/>"

            if posting.salary_range:
                preview_text += f"💰 {posting.salary_range}<br/>"

            if posting.application_url:
                preview_text += f"🔗 <a href='{posting.application_url}'>{posting.application_url[:50]}...</a><br/>"

            preview_text += f"<br/><small>Uploaded: {posting.uploaded_at.strftime('%Y-%m-%d')}</small>"

            self.preview_label.setText(preview_text)
            self.preview_label.setOpenExternalLinks(True)

        except Exception as e:
            self.preview_label.setText(f"Error loading preview: {str(e)}")

    def _on_mode_changed(self):
        """Handle mode selection change."""
        is_existing = self.existing_radio.isChecked()

        self.existing_container.setVisible(is_existing)
        self.manual_container.setVisible(not is_existing)

    def _prefill_from_posting(self):
        """Pre-fill form from JobPosting."""
        if not self.job_posting:
            return

        self.company_input.setText(self.job_posting.company or "")
        self.position_input.setText(self.job_posting.title or "")
        self.url_input.setText(self.job_posting.source_url or "")

        if self.job_posting.raw_text:
            self.description_text.setPlainText(self.job_posting.raw_text)

        # If we have a job posting, default to "interested" status
        status_index = self.status_combo.findData(JobApplication.STATUS_INTERESTED)
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)

    def _create_application(self, view_after: bool = False):
        """Create the application.

        Args:
            view_after: If True, open detail dialog after creation
        """
        is_existing = self.existing_radio.isChecked()

        if is_existing:
            # Mode: Select from existing job posting
            return self._create_from_existing_posting(view_after)
        else:
            # Mode: Manual entry
            return self._create_from_manual_entry(view_after)

    def _create_from_existing_posting(self, view_after: bool = False):
        """Create application from selected job posting.

        Args:
            view_after: If True, open detail dialog after creation
        """
        # Validate job posting selection
        posting_id = self.posting_combo.currentData()

        if not posting_id:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a job posting from the dropdown."
            )
            self.posting_combo.setFocus()
            return

        try:
            # Fetch the job posting
            posting = self.session.query(JobPosting).filter_by(id=posting_id).first()

            if not posting:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Selected job posting not found in database."
                )
                return

            # Create application linked to posting
            app = self.service.create_application(
                profile_id=self.profile_id,
                company_name=posting.company_name,
                position_title=posting.job_title,
                job_description=posting.raw_text or None,
                job_url=posting.application_url or None,
                job_posting_id=posting.id,
                status=self.existing_status_combo.currentData(),
                priority=self.existing_priority_combo.currentData(),
                location=posting.location or None,
                salary_range=posting.salary_range or None,
            )

            self.application_created.emit(app.id)

            # Show confirmation
            QMessageBox.information(
                self,
                "Application Created",
                f"Successfully created application for {posting.company_name} - {posting.job_title}"
            )

            # If view_after, open detail dialog
            if view_after:
                from .application_detail_dialog import ApplicationDetailDialog

                detail_dialog = ApplicationDetailDialog(app.id, parent=self.parent())
                detail_dialog.exec()

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Create Error",
                f"Failed to create application:\n{str(e)}"
            )

    def _create_from_manual_entry(self, view_after: bool = False):
        """Create application from manual form entry.

        Args:
            view_after: If True, open detail dialog after creation
        """
        # Validate required fields
        company = self.company_input.text().strip()
        position = self.position_input.text().strip()

        if not company:
            QMessageBox.warning(
                self,
                "Missing Company",
                "Please enter the company name."
            )
            self.company_input.setFocus()
            return

        if not position:
            QMessageBox.warning(
                self,
                "Missing Position",
                "Please enter the position title."
            )
            self.position_input.setFocus()
            return

        try:
            # Create application
            job_posting_id = self.job_posting.id if self.job_posting else None

            app = self.service.create_application(
                profile_id=self.profile_id,
                company_name=company,
                position_title=position,
                job_description=self.description_text.toPlainText().strip() or None,
                job_url=self.url_input.text().strip() or None,
                job_posting_id=job_posting_id,
                status=self.status_combo.currentData(),
                priority=self.priority_combo.currentData(),
                location=self.location_input.text().strip() or None,
                salary_range=self.salary_input.text().strip() or None,
            )

            self.application_created.emit(app.id)

            # Show confirmation
            QMessageBox.information(
                self,
                "Application Created",
                f"Successfully created application for {company} - {position}"
            )

            # If view_after, open detail dialog
            if view_after:
                from .application_detail_dialog import ApplicationDetailDialog

                detail_dialog = ApplicationDetailDialog(app.id, parent=self.parent())
                detail_dialog.exec()

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Create Error",
                f"Failed to create application:\n{str(e)}"
            )


__all__ = ['AddApplicationDialog']
