"""Dialog for importing job postings from various sources."""

from __future__ import annotations

from typing import Optional, List
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QTextEdit,
        QTabWidget,
        QWidget,
        QGroupBox,
        QFileDialog,
        QMessageBox,
        QCheckBox,
        QProgressBar,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QThread
    from PyQt6.QtWidgets import QApplication
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.services import JobImportService, ImportedJob
from adaptive_resume.gui.database_manager import DatabaseManager


class ImportWorker(QThread):
    """Background worker for importing jobs."""

    finished = pyqtSignal(object, str)  # (ImportedJob or list, error_message)
    progress = pyqtSignal(str)  # Status message

    def __init__(self, service: JobImportService, import_type: str, data: str, user_consent: bool = False):
        super().__init__()
        self.service = service
        self.import_type = import_type
        self.data = data
        self.user_consent = user_consent

    def run(self):
        """Run the import in background."""
        try:
            if self.import_type == 'url':
                self.progress.emit("Fetching job posting from URL...")
                job = self.service.import_from_url(self.data, self.user_consent)
                self.finished.emit(job, "")

            elif self.import_type == 'clipboard':
                self.progress.emit("Parsing clipboard text...")
                job = self.service.import_from_clipboard(self.data)
                self.finished.emit(job, "")

            elif self.import_type == 'csv':
                self.progress.emit("Parsing CSV file...")
                results = self.service.import_bulk_csv(self.data)
                self.finished.emit(results, "")

        except Exception as e:
            self.finished.emit(None, str(e))


