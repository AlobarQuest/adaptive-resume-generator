"""Screen for managing saved job postings."""

from __future__ import annotations

from typing import Optional
import logging
import webbrowser

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QLineEdit,
        QMessageBox,
        QDialog,
        QFormLayout,
        QTextEdit,
        QDialogButtonBox,
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.gui.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class JobPostingDetailDialog(QDialog):
    """Dialog for viewing/editing job posting details."""

    def __init__(self, job_posting: JobPosting, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.job_posting = job_posting

        self.setWindowTitle(f"Job Posting: {job_posting.job_title or 'Untitled'}")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel(f"{self.job_posting.company_name or 'Unknown Company'} - {self.job_posting.job_title or 'Untitled'}")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Form for metadata
        form_layout = QFormLayout()

        self.company_edit = QLineEdit(self.job_posting.company_name or "")
        form_layout.addRow("Company:", self.company_edit)

        self.title_edit = QLineEdit(self.job_posting.job_title or "")
        form_layout.addRow("Job Title:", self.title_edit)

        self.location_edit = QLineEdit(self.job_posting.location or "")
        form_layout.addRow("Location:", self.location_edit)

        self.salary_edit = QLineEdit(self.job_posting.salary_range or "")
        form_layout.addRow("Salary/Pay:", self.salary_edit)

        self.url_edit = QLineEdit(self.job_posting.application_url or "")
        form_layout.addRow("Application URL:", self.url_edit)

        # Date added (read-only)
        date_str = self.job_posting.uploaded_at.strftime("%Y-%m-%d %H:%M") if self.job_posting.uploaded_at else "Unknown"
        date_label = QLabel(date_str)
        form_layout.addRow("Date Added:", date_label)

        # Number of resumes generated (read-only)
        resume_count = len(self.job_posting.tailored_resumes) if self.job_posting.tailored_resumes else 0
        resume_count_label = QLabel(str(resume_count))
        form_layout.addRow("Resumes Generated:", resume_count_label)

        layout.addLayout(form_layout)

        # Notes section
        notes_label = QLabel("Notes:")
        notes_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlainText(self.job_posting.notes or "")
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(self.notes_edit)

        # Job posting text (read-only)
        posting_label = QLabel("Job Posting Text:")
        posting_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(posting_label)

        self.posting_text = QTextEdit()
        self.posting_text.setPlainText(self.job_posting.raw_text or "")
        self.posting_text.setReadOnly(True)
        layout.addWidget(self.posting_text)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_save(self):
        """Save changes to the job posting."""
        try:
            session = DatabaseManager.get_session()

            self.job_posting.company_name = self.company_edit.text().strip() or None
            self.job_posting.job_title = self.title_edit.text().strip() or None
            self.job_posting.location = self.location_edit.text().strip() or None
            self.job_posting.salary_range = self.salary_edit.text().strip() or None
            self.job_posting.application_url = self.url_edit.text().strip() or None
            self.job_posting.notes = self.notes_edit.toPlainText().strip() or None

            session.commit()
            self.accept()

        except Exception as e:
            logger.error(f"Error saving job posting: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save changes:\n{str(e)}")
            session.rollback()


class ManageJobPostingsScreen(BaseScreen):
    """Screen for managing saved job postings."""

    def __init__(self, parent: Optional[QWidget] = None):
        self.all_postings = []
        super().__init__(parent)  # This calls _setup_ui() automatically

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Manage Job Postings")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._load_job_postings)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by company, title, or location...")
        self.search_box.textChanged.connect(self._filter_postings)
        search_layout.addWidget(self.search_box)

        layout.addLayout(search_layout)

        # Table for job postings
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Company", "Job Title", "Location", "Salary", "Date Added", "# Resumes", "Actions"
        ])

        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Company
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Location
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Salary
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Resumes
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Actions

        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(6, 450)  # Increased for Apply Online + Edit + Generate + Delete buttons

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Summary label
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

    def on_screen_shown(self):
        """Called when the screen is shown."""
        logger.info("ManageJobPostingsScreen.on_screen_shown() called")
        self._load_job_postings()

    def _load_job_postings(self):
        """Load all job postings from database."""
        logger.info("_load_job_postings() called - starting job posting query")
        try:
            # Get a fresh session each time
            session = DatabaseManager.get_session()
            logger.info(f"Got database session: {session}")

            # Query all job postings for current profile, ordered by date (newest first)
            self.all_postings = session.query(JobPosting).filter_by(
                profile_id=1  # DEFAULT_PROFILE_ID
            ).order_by(JobPosting.uploaded_at.desc()).all()

            logger.info(f"Query completed - Loaded {len(self.all_postings)} job postings from database")
            if self.all_postings:
                logger.info(f"First posting: company={self.all_postings[0].company_name}, title={self.all_postings[0].job_title}")

            self._display_postings(self.all_postings)
            self.summary_label.setText(f"Total job postings: {len(self.all_postings)}")

        except Exception as e:
            logger.error(f"Error loading job postings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load job postings:\n{str(e)}")

    def _display_postings(self, postings: list[JobPosting]):
        """Display job postings in the table."""
        logger.info(f"_display_postings() called with {len(postings)} postings")
        logger.info(f"Table widget: {self.table}, current row count: {self.table.rowCount()}")
        self.table.setRowCount(0)
        logger.info(f"Table cleared, row count now: {self.table.rowCount()}")

        for row, posting in enumerate(postings):
            logger.info(f"Adding row {row}: {posting.company_name} - {posting.job_title}")
            self.table.insertRow(row)

            # Company
            self.table.setItem(row, 0, QTableWidgetItem(posting.company_name or "Unknown"))

            # Job Title
            self.table.setItem(row, 1, QTableWidgetItem(posting.job_title or "Untitled"))

            # Location
            self.table.setItem(row, 2, QTableWidgetItem(posting.location or ""))

            # Salary
            self.table.setItem(row, 3, QTableWidgetItem(posting.salary_range or ""))

            # Date Added
            date_str = posting.uploaded_at.strftime("%Y-%m-%d") if posting.uploaded_at else ""
            self.table.setItem(row, 4, QTableWidgetItem(date_str))

            # Number of resumes
            resume_count = len(posting.tailored_resumes) if posting.tailored_resumes else 0
            self.table.setItem(row, 5, QTableWidgetItem(str(resume_count)))

            # Actions (buttons)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            # View/Edit button
            view_btn = QPushButton("📝 Edit")
            view_btn.setMinimumWidth(75)
            view_btn.setMinimumHeight(30)
            view_btn.setMaximumHeight(35)
            view_btn.setStyleSheet("QPushButton { padding: 4px 8px; }")
            view_btn.clicked.connect(lambda checked, p=posting: self._on_edit_posting(p))
            actions_layout.addWidget(view_btn)

            # Generate Resume button
            generate_btn = QPushButton("📄 Generate")
            generate_btn.setMinimumWidth(105)
            generate_btn.setMinimumHeight(30)
            generate_btn.setMaximumHeight(35)
            generate_btn.setToolTip("Generate tailored resume for this job posting")
            generate_btn.setStyleSheet("QPushButton { padding: 4px 8px; }")
            generate_btn.clicked.connect(lambda checked, p=posting: self._on_generate_resume(p))
            actions_layout.addWidget(generate_btn)

            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setMinimumWidth(40)
            delete_btn.setMinimumHeight(30)
            delete_btn.setMaximumHeight(35)
            delete_btn.setToolTip("Delete this job posting")
            delete_btn.setStyleSheet("QPushButton { padding: 4px 8px; }")
            delete_btn.clicked.connect(lambda checked, p=posting: self._on_delete_posting(p))
            actions_layout.addWidget(delete_btn)

            # Apply Online button (only if URL is available) - positioned at far right
            if posting.application_url:
                apply_btn = QPushButton("🌐 Apply")
                apply_btn.setMinimumWidth(85)
                apply_btn.setMinimumHeight(30)
                apply_btn.setMaximumHeight(35)
                apply_btn.setToolTip("Apply Online - Open application URL in browser")
                apply_btn.setStyleSheet("QPushButton { background-color: #4a90e2; color: white; font-weight: bold; padding: 4px 8px; }")
                apply_btn.clicked.connect(lambda checked, p=posting: self._on_apply_online(p))
                actions_layout.addWidget(apply_btn)

            self.table.setCellWidget(row, 6, actions_widget)

            # Set row height to accommodate buttons
            self.table.setRowHeight(row, 45)

    def _filter_postings(self):
        """Filter postings based on search text."""
        search_text = self.search_box.text().lower()

        if not search_text:
            self._display_postings(self.all_postings)
            return

        filtered = [
            p for p in self.all_postings
            if search_text in (p.company_name or "").lower()
            or search_text in (p.job_title or "").lower()
            or search_text in (p.location or "").lower()
        ]

        self._display_postings(filtered)
        self.summary_label.setText(f"Showing {len(filtered)} of {len(self.all_postings)} job postings")

    def _on_apply_online(self, posting: JobPosting):
        """Open the application URL in a web browser."""
        if posting.application_url:
            try:
                webbrowser.open(posting.application_url)
                logger.info(f"Opened application URL: {posting.application_url}")
            except Exception as e:
                logger.error(f"Failed to open URL: {e}", exc_info=True)
                QMessageBox.warning(
                    self,
                    "Error Opening URL",
                    f"Could not open the application URL:\n{posting.application_url}\n\nError: {str(e)}"
                )
        else:
            QMessageBox.information(
                self,
                "No URL Available",
                "This job posting does not have an application URL saved."
            )

    def _on_edit_posting(self, posting: JobPosting):
        """Open dialog to edit job posting."""
        dialog = JobPostingDetailDialog(posting, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_job_postings()  # Refresh the list

    def _on_generate_resume(self, posting: JobPosting):
        """Generate a new tailored resume for this job posting."""
        # Emit signal to main window to navigate to upload screen with this posting
        QMessageBox.information(
            self,
            "Generate Resume",
            f"This will navigate to the job posting screen to analyze:\n\n"
            f"{posting.company_name} - {posting.job_title}\n\n"
            f"Feature coming in next update!"
        )

    def _on_delete_posting(self, posting: JobPosting):
        """Delete a job posting."""
        reply = QMessageBox.question(
            self,
            "Delete Job Posting",
            f"Are you sure you want to delete this job posting?\n\n"
            f"{posting.company_name} - {posting.job_title}\n\n"
            f"This will also delete {len(posting.tailored_resumes) if posting.tailored_resumes else 0} associated resume(s).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                session = DatabaseManager.get_session()
                session.delete(posting)
                session.commit()
                self._load_job_postings()  # Refresh
                QMessageBox.information(self, "Success", "Job posting deleted successfully.")

            except Exception as e:
                logger.error(f"Error deleting job posting: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to delete job posting:\n{str(e)}")
                session.rollback()


__all__ = ["ManageJobPostingsScreen"]
