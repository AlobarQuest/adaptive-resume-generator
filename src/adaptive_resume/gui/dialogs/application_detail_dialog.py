"""Dialog for viewing and editing job application details.

Provides comprehensive view and editing capabilities for all application fields:
- Basic information (company, position, description, URL)
- Status and priority management
- Timeline tracking (dates for all lifecycle stages)
- Contact information (hiring manager, recruiter)
- Interview management
- Follow-up scheduling
- Notes and metrics
"""

from __future__ import annotations

from typing import Optional
from datetime import date, datetime

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
        QComboBox,
        QDateEdit,
        QTabWidget,
        QWidget,
        QGroupBox,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QMessageBox,
        QCheckBox,
        QSpinBox,
    )
    from PyQt6.QtCore import Qt, QDate, pyqtSignal
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.gui.database_manager import DatabaseManager
from adaptive_resume.services.application_tracking_service import ApplicationTrackingService
from adaptive_resume.models.job_application import JobApplication


class ApplicationDetailDialog(QDialog):
    """Dialog for viewing and editing job application details.

    Features:
    - Comprehensive view of all application data
    - In-place editing with save/cancel
    - Status and priority management
    - Interview tracking
    - Contact management
    - Follow-up scheduling
    - Timeline visualization
    - Metrics display
    """

    application_updated = pyqtSignal(int)  # Emits application_id

    def __init__(
        self,
        application_id: int,
        parent: Optional[QWidget] = None,
        read_only: bool = False
    ):
        """Initialize the dialog.

        Args:
            application_id: Application ID to display/edit
            parent: Parent widget
            read_only: If True, editing is disabled
        """
        super().__init__(parent)
        self.application_id = application_id
        self.read_only = read_only
        self.session = DatabaseManager.get_session()
        self.service = ApplicationTrackingService(self.session)

        # Load application
        self.application = self.service.get_application(application_id)
        if not self.application:
            raise ValueError(f"Application {application_id} not found")

        self.setWindowTitle(f"Application: {self.application.company_name}")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Header with title
        header = self._build_header()
        layout.addWidget(header)

        # Tab widget for different sections
        self.tabs = QTabWidget()

        # Basic Info tab
        self.basic_tab = self._build_basic_tab()
        self.tabs.addTab(self.basic_tab, "📋 Basic Info")

        # Timeline tab
        self.timeline_tab = self._build_timeline_tab()
        self.tabs.addTab(self.timeline_tab, "📅 Timeline")

        # Contacts tab
        self.contacts_tab = self._build_contacts_tab()
        self.tabs.addTab(self.contacts_tab, "👥 Contacts")

        # Interviews tab
        self.interviews_tab = self._build_interviews_tab()
        self.tabs.addTab(self.interviews_tab, "🎤 Interviews")

        # Notes & Details tab
        self.notes_tab = self._build_notes_tab()
        self.tabs.addTab(self.notes_tab, "📝 Notes")

        # Metrics tab
        self.metrics_tab = self._build_metrics_tab()
        self.tabs.addTab(self.metrics_tab, "📊 Metrics")

        layout.addWidget(self.tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        if not self.read_only:
            save_button = QPushButton("Save Changes")
            save_button.setObjectName("primaryButton")
            save_button.setMinimumHeight(40)
            save_button.clicked.connect(self._save)
            button_layout.addWidget(save_button)

        cancel_button = QPushButton("Close" if self.read_only else "Cancel")
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def _build_header(self) -> QWidget:
        """Build header with company and position."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Company and position
        company_label = QLabel(f"<h2>{self.application.company_name}</h2>")
        layout.addWidget(company_label)

        position_label = QLabel(f"<b>{self.application.position_title}</b>")
        position_label.setStyleSheet("font-size: 14px; color: #b0b0b0;")
        layout.addWidget(position_label)

        # Status and priority
        info_layout = QHBoxLayout()

        status_label = QLabel(f"Status: <b>{self.application.status.replace('_', ' ').title()}</b>")
        info_layout.addWidget(status_label)

        if self.application.priority:
            priority_color = {
                'high': '#ff6666',
                'medium': '#ffaa66',
                'low': '#66ff66'
            }.get(self.application.priority, '#888')

            priority_label = QLabel(f"Priority: <b style='color:{priority_color}'>{self.application.priority.title()}</b>")
            info_layout.addWidget(priority_label)

        info_layout.addStretch()

        layout.addLayout(info_layout)

        return widget

    def _build_basic_tab(self) -> QWidget:
        """Build basic information tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Company name
        self.company_input = QLineEdit()
        self.company_input.setReadOnly(self.read_only)
        layout.addRow("Company:", self.company_input)

        # Position title
        self.position_input = QLineEdit()
        self.position_input.setReadOnly(self.read_only)
        layout.addRow("Position:", self.position_input)

        # Job URL
        self.url_input = QLineEdit()
        self.url_input.setReadOnly(self.read_only)
        layout.addRow("Job URL:", self.url_input)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.setEnabled(not self.read_only)
        for status in JobApplication.VALID_STATUSES:
            self.status_combo.addItem(status.replace('_', ' ').title(), status)
        layout.addRow("Status:", self.status_combo)

        # Substatus
        self.substatus_input = QLineEdit()
        self.substatus_input.setReadOnly(self.read_only)
        self.substatus_input.setPlaceholderText("e.g., phone_screen, technical, onsite")
        layout.addRow("Substatus:", self.substatus_input)

        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.setEnabled(not self.read_only)
        for priority in JobApplication.VALID_PRIORITIES:
            self.priority_combo.addItem(priority.title(), priority)
        layout.addRow("Priority:", self.priority_combo)

        # Application method
        self.method_input = QLineEdit()
        self.method_input.setReadOnly(self.read_only)
        self.method_input.setPlaceholderText("e.g., company_site, linkedin, indeed")
        layout.addRow("Application Method:", self.method_input)

        # Location
        self.location_input = QLineEdit()
        self.location_input.setReadOnly(self.read_only)
        layout.addRow("Location:", self.location_input)

        # Remote option
        self.remote_combo = QComboBox()
        self.remote_combo.setEnabled(not self.read_only)
        self.remote_combo.addItem("Unknown", None)
        self.remote_combo.addItem("Remote", True)
        self.remote_combo.addItem("On-site", False)
        layout.addRow("Remote Option:", self.remote_combo)

        # Salary range
        self.salary_input = QLineEdit()
        self.salary_input.setReadOnly(self.read_only)
        self.salary_input.setPlaceholderText("e.g., $120k-$150k")
        layout.addRow("Salary Range:", self.salary_input)

        # Referral source
        self.referral_input = QLineEdit()
        self.referral_input.setReadOnly(self.read_only)
        layout.addRow("Referral Source:", self.referral_input)

        # Job description
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(self.read_only)
        self.description_text.setMinimumHeight(150)
        layout.addRow("Job Description:", self.description_text)

        return widget

    def _build_timeline_tab(self) -> QWidget:
        """Build timeline tab with all date fields."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Discovered date
        self.discovered_date = QDateEdit()
        self.discovered_date.setCalendarPopup(True)
        self.discovered_date.setEnabled(not self.read_only)
        self.discovered_date.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("Discovered:", self.discovered_date)

        # Application date
        self.application_date = QDateEdit()
        self.application_date.setCalendarPopup(True)
        self.application_date.setEnabled(not self.read_only)
        self.application_date.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("Applied:", self.application_date)

        # First response date
        self.response_date = QDateEdit()
        self.response_date.setCalendarPopup(True)
        self.response_date.setEnabled(not self.read_only)
        self.response_date.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("First Response:", self.response_date)

        # Offer date
        self.offer_date = QDateEdit()
        self.offer_date.setCalendarPopup(True)
        self.offer_date.setEnabled(not self.read_only)
        self.offer_date.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("Offer Date:", self.offer_date)

        # Acceptance date
        self.acceptance_date = QDateEdit()
        self.acceptance_date.setCalendarPopup(True)
        self.acceptance_date.setEnabled(not self.read_only)
        self.acceptance_date.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("Acceptance Date:", self.acceptance_date)

        # Rejection date
        self.rejection_date = QDateEdit()
        self.rejection_date.setCalendarPopup(True)
        self.rejection_date.setEnabled(not self.read_only)
        self.rejection_date.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("Rejection Date:", self.rejection_date)

        # Last contact date
        self.last_contact_date = QDateEdit()
        self.last_contact_date.setCalendarPopup(True)
        self.last_contact_date.setEnabled(not self.read_only)
        self.last_contact_date.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("Last Contact:", self.last_contact_date)

        # Next follow-up date
        self.followup_date = QDateEdit()
        self.followup_date.setCalendarPopup(True)
        self.followup_date.setEnabled(not self.read_only)
        self.followup_date.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("Next Follow-up:", self.followup_date)

        return widget

    def _build_contacts_tab(self) -> QWidget:
        """Build contacts tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Contact person
        self.contact_person_input = QLineEdit()
        self.contact_person_input.setReadOnly(self.read_only)
        layout.addRow("Contact Person:", self.contact_person_input)

        # Contact email
        self.contact_email_input = QLineEdit()
        self.contact_email_input.setReadOnly(self.read_only)
        layout.addRow("Contact Email:", self.contact_email_input)

        # Contact phone
        self.contact_phone_input = QLineEdit()
        self.contact_phone_input.setReadOnly(self.read_only)
        layout.addRow("Contact Phone:", self.contact_phone_input)

        layout.addRow(QLabel(""))  # Spacer

        # Recruiter name
        self.recruiter_name_input = QLineEdit()
        self.recruiter_name_input.setReadOnly(self.read_only)
        layout.addRow("Recruiter Name:", self.recruiter_name_input)

        # Recruiter email
        self.recruiter_email_input = QLineEdit()
        self.recruiter_email_input.setReadOnly(self.read_only)
        layout.addRow("Recruiter Email:", self.recruiter_email_input)

        return widget

    def _build_interviews_tab(self) -> QWidget:
        """Build interviews tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Interview count display
        self.interview_count_label = QLabel()
        self.interview_count_label.setStyleSheet("font-size: 13px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.interview_count_label)

        # Interviews table
        self.interviews_table = QTableWidget()
        self.interviews_table.setColumnCount(3)
        self.interviews_table.setHorizontalHeaderLabels(["Date", "Type", "Notes"])
        self.interviews_table.horizontalHeader().setStretchLastSection(True)
        self.interviews_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.interviews_table)

        # Add interview button
        if not self.read_only:
            add_interview_btn = QPushButton("+ Add Interview")
            add_interview_btn.clicked.connect(self._add_interview)
            layout.addWidget(add_interview_btn)

        return widget

    def _build_notes_tab(self) -> QWidget:
        """Build notes tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        notes_label = QLabel("<b>Notes:</b>")
        layout.addWidget(notes_label)

        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(self.read_only)
        self.notes_text.setMinimumHeight(400)
        layout.addWidget(self.notes_text)

        return widget

    def _build_metrics_tab(self) -> QWidget:
        """Build metrics tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Days since application
        self.days_since_label = QLabel()
        layout.addRow("Days Since Application:", self.days_since_label)

        # Response time
        self.response_time_label = QLabel()
        layout.addRow("Response Time (days):", self.response_time_label)

        # Interview count
        self.interview_count_metric_label = QLabel()
        layout.addRow("Interview Count:", self.interview_count_metric_label)

        # Time to outcome
        self.time_to_outcome_label = QLabel()
        layout.addRow("Time to Outcome (days):", self.time_to_outcome_label)

        # Is active
        self.is_active_label = QLabel()
        layout.addRow("Status:", self.is_active_label)

        # Needs follow-up
        self.needs_followup_label = QLabel()
        layout.addRow("Follow-up Status:", self.needs_followup_label)

        # Created/Updated timestamps
        self.created_label = QLabel()
        layout.addRow("Created:", self.created_label)

        self.updated_label = QLabel()
        layout.addRow("Last Updated:", self.updated_label)

        return widget

    def _load_data(self):
        """Load application data into form fields."""
        app = self.application

        # Basic info
        self.company_input.setText(app.company_name or "")
        self.position_input.setText(app.position_title or "")
        self.url_input.setText(app.job_url or "")

        # Set status
        status_index = self.status_combo.findData(app.status)
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)

        self.substatus_input.setText(app.substatus or "")

        # Set priority
        priority_index = self.priority_combo.findData(app.priority or 'medium')
        if priority_index >= 0:
            self.priority_combo.setCurrentIndex(priority_index)

        self.method_input.setText(app.application_method or "")
        self.location_input.setText(app.location or "")

        # Remote option
        if app.remote_option is None:
            self.remote_combo.setCurrentIndex(0)
        elif app.remote_option:
            self.remote_combo.setCurrentIndex(1)
        else:
            self.remote_combo.setCurrentIndex(2)

        self.salary_input.setText(app.salary_range or "")
        self.referral_input.setText(app.referral_source or "")
        self.description_text.setPlainText(app.job_description or "")

        # Timeline
        self._set_date_field(self.discovered_date, app.discovered_date)
        self._set_date_field(self.application_date, app.application_date)
        self._set_date_field(self.response_date, app.first_response_date)
        self._set_date_field(self.offer_date, app.offer_date)
        self._set_date_field(self.acceptance_date, app.acceptance_date)
        self._set_date_field(self.rejection_date, app.rejection_date)
        self._set_date_field(self.last_contact_date, app.last_contact_date)
        self._set_date_field(self.followup_date, app.next_followup_date)

        # Contacts
        self.contact_person_input.setText(app.contact_person or "")
        self.contact_email_input.setText(app.contact_email or "")
        self.contact_phone_input.setText(app.contact_phone or "")
        self.recruiter_name_input.setText(app.recruiter_name or "")
        self.recruiter_email_input.setText(app.recruiter_email or "")

        # Interviews
        self._load_interviews()

        # Notes
        self.notes_text.setPlainText(app.notes or "")

        # Metrics
        self._load_metrics()

    def _set_date_field(self, date_edit: QDateEdit, value: Optional[date]):
        """Set date field value, clearing if None."""
        if value:
            date_edit.setDate(QDate(value.year, value.month, value.day))
        else:
            date_edit.setDate(QDate(2000, 1, 1))
            date_edit.setSpecialValueText("Not set")
            date_edit.setMinimumDate(QDate(2000, 1, 1))

    def _get_date_field(self, date_edit: QDateEdit) -> Optional[date]:
        """Get date from date field, returning None if not set."""
        qdate = date_edit.date()
        if qdate.year() == 2000 and qdate.month() == 1 and qdate.day() == 1:
            return None
        return date(qdate.year(), qdate.month(), qdate.day())

    def _load_interviews(self):
        """Load interviews into table."""
        interviews = self.application.get_interviews()

        self.interview_count_label.setText(f"Total Interviews: {len(interviews)}")

        self.interviews_table.setRowCount(0)
        for i, interview in enumerate(interviews):
            self.interviews_table.insertRow(i)

            # Date
            interview_date = interview.get('date', '')
            self.interviews_table.setItem(i, 0, QTableWidgetItem(interview_date))

            # Type
            interview_type = interview.get('type', 'general')
            self.interviews_table.setItem(i, 1, QTableWidgetItem(interview_type))

            # Notes
            notes = interview.get('notes', '')
            self.interviews_table.setItem(i, 2, QTableWidgetItem(notes))

    def _load_metrics(self):
        """Load metrics."""
        app = self.application

        # Days since application
        days_since = app.days_since_application
        self.days_since_label.setText(f"{days_since} days" if days_since is not None else "N/A")

        # Response time
        response_time = app.response_time_days
        self.response_time_label.setText(f"{response_time} days" if response_time is not None else "N/A")

        # Interview count
        self.interview_count_metric_label.setText(str(app.interview_count or 0))

        # Time to outcome
        time_to_outcome = app.total_time_to_outcome_days
        self.time_to_outcome_label.setText(f"{time_to_outcome} days" if time_to_outcome is not None else "N/A")

        # Is active
        self.is_active_label.setText("Active" if app.is_active else "Inactive")

        # Needs follow-up
        self.needs_followup_label.setText("Follow-up Due!" if app.needs_follow_up else "No follow-up due")

        # Timestamps
        if app.created_at:
            self.created_label.setText(app.created_at.strftime("%Y-%m-%d %H:%M:%S"))

        if app.updated_at:
            self.updated_label.setText(app.updated_at.strftime("%Y-%m-%d %H:%M:%S"))

    def _add_interview(self):
        """Add new interview."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDateEdit, QLineEdit, QTextEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Interview")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        # Interview date
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Interview Date:", date_edit)

        # Interview type
        type_input = QLineEdit()
        type_input.setPlaceholderText("e.g., phone_screen, technical, onsite, final")
        form.addRow("Interview Type:", type_input)

        # Notes
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(150)
        form.addRow("Notes:", notes_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Add Interview")
        save_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            qdate = date_edit.date()
            interview_date = date(qdate.year(), qdate.month(), qdate.day())
            interview_type = type_input.text().strip() or "general"
            notes = notes_input.toPlainText().strip()

            # Add to application
            self.application.add_interview(interview_date, interview_type, notes)

            # Reload interviews display
            self._load_interviews()

    def _save(self):
        """Save changes to application."""
        try:
            # Basic info
            updates = {
                'company_name': self.company_input.text().strip() or None,
                'position_title': self.position_input.text().strip() or None,
                'job_url': self.url_input.text().strip() or None,
                'status': self.status_combo.currentData(),
                'substatus': self.substatus_input.text().strip() or None,
                'priority': self.priority_combo.currentData(),
                'application_method': self.method_input.text().strip() or None,
                'location': self.location_input.text().strip() or None,
                'salary_range': self.salary_input.text().strip() or None,
                'referral_source': self.referral_input.text().strip() or None,
                'job_description': self.description_text.toPlainText().strip() or None,
            }

            # Remote option
            remote_idx = self.remote_combo.currentIndex()
            if remote_idx == 0:
                updates['remote_option'] = None
            elif remote_idx == 1:
                updates['remote_option'] = True
            else:
                updates['remote_option'] = False

            # Timeline dates
            updates['discovered_date'] = self._get_date_field(self.discovered_date)
            updates['application_date'] = self._get_date_field(self.application_date)
            updates['first_response_date'] = self._get_date_field(self.response_date)
            updates['offer_date'] = self._get_date_field(self.offer_date)
            updates['acceptance_date'] = self._get_date_field(self.acceptance_date)
            updates['rejection_date'] = self._get_date_field(self.rejection_date)
            updates['last_contact_date'] = self._get_date_field(self.last_contact_date)
            updates['next_followup_date'] = self._get_date_field(self.followup_date)

            # Contacts
            updates['contact_person'] = self.contact_person_input.text().strip() or None
            updates['contact_email'] = self.contact_email_input.text().strip() or None
            updates['contact_phone'] = self.contact_phone_input.text().strip() or None
            updates['recruiter_name'] = self.recruiter_name_input.text().strip() or None
            updates['recruiter_email'] = self.recruiter_email_input.text().strip() or None

            # Notes
            updates['notes'] = self.notes_text.toPlainText().strip() or None

            # Update via service
            self.service.update_application(self.application_id, **updates)

            # Recalculate metrics if needed
            app = self.service.get_application(self.application_id)
            if app:
                app.calculate_response_time()
                app.calculate_time_to_outcome()
                self.session.commit()

            self.application_updated.emit(self.application_id)
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save application:\n{str(e)}"
            )


__all__ = ['ApplicationDetailDialog']