class JobImportDialog(QDialog):
    """Dialog for importing job postings from various sources.

    Features:
    - Import from URL (LinkedIn, Indeed, etc.)
    - Import from clipboard (paste text)
    - Bulk import from CSV file
    - Preview and edit before saving
    - User consent for web scraping
    """

    job_imported = pyqtSignal(object)  # Emits ImportedJob or List[ImportedJob]

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.session = DatabaseManager.get_session()
        self.import_service = JobImportService()
        self.import_worker: Optional[ImportWorker] = None
        self.imported_job: Optional[ImportedJob] = None
        self.imported_jobs_bulk: List[ImportedJob] = []

        self.setWindowTitle("Import Job Posting")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Import Job Posting")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "Import job postings from URLs, clipboard, or CSV files. "
            "The imported data can be previewed and edited before saving."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        # Tab widget for different import methods
        self.tabs = QTabWidget()

        # Tab 1: URL Import
        self.url_tab = self._build_url_tab()
        self.tabs.addTab(self.url_tab, "From URL")

        # Tab 2: Clipboard Import
        self.clipboard_tab = self._build_clipboard_tab()
        self.tabs.addTab(self.clipboard_tab, "From Clipboard")

        # Tab 3: CSV Import
        self.csv_tab = self._build_csv_tab()
        self.tabs.addTab(self.csv_tab, "From CSV File")

        layout.addWidget(self.tabs)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px; background: #1a2332; border-radius: 4px;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _build_url_tab(self) -> QWidget:
        """Build the URL import tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Instructions
        instructions = QLabel(
            "Enter a job posting URL from LinkedIn, Indeed, Glassdoor, or other job boards. "
            "The system will attempt to extract job details automatically."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(instructions)

        # URL input
        url_group = QGroupBox("Job Posting URL")
        url_layout = QVBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.linkedin.com/jobs/view/...")
        self.url_input.textChanged.connect(self._on_url_changed)
        url_layout.addWidget(self.url_input)

        # Platform detection
        self.platform_label = QLabel("Platform: Not detected")
        self.platform_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        url_layout.addWidget(self.platform_label)

        url_group.setLayout(url_layout)
        layout.addWidget(url_group)

        # User consent checkbox
        self.consent_checkbox = QCheckBox(
            "I consent to web scraping and confirm that I have permission to access this website "
            "in accordance with its Terms of Service and robots.txt"
        )
        self.consent_checkbox.setStyleSheet("margin: 10px 0;")
        layout.addWidget(self.consent_checkbox)

        # Warning label
        warning = QLabel(
            "⚠️ Note: Some job boards (like LinkedIn) actively prevent automated scraping. "
            "If URL import fails, please use the 'From Clipboard' tab to paste the job text directly."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "background: #3a2a1a; color: #ffa500; padding: 10px; "
            "border-radius: 4px; margin: 10px 0;"
        )
        layout.addWidget(warning)

        # Import button
        import_button = QPushButton("Import from URL")
        import_button.setObjectName("primaryButton")
        import_button.setMinimumHeight(40)
        import_button.setStyleSheet("font-weight: bold;")
        import_button.clicked.connect(self._import_from_url)
        layout.addWidget(import_button)

        layout.addStretch()

        return widget

    def _build_clipboard_tab(self) -> QWidget:
        """Build the clipboard import tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Instructions
        instructions = QLabel(
            "Paste job posting text from any source. The system will attempt to extract "
            "key information like job title, company, location, and requirements."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(instructions)

        # Text input
        text_group = QGroupBox("Job Posting Text")
        text_layout = QVBoxLayout()

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Paste job posting text here...\n\n"
            "Example:\n"
            "Software Engineer - Python\n"
            "Tech Company Inc.\n"
            "San Francisco, CA\n\n"
            "We are looking for a skilled Python developer..."
        )
        self.text_input.setMinimumHeight(250)
        text_layout.addWidget(self.text_input)

        # Paste button
        paste_layout = QHBoxLayout()
        paste_button = QPushButton("Paste from Clipboard")
        paste_button.clicked.connect(self._paste_from_clipboard)
        paste_layout.addWidget(paste_button)
        paste_layout.addStretch()
        text_layout.addLayout(paste_layout)

        text_group.setLayout(text_layout)
        layout.addWidget(text_group)

        # Import button
        import_button = QPushButton("Import from Text")
        import_button.setObjectName("primaryButton")
        import_button.setMinimumHeight(40)
        import_button.setStyleSheet("font-weight: bold;")
        import_button.clicked.connect(self._import_from_clipboard)
        layout.addWidget(import_button)

        layout.addStretch()

        return widget

    def _build_csv_tab(self) -> QWidget:
        """Build the CSV import tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Instructions
        instructions = QLabel(
            "Import multiple job postings from a CSV file. "
            "Expected columns: company_name, job_title, location, salary, description, application_url"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(instructions)

        # CSV format example
        format_group = QGroupBox("CSV Format Example")
        format_layout = QVBoxLayout()

        example_text = QLabel(
            "company_name,job_title,location,salary,description,application_url\n"
            "\"Tech Co\",\"Software Engineer\",\"San Francisco, CA\",\"$120k-$150k\",\"Looking for...\",\"https://...\""
        )
        example_text.setStyleSheet(
            "font-family: monospace; background: #1a2332; padding: 10px; border-radius: 4px;"
        )
        format_layout.addWidget(example_text)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # File selection
        file_layout = QHBoxLayout()

        self.csv_file_label = QLabel("No file selected")
        self.csv_file_label.setStyleSheet("color: #888;")
        file_layout.addWidget(self.csv_file_label)

        file_layout.addStretch()

        select_file_button = QPushButton("Select CSV File...")
        select_file_button.clicked.connect(self._select_csv_file)
        file_layout.addWidget(select_file_button)

        layout.addLayout(file_layout)

        # Import button
        self.csv_import_button = QPushButton("Import from CSV")
        self.csv_import_button.setObjectName("primaryButton")
        self.csv_import_button.setMinimumHeight(40)
        self.csv_import_button.setStyleSheet("font-weight: bold;")
        self.csv_import_button.setEnabled(False)
        self.csv_import_button.clicked.connect(self._import_from_csv)
        layout.addWidget(self.csv_import_button)

        layout.addStretch()

        return widget

    def _on_url_changed(self):
        """Handle URL input change."""
        url = self.url_input.text().strip()
        if url:
            platform = self.import_service.detect_platform(url)
            self.platform_label.setText(f"Platform: {platform.title() if platform else 'Unknown'}")
        else:
            self.platform_label.setText("Platform: Not detected")

    def _paste_from_clipboard(self):
        """Paste text from clipboard."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.text_input.setPlainText(text)

    def _select_csv_file(self):
        """Select a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.csv_file_path = file_path
            self.csv_file_label.setText(Path(file_path).name)
            self.csv_import_button.setEnabled(True)

    def _import_from_url(self):
        """Import job from URL."""
        url = self.url_input.text().strip()

        if not url:
            QMessageBox.warning(self, "No URL", "Please enter a job posting URL.")
            return

        if not self.consent_checkbox.isChecked():
            QMessageBox.warning(
                self,
                "Consent Required",
                "Please confirm that you consent to web scraping and have permission "
                "to access this website."
            )
            return

        # Start import in background
        self._start_import('url', url, user_consent=True)

    def _import_from_clipboard(self):
        """Import job from clipboard text."""
        text = self.text_input.toPlainText().strip()

        if not text:
            QMessageBox.warning(self, "No Text", "Please paste job posting text.")
            return

        # Start import in background
        self._start_import('clipboard', text)

    def _import_from_csv(self):
        """Import jobs from CSV file."""
        if not hasattr(self, 'csv_file_path'):
            QMessageBox.warning(self, "No File", "Please select a CSV file first.")
            return

        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()

            # Start import in background
            self._start_import('csv', csv_content)

        except Exception as e:
            QMessageBox.critical(
                self,
                "File Error",
                f"Failed to read CSV file:\n{str(e)}"
            )

    def _start_import(self, import_type: str, data: str, user_consent: bool = False):
        """Start background import."""
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setVisible(True)
        self.status_label.setText("Importing...")

        # Create worker
        self.import_worker = ImportWorker(
            self.import_service,
            import_type,
            data,
            user_consent
        )
        self.import_worker.progress.connect(self._on_import_progress)
        self.import_worker.finished.connect(self._on_import_finished)
        self.import_worker.start()

    def _on_import_progress(self, message: str):
        """Handle import progress update."""
        self.status_label.setText(message)

    def _on_import_finished(self, result, error: str):
        """Handle import completion."""
        self.progress_bar.setVisible(False)

        if error:
            self.status_label.setStyleSheet(
                "padding: 10px; background: #3a1a1a; color: #ff6666; border-radius: 4px;"
            )
            self.status_label.setText(f"❌ Import failed:\n{error}")
            return

        if result is None:
            self.status_label.setText("❌ Import failed: No data returned")
            return

        # Handle different result types
        if isinstance(result, ImportedJob):
            # Single job import
            self._show_import_preview(result)

        elif isinstance(result, list):
            # Bulk CSV import
            self._show_bulk_import_results(result)

    def _show_import_preview(self, job: ImportedJob):
        """Show preview of imported job."""
        from .job_preview_dialog import JobPreviewDialog

        dialog = JobPreviewDialog(job, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # User confirmed, emit the imported job
            edited_job = dialog.get_edited_job()
            self.job_imported.emit(edited_job)
            self.status_label.setStyleSheet(
                "padding: 10px; background: #1a3a2a; color: #66ff66; border-radius: 4px;"
            )
            self.status_label.setText("✓ Job imported successfully!")

            # Close dialog after short delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, self.accept)

    def _show_bulk_import_results(self, results: List[tuple]):
        """Show results of bulk CSV import."""
        # Count successes and failures
        successful = sum(1 for _, error in results if error is None)
        failed = len(results) - successful

        message = f"CSV Import Results:\n\n"
        message += f"✓ Successful: {successful}\n"
        message += f"❌ Failed: {failed}\n\n"

        if failed > 0:
            message += "Errors:\n"
            for job, error in results:
                if error:
                    message += f"  • {error}\n"

        QMessageBox.information(self, "Import Results", message)

        # If any succeeded, emit them
        if successful > 0:
            successful_jobs = [job for job, error in results if error is None]
            self.job_imported.emit(successful_jobs)
            self.accept()


__all__ = ['JobImportDialog']
