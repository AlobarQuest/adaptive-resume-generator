"""Job posting upload screen with full Phase 4 functionality."""

from __future__ import annotations

from typing import Optional
import logging

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QComboBox,
        QHBoxLayout,
        QScrollArea,
        QFileDialog,
        QTextEdit,
        QDialog,
        QDialogButtonBox,
        QProgressDialog,
        QMessageBox,
        QLineEdit,
        QFormLayout,
        QGroupBox,
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from adaptive_resume.models import Profile
from adaptive_resume.models.base import DEFAULT_PROFILE_ID
from adaptive_resume.services import (
    JobPostingParser,
    NLPAnalyzer,
    MatchingEngine,
    ResumeGenerator,
    JobRequirements,
    ImportedJob,
)
from adaptive_resume.gui.dialogs import JobImportDialog

logger = logging.getLogger(__name__)


class ProcessingWorker(QThread):
    """Background worker for processing job postings."""

    progress = pyqtSignal(str)  # Progress message
    finished = pyqtSignal(object)  # TailoredResume result
    error = pyqtSignal(str)  # Error message

    def __init__(
        self,
        job_text: str,
        profile_id: int,
        accomplishments: list,
        job_title: str = "",
        company_name: str = "",
        location: str = "",
        salary_range: str = "",
        application_url: str = "",
        notes: str = "",
        source: str = "paste",
    ):
        super().__init__()
        self.job_text = job_text
        self.profile_id = profile_id
        self.accomplishments = accomplishments
        self.job_title = job_title
        self.company_name = company_name
        self.location = location
        self.salary_range = salary_range
        self.application_url = application_url
        self.notes = notes
        self.source = source

    def run(self):
        """Process the job posting."""
        try:
            # Step 1: Parse text (already done, but clean it)
            self.progress.emit("Cleaning job posting text...")
            parser = JobPostingParser()
            cleaned_text = parser.clean_text(self.job_text)

            # Step 2: Analyze requirements
            self.progress.emit("Analyzing job requirements...")
            analyzer = NLPAnalyzer()
            requirements = analyzer.analyze(cleaned_text, use_ai=True)

            # Step 3: Generate tailored resume
            self.progress.emit("Matching your experience...")
            generator = ResumeGenerator()

            result = generator.generate_tailored_resume(
                profile_id=self.profile_id,
                accomplishments=self.accomplishments,
                requirements=requirements,
                job_description_text=cleaned_text,
                job_title=self.job_title,
                company_name=self.company_name,
            )

            # Store all metadata in the result for database persistence
            result.raw_job_text = self.job_text
            result.location = self.location
            result.salary_range = self.salary_range
            result.application_url = self.application_url
            result.notes = self.notes
            result.source = self.source

            self.progress.emit("Complete!")
            self.finished.emit(result)

        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            self.error.emit(str(e))


