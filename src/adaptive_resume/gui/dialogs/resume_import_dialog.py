"""Dialog for importing a resume file and extracting structured data."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QFileDialog,
        QTextEdit,
        QMessageBox,
        QProgressDialog,
        QWidget,
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QDragEnterEvent, QDropEvent
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.services import (
    ResumeParser,
    ResumeExtractor,
    ExtractedResume
)


class ResumeExtractionWorker(QThread):
    """Background worker for parsing and extracting resume data."""

    finished = pyqtSignal(object)  # Emits ExtractedResume
    error = pyqtSignal(str)  # Emits error message
    progress = pyqtSignal(str)  # Emits progress message

    def __init__(self, file_path: str, use_ai: bool = False):
        super().__init__()
        self.file_path = file_path
        self.use_ai = use_ai

    def run(self):
        """Execute resume parsing and extraction."""
        try:
            # Step 1: Parse resume file
            self.progress.emit("Parsing resume file...")
            parser = ResumeParser()
            sections = parser.parse_resume_with_sections(self.file_path)

            # Step 2: Extract structured data
            self.progress.emit("Extracting information...")
            extractor = ResumeExtractor()
            extracted = extractor.extract(sections, use_ai=self.use_ai)

            # Step 3: Done
            self.progress.emit("Extraction complete!")
            self.finished.emit(extracted)

        except Exception as e:
            self.error.emit(f"Failed to process resume: {str(e)}")


class ResumeImportDialog(QDialog):
    """Dialog for selecting and processing a resume file.

    This dialog allows users to:
    - Browse for a resume file (PDF, DOCX, TXT)
    - Drag and drop a resume file
    - Process the file to extract structured data
    - Preview extracted data (opens ResumePreviewDialog)
    """

    def __init__(self, parent: Optional[QWidget] = None, use_ai: bool = False):
        super().__init__(parent)
        self.use_ai = use_ai
        self.extracted_resume: Optional[ExtractedResume] = None
        self.selected_file: Optional[str] = None

        self.setWindowTitle("Import Resume")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setAcceptDrops(True)

        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Import Resume")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Select a resume file to import. Supported formats: PDF, DOCX, TXT.\n"
            "The system will extract contact information, work experience, education, skills, and certifications."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("margin-bottom: 20px;")
        layout.addWidget(instructions)

        # File selection area
        file_area = QLabel("No file selected")
        file_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_area.setStyleSheet(
            "border: 2px dashed #ccc; "
            "border-radius: 5px; "
            "padding: 40px; "
            "background-color: #f9f9f9; "
            "min-height: 150px;"
        )
        file_area.setWordWrap(True)
        self.file_label = file_area
        layout.addWidget(file_area)

        # Drag and drop hint
        drop_hint = QLabel("Drag and drop a resume file here, or click Browse below")
        drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_hint.setStyleSheet("color: #666; font-size: 12px; margin-top: 5px;")
        layout.addWidget(drop_hint)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        browse_button = QPushButton("Browse Files...")
        browse_button.clicked.connect(self._browse_file)
        button_layout.addWidget(browse_button)

        self.process_button = QPushButton("Process Resume")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self._process_resume)
        self.process_button.setStyleSheet("font-weight: bold;")
        button_layout.addWidget(self.process_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # Status/Log area (hidden by default)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        self.log_area.setVisible(False)
        layout.addWidget(self.log_area)

    def _browse_file(self):
        """Open file browser to select a resume file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Resume File",
            "",
            "Resume Files (*.pdf *.docx *.txt);;All Files (*.*)"
        )

        if file_path:
            self._set_file(file_path)

    def _set_file(self, file_path: str):
        """Set the selected file and update UI."""
        self.selected_file = file_path
        file_name = Path(file_path).name

        self.file_label.setText(
            f"Selected file:\n{file_name}\n\n"
            f"Click 'Process Resume' to extract information"
        )
        self.process_button.setEnabled(True)

    def _process_resume(self):
        """Process the selected resume file."""
        if not self.selected_file:
            return

        # Show progress dialog
        progress = QProgressDialog("Processing resume...", None, 0, 0, self)
        progress.setWindowTitle("Processing")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # Create and start worker thread
        self.worker = ResumeExtractionWorker(self.selected_file, self.use_ai)
        self.worker.progress.connect(lambda msg: progress.setLabelText(msg))
        self.worker.finished.connect(lambda result: self._on_extraction_complete(result, progress))
        self.worker.error.connect(lambda error: self._on_extraction_error(error, progress))
        self.worker.start()

    def _on_extraction_complete(self, extracted: ExtractedResume, progress: QProgressDialog):
        """Handle successful extraction."""
        progress.close()
        self.extracted_resume = extracted

        # Show summary
        summary = self._get_extraction_summary(extracted)
        QMessageBox.information(
            self,
            "Extraction Complete",
            f"Successfully extracted resume data:\n\n{summary}\n\n"
            f"Click OK to review and import the data."
        )

        # Close this dialog and signal success
        self.accept()

    def _on_extraction_error(self, error: str, progress: QProgressDialog):
        """Handle extraction error."""
        progress.close()
        QMessageBox.critical(
            self,
            "Extraction Failed",
            f"Failed to process resume:\n\n{error}\n\n"
            f"Please try a different file or check the file format."
        )

    def _get_extraction_summary(self, extracted: ExtractedResume) -> str:
        """Generate a summary of extracted data."""
        parts = []

        if extracted.first_name or extracted.last_name:
            name = f"{extracted.first_name} {extracted.last_name}".strip()
            parts.append(f"Name: {name}")

        if extracted.email:
            parts.append(f"Email: {extracted.email}")

        parts.append(f"Jobs: {len(extracted.jobs)}")
        parts.append(f"Education: {len(extracted.education)}")
        parts.append(f"Skills: {len(extracted.skills)}")
        parts.append(f"Certifications: {len(extracted.certifications)}")

        if extracted.extraction_method:
            method = extracted.extraction_method.title()
            parts.append(f"\nExtraction method: {method}")

        if extracted.confidence_score > 0:
            confidence = int(extracted.confidence_score * 100)
            parts.append(f"Confidence: {confidence}%")

        return "\n".join(parts)

    def get_extracted_resume(self) -> Optional[ExtractedResume]:
        """Return the extracted resume data."""
        return self.extracted_resume

    # Drag and drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            # Check if it's a supported file type
            if file_path.lower().endswith(('.pdf', '.docx', '.txt')):
                self._set_file(file_path)
            else:
                QMessageBox.warning(
                    self,
                    "Unsupported File Type",
                    "Please select a PDF, DOCX, or TXT file."
                )