class FileMetadataDialog(QDialog):
    """Dialog for adding metadata to an uploaded job posting file."""

    def __init__(
        self,
        company_name: str = "",
        job_title: str = "",
        location: str = "",
        salary_range: str = "",
        application_url: str = "",
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Add Job Details")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Instructions
        label = QLabel("Review and edit job details extracted from the file:")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        label.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(label)

        # Info label if any fields were auto-filled
        auto_filled = any([company_name, job_title, location, salary_range, application_url])
        if auto_filled:
            info_label = QLabel("✓ Some fields were automatically detected. Please review and edit as needed.")
            info_label.setStyleSheet("color: #4a90e2; font-style: italic; margin-bottom: 10px;")
            layout.addWidget(info_label)

        # Metadata fields form
        form_layout = QFormLayout()

        self.company_edit = QLineEdit(company_name)
        self.company_edit.setPlaceholderText("e.g., Acme Corporation")
        form_layout.addRow("Company:", self.company_edit)

        self.title_edit = QLineEdit(job_title)
        self.title_edit.setPlaceholderText("e.g., Senior Software Engineer")
        form_layout.addRow("Job Title:", self.title_edit)

        self.location_edit = QLineEdit(location)
        self.location_edit.setPlaceholderText("e.g., San Francisco, CA (Remote)")
        form_layout.addRow("Location:", self.location_edit)

        self.salary_edit = QLineEdit(salary_range)
        self.salary_edit.setPlaceholderText("e.g., $120k - $180k")
        form_layout.addRow("Salary/Pay:", self.salary_edit)

        self.url_edit = QLineEdit(application_url)
        self.url_edit.setPlaceholderText("e.g., https://company.com/careers/job-id")
        form_layout.addRow("Application URL:", self.url_edit)

        layout.addLayout(form_layout)

        # Optional notes field
        notes_label = QLabel("Notes (optional):")
        notes_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add any personal notes about this position...")
        self.notes_edit.setMaximumHeight(80)
        layout.addWidget(self.notes_edit)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_company(self) -> str:
        """Get the company name."""
        return self.company_edit.text().strip()

    def get_title(self) -> str:
        """Get the job title."""
        return self.title_edit.text().strip()

    def get_location(self) -> str:
        """Get the location."""
        return self.location_edit.text().strip()

    def get_salary(self) -> str:
        """Get the salary range."""
        return self.salary_edit.text().strip()

    def get_url(self) -> str:
        """Get the application URL."""
        return self.url_edit.text().strip()

    def get_notes(self) -> str:
        """Get the notes."""
        return self.notes_edit.toPlainText().strip()


class PasteTextDialog(QDialog):
    """Dialog for pasting job posting text with metadata fields."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paste Job Posting")
        self.setMinimumSize(800, 700)

        layout = QVBoxLayout(self)

        # Instructions
        label = QLabel("Paste the job posting text and add details:")
        label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(label)

        # Metadata fields group
        metadata_group = QGroupBox("Job Details")
        metadata_layout = QFormLayout()

        self.company_edit = QLineEdit()
        self.company_edit.setPlaceholderText("e.g., Acme Corporation")
        metadata_layout.addRow("Company:", self.company_edit)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("e.g., Senior Software Engineer")
        metadata_layout.addRow("Job Title:", self.title_edit)

        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., San Francisco, CA (Remote)")
        metadata_layout.addRow("Location:", self.location_edit)

        self.salary_edit = QLineEdit()
        self.salary_edit.setPlaceholderText("e.g., $120k - $180k")
        metadata_layout.addRow("Salary/Pay:", self.salary_edit)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("e.g., https://company.com/careers/job-id")
        metadata_layout.addRow("Application URL:", self.url_edit)

        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

        # Job posting text
        text_label = QLabel("Job Posting Text:")
        text_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(text_label)

        # Text edit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Paste job description here...\n\n"
            "Include:\n"
            "• Required skills and qualifications\n"
            "• Responsibilities\n"
            "• Preferred qualifications\n"
            "• Benefits and perks"
        )
        layout.addWidget(self.text_edit)

        # Bottom row: Character count and Extract button
        bottom_row = QHBoxLayout()

        self.char_count_label = QLabel("0 characters")
        self.char_count_label.setStyleSheet("color: #666; font-size: 11px;")
        bottom_row.addWidget(self.char_count_label)

        bottom_row.addStretch()

        extract_btn = QPushButton("📋 Extract Info from Text")
        extract_btn.setToolTip("Automatically extract company, title, location, salary, and URL from the pasted text")
        extract_btn.clicked.connect(self._extract_metadata)
        bottom_row.addWidget(extract_btn)

        layout.addLayout(bottom_row)

        # Connect signal for character count
        self.text_edit.textChanged.connect(self._update_char_count)

        # Optional notes field
        notes_label = QLabel("Notes (optional):")
        notes_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add any personal notes about this position...")
        self.notes_edit.setMaximumHeight(60)
        layout.addWidget(self.notes_edit)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _update_char_count(self):
        """Update character count label."""
        text = self.text_edit.toPlainText()
        count = len(text)
        self.char_count_label.setText(f"{count:,} characters")

    def _extract_metadata(self):
        """Extract metadata from pasted text and populate fields."""
        text = self.text_edit.toPlainText()
        if not text.strip():
            QMessageBox.information(
                self,
                "No Text",
                "Please paste job posting text first before extracting metadata."
            )
            return

        # Use the parser to extract metadata
        parser = JobPostingParser()
        metadata = parser.extract_metadata(text)

        # Only populate empty fields (don't overwrite user input)
        if not self.company_edit.text() and metadata.get('company_name'):
            self.company_edit.setText(metadata['company_name'])

        if not self.title_edit.text() and metadata.get('job_title'):
            self.title_edit.setText(metadata['job_title'])

        if not self.location_edit.text() and metadata.get('location'):
            self.location_edit.setText(metadata['location'])

        if not self.salary_edit.text() and metadata.get('salary_range'):
            self.salary_edit.setText(metadata['salary_range'])

        if not self.url_edit.text() and metadata.get('application_url'):
            self.url_edit.setText(metadata['application_url'])

        # Show feedback
        extracted_fields = [k for k, v in metadata.items() if v]
        if extracted_fields:
            QMessageBox.information(
                self,
                "Extraction Complete",
                f"Successfully extracted: {', '.join(extracted_fields)}"
            )
        else:
            QMessageBox.information(
                self,
                "No Data Found",
                "Could not automatically extract metadata from the text. Please fill in the fields manually."
            )

    def get_text(self) -> str:
        """Get the pasted text."""
        return self.text_edit.toPlainText()

    def get_company(self) -> str:
        """Get the company name."""
        return self.company_edit.text().strip()

    def get_title(self) -> str:
        """Get the job title."""
        return self.title_edit.text().strip()

    def get_location(self) -> str:
        """Get the location."""
        return self.location_edit.text().strip()

    def get_salary(self) -> str:
        """Get the salary range."""
        return self.salary_edit.text().strip()

    def get_url(self) -> str:
        """Get the application URL."""
        return self.url_edit.text().strip()

    def get_notes(self) -> str:
        """Get the notes."""
        return self.notes_edit.toPlainText().strip()


class JobPostingScreen(BaseScreen):
    """Screen for uploading and analyzing job postings."""

    # Signal to notify when tailored resume is ready
    tailored_resume_ready = pyqtSignal(object)  # TailoredResume

    def __init__(
        self,
        profile_service=None,
        job_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.profile_service = profile_service
        self.job_service = job_service
        self.uploaded_file_path: Optional[str] = None
        self.job_posting_text: Optional[str] = None
        self.job_title: str = ""
        self.company_name: str = ""
        # Metadata fields
        self.location: str = ""
        self.salary_range: str = ""
        self.application_url: str = ""
        self.notes: str = ""

        super().__init__(parent)

        # Enable drag-and-drop
        self.setAcceptDrops(True)

    def _setup_ui(self) -> None:
        """Setup the job posting screen UI."""
        # Main layout for the screen
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header = QLabel("Upload Job Posting")
        header.setObjectName("screenTitle")
        layout.addWidget(header)

        # Description
        description = QLabel(
            "Upload a job posting to automatically match your experience and generate a tailored resume."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #ccc; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(description)

        # Upload area
        self.upload_frame = QFrame()
        self.upload_frame.setObjectName("uploadFrame")
        self.upload_frame.setMinimumHeight(250)

        upload_layout = QVBoxLayout(self.upload_frame)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.setSpacing(15)

        self.upload_icon = QLabel("📄")
        self.upload_icon.setStyleSheet("font-size: 48px;")
        self.upload_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(self.upload_icon)

        self.upload_title = QLabel("Upload Job Posting")
        self.upload_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        self.upload_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(self.upload_title)

        upload_text = QLabel("Drag & Drop your file here\nor")
        upload_text.setStyleSheet("color: #999; font-size: 14px;")
        upload_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(upload_text)

        # Buttons in horizontal layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.browse_btn = QPushButton("📁 Browse Files")
        self.browse_btn.setMinimumHeight(40)
        self.browse_btn.setStyleSheet("padding: 10px 20px;")
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        button_layout.addWidget(self.browse_btn)

        self.paste_btn = QPushButton("📋 Paste Text")
        self.paste_btn.setMinimumHeight(40)
        self.paste_btn.setStyleSheet("padding: 10px 20px;")
        self.paste_btn.clicked.connect(self._on_paste_clicked)
        button_layout.addWidget(self.paste_btn)

        self.import_btn = QPushButton("🔗 Import from URL")
        self.import_btn.setMinimumHeight(40)
        self.import_btn.setStyleSheet("padding: 10px 20px;")
        self.import_btn.clicked.connect(self._on_import_clicked)
        button_layout.addWidget(self.import_btn)

        upload_layout.addLayout(button_layout)

        supported_label = QLabel("Supported formats: .txt, .pdf, .docx, or plain text")
        supported_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        supported_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        upload_layout.addWidget(supported_label)

        layout.addWidget(self.upload_frame)

        # Process button
        self.process_btn = QPushButton("🚀 Analyze Job/Generate Tailored Resume")
        self.process_btn.setObjectName("primaryButton")
        self.process_btn.setMinimumHeight(50)
        self.process_btn.setEnabled(False)
        self.process_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.process_btn.clicked.connect(self._on_process_clicked)
        layout.addWidget(self.process_btn)

        layout.addStretch()

        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)

        # Add scroll area to main layout
        main_layout.addWidget(scroll)

    def _on_browse_clicked(self):
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Job Posting File",
            "",
            "Job Posting Files (*.txt *.pdf *.docx);;All Files (*)"
        )

        if file_path:
            self._load_file(file_path)

    def _on_paste_clicked(self):
        """Handle paste button click."""
        dialog = PasteTextDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            text = dialog.get_text()
            if text.strip():
                self.job_posting_text = text
                self.uploaded_file_path = None

                # Get metadata from dialog
                self.company_name = dialog.get_company()
                self.job_title = dialog.get_title()
                self.location = dialog.get_location()
                self.salary_range = dialog.get_salary()
                self.application_url = dialog.get_url()
                self.notes = dialog.get_notes()

                # Fallback: Extract job title and company from text if not provided
                if not self.job_title or not self.company_name:
                    lines = text.split('\n')
                    if len(lines) >= 2:
                        if not self.job_title:
                            self.job_title = lines[0].strip()
                        if not self.company_name:
                            self.company_name = lines[1].strip() if len(lines) > 1 else ""

                self._update_upload_status("Pasted Text", len(text))
                self.process_btn.setEnabled(True)

    def _on_import_clicked(self):
        """Handle import from URL button click."""
        dialog = JobImportDialog(self)
        dialog.job_imported.connect(self._on_job_imported)
        dialog.exec()

    def _on_job_imported(self, imported_data):
        """Handle successful job import."""
        # imported_data can be ImportedJob or List[ImportedJob]
        if isinstance(imported_data, ImportedJob):
            # Single import
            self.job_posting_text = imported_data.description
            self.uploaded_file_path = None
            self._imported_from_url = True

            # Store company and title for processing
            self.company_name = imported_data.company_name or ""
            self.job_title = imported_data.job_title or ""

            # Store location and URL if available
            self.location = getattr(imported_data, 'location', "") or ""
            self.application_url = getattr(imported_data, 'url', "") or ""

            # Initialize other metadata fields
            self.salary_range = ""
            self.notes = ""

            self._update_upload_status(
                f"Imported from {imported_data.source_platform.title()}",
                len(imported_data.description)
            )
            self.process_btn.setEnabled(True)

        elif isinstance(imported_data, list):
            # Bulk import - process first job for now
            # TODO: Add support for batch processing multiple jobs
            if imported_data:
                first_job = imported_data[0]
                self.job_posting_text = first_job.description
                self.uploaded_file_path = None
                self._imported_from_url = True
                self.company_name = first_job.company_name or ""
                self.job_title = first_job.job_title or ""

                # Store location and URL if available
                self.location = getattr(first_job, 'location', "") or ""
                self.application_url = getattr(first_job, 'url', "") or ""

                # Initialize other metadata fields
                self.salary_range = ""
                self.notes = ""

                self._update_upload_status(
                    f"Imported {len(imported_data)} jobs (showing first)",
                    len(first_job.description)
                )
                self.process_btn.setEnabled(True)

    def _load_file(self, file_path: str):
        """Load and parse a file."""
        try:
            parser = JobPostingParser()

            # Validate file first
            is_valid, error = parser.validate_file(file_path)
            if not is_valid:
                QMessageBox.warning(self, "Invalid File", error)
                return

            # Parse file
            self.job_posting_text = parser.parse_file(file_path)
            self.uploaded_file_path = file_path

            # Extract metadata from job posting text
            metadata = parser.extract_metadata(self.job_posting_text)

            # Show metadata dialog with extracted data pre-filled
            metadata_dialog = FileMetadataDialog(
                company_name=metadata.get('company_name', ''),
                job_title=metadata.get('job_title', ''),
                location=metadata.get('location', ''),
                salary_range=metadata.get('salary_range', ''),
                application_url=metadata.get('application_url', ''),
                parent=self
            )

            if metadata_dialog.exec() == QDialog.DialogCode.Accepted:
                # Get metadata from dialog (already pre-filled with extracted data)
                self.company_name = metadata_dialog.get_company()
                self.job_title = metadata_dialog.get_title()
                self.location = metadata_dialog.get_location()
                self.salary_range = metadata_dialog.get_salary()
                self.application_url = metadata_dialog.get_url()
                self.notes = metadata_dialog.get_notes()

                # Update UI
                file_name = file_path.split('/')[-1].split('\\')[-1]
                self._update_upload_status(file_name, len(self.job_posting_text))

                # Enable process button
                self.process_btn.setEnabled(True)
            else:
                # User cancelled, clear the loaded file
                self.job_posting_text = None
                self.uploaded_file_path = None
                self.process_btn.setEnabled(False)

        except Exception as e:
            logger.error(f"Error loading file: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error Loading File",
                f"Failed to load file:\n{str(e)}"
            )

    def _update_upload_status(self, name: str, char_count: int):
        """Update UI to show file/text is loaded."""
        self.upload_icon.setText("✅")
        self.upload_icon.setStyleSheet("font-size: 48px; color: #4a90e2;")
        self.upload_title.setText(f"Loaded: {name}")
        self.upload_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a90e2;")

    def _on_process_clicked(self):
        """Handle process button click."""
        if not self.job_posting_text:
            QMessageBox.warning(self, "No Job Posting", "Please upload a job posting first.")
            return

        # Use default profile (single-user mode)
        profile_id = DEFAULT_PROFILE_ID

        # Load profile accomplishments
        accomplishments = self._load_accomplishments(profile_id)
        if not accomplishments:
            QMessageBox.warning(
                self,
                "No Experience",
                "This profile has no work experience or bullet points.\n"
                "Please add some accomplishments before analyzing a job posting."
            )
            return

        # Create progress dialog
        progress = QProgressDialog("Processing job posting...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Analyzing Job Posting")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # Determine source
        if self.uploaded_file_path:
            source = "file"
        elif hasattr(self, '_imported_from_url') and self._imported_from_url:
            source = "import"
        else:
            source = "paste"

        # Create worker thread
        self.worker = ProcessingWorker(
            job_text=self.job_posting_text,
            profile_id=profile_id,
            accomplishments=accomplishments,
            job_title=self.job_title,
            company_name=self.company_name,
            location=self.location,
            salary_range=self.salary_range,
            application_url=self.application_url,
            notes=self.notes,
            source=source,
        )

        # Connect signals
        self.worker.progress.connect(progress.setLabelText)
        self.worker.finished.connect(lambda result: self._on_processing_complete(result, progress))
        self.worker.error.connect(lambda err: self._on_processing_error(err, progress))
        progress.canceled.connect(self.worker.terminate)

        # Start processing
        self.worker.start()

    def _load_accomplishments(self, profile_id: int):
        """Load all accomplishments for a profile."""
        if not self.job_service:
            return []

        # Get all jobs for this profile
        from adaptive_resume.models import Job

        jobs = (
            self.job_service.session.query(Job)
            .filter(Job.profile_id == profile_id)
            .order_by(Job.is_current.desc(), Job.start_date.desc())
            .all()
        )

        accomplishments = []
        for job in jobs:
            for bullet in job.bullet_points:
                accomplishments.append((bullet, job))

        return accomplishments

    def _on_processing_complete(self, result, progress: QProgressDialog):
        """Handle successful processing."""
        progress.close()

        # Emit signal with result
        self.tailored_resume_ready.emit(result)

    def _on_processing_error(self, error: str, progress: QProgressDialog):
        """Handle processing error."""
        progress.close()

        QMessageBox.critical(
            self,
            "Processing Error",
            f"Failed to process job posting:\n\n{error}"
        )

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop event."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self._load_file(file_path)

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        pass  # No profile combo to update in single-user mode


__all__ = ["JobPostingScreen"]
