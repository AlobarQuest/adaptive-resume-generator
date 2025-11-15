"""Dialog for previewing and exporting resume PDFs."""

from __future__ import annotations

import tempfile
import os
from typing import Optional
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QComboBox,
        QCheckBox,
        QGroupBox,
        QTextEdit,
        QMessageBox,
        QFileDialog,
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QDesktopServices
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.services import ResumePDFGenerator, ResumePDFGeneratorError
from adaptive_resume.gui.database_manager import DatabaseManager


class ResumePDFPreviewDialog(QDialog):
    """Dialog for previewing and exporting resume PDFs.

    Features:
    - Template selector dropdown
    - Options for customization (include summary)
    - Export to PDF button
    - Preview information display
    - Direct print capability (future enhancement)
    """

    def __init__(
        self,
        tailored_resume_id: int,
        parent: Optional[QDialog] = None
    ):
        """Initialize PDF preview dialog.

        Args:
            tailored_resume_id: ID of the TailoredResume to generate PDF from
            parent: Parent widget
        """
        super().__init__(parent)
        self.tailored_resume_id = tailored_resume_id
        self.session = DatabaseManager.get_session()
        self.pdf_generator = ResumePDFGenerator(self.session)
        self.current_pdf_bytes = None
        self.temp_pdf_path = None

        self.setWindowTitle("Resume PDF Preview")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self._build_ui()
        self._load_initial_preview()

    def _build_ui(self):
        """Build the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Resume PDF Export")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Select a template and customize your resume before exporting.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        # Template Selection Section
        template_group = self._build_template_section()
        layout.addWidget(template_group)

        # Options Section
        options_group = self._build_options_section()
        layout.addWidget(options_group)

        # Preview Info Section
        preview_group = self._build_preview_section()
        layout.addWidget(preview_group)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Preview button (opens PDF in external viewer)
        preview_button = QPushButton("Preview in PDF Viewer")
        preview_button.clicked.connect(self._preview_in_viewer)
        button_layout.addWidget(preview_button)

        # Export button
        export_button = QPushButton("Export as PDF...")
        export_button.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        export_button.clicked.connect(self._export_pdf)
        button_layout.addWidget(export_button)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _build_template_section(self) -> QGroupBox:
        """Build the template selection section."""
        group = QGroupBox("Template Selection")
        layout = QVBoxLayout()

        # Template selector
        selector_layout = QHBoxLayout()
        template_label = QLabel("Template:")
        template_label.setStyleSheet("font-weight: bold;")
        selector_layout.addWidget(template_label)

        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(200)

        # Get available templates
        templates = self.pdf_generator.list_available_templates()
        template_descriptions = {
            'classic': 'Classic - Traditional professional layout',
            'modern': 'Modern - Contemporary two-column design',
            'compact': 'Compact - Dense, space-efficient layout',
            'ats-friendly': 'ATS-Friendly - Optimized for applicant tracking systems'
        }

        for template_name in templates:
            display_text = template_descriptions.get(template_name, template_name.title())
            self.template_combo.addItem(display_text, template_name)

        # Set default to classic
        classic_index = self.template_combo.findData('classic')
        if classic_index >= 0:
            self.template_combo.setCurrentIndex(classic_index)

        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        selector_layout.addWidget(self.template_combo)
        selector_layout.addStretch()

        layout.addLayout(selector_layout)

        # Template description
        self.template_description = QLabel()
        self.template_description.setWordWrap(True)
        self.template_description.setStyleSheet("color: #888; margin-top: 10px; padding: 10px;")
        self._update_template_description()
        layout.addWidget(self.template_description)

        group.setLayout(layout)
        return group

    def _build_options_section(self) -> QGroupBox:
        """Build the options section."""
        group = QGroupBox("Customization Options")
        layout = QVBoxLayout()

        # Include summary checkbox
        self.include_summary_cb = QCheckBox("Include professional summary")
        self.include_summary_cb.setChecked(True)
        self.include_summary_cb.stateChanged.connect(self._on_options_changed)
        layout.addWidget(self.include_summary_cb)

        # Summary text edit (only visible when checkbox is checked)
        summary_label = QLabel("Summary text:")
        summary_label.setStyleSheet("margin-top: 10px;")
        layout.addWidget(summary_label)

        self.summary_text_edit = QTextEdit()
        self.summary_text_edit.setPlaceholderText(
            "Enter your professional summary here, or leave blank to use profile summary..."
        )
        self.summary_text_edit.setMaximumHeight(100)
        self.summary_text_edit.textChanged.connect(self._on_options_changed)
        layout.addWidget(self.summary_text_edit)

        # Connect checkbox to show/hide summary edit
        self.include_summary_cb.stateChanged.connect(
            lambda: self.summary_text_edit.setEnabled(self.include_summary_cb.isChecked())
        )

        group.setLayout(layout)
        return group

    def _build_preview_section(self) -> QGroupBox:
        """Build the preview information section."""
        group = QGroupBox("Preview Information")
        layout = QVBoxLayout()

        self.preview_info_label = QLabel("Generating preview...")
        self.preview_info_label.setWordWrap(True)
        self.preview_info_label.setStyleSheet("padding: 15px;")
        layout.addWidget(self.preview_info_label)

        note_label = QLabel(
            "💡 Tip: Use 'Preview in PDF Viewer' to see the actual PDF before exporting."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet(
            "color: #888; font-size: 11px; padding: 10px; "
            "background: #1a2332; border-radius: 4px; margin-top: 10px;"
        )
        layout.addWidget(note_label)

        group.setLayout(layout)
        return group

    def _update_template_description(self):
        """Update the template description based on current selection."""
        template_name = self.template_combo.currentData()

        descriptions = {
            'classic': (
                "Traditional professional layout with serif fonts (Times-Roman). "
                "Features clean section headers, bullet points, and a single-column design. "
                "Best for: Traditional industries, formal positions."
            ),
            'modern': (
                "Contemporary two-column design with a sidebar. "
                "Uses Helvetica fonts with blue accents and a modern feel. "
                "Best for: Tech roles, creative positions, modern companies."
            ),
            'compact': (
                "Dense, space-efficient layout with smaller fonts and tight spacing. "
                "Designed to fit maximum content on a single page. "
                "Best for: Senior roles with extensive experience."
            ),
            'ats-friendly': (
                "Simple, parseable structure optimized for Applicant Tracking Systems. "
                "Uses standard fonts with clear labels and no special formatting. "
                "Best for: Large companies, online applications, ATS systems."
            )
        }

        description = descriptions.get(template_name, "No description available.")
        self.template_description.setText(description)

    def _on_template_changed(self):
        """Handle template selection change."""
        self._update_template_description()
        self._regenerate_preview()

    def _on_options_changed(self):
        """Handle options change."""
        self._regenerate_preview()

    def _load_initial_preview(self):
        """Load initial preview."""
        self._regenerate_preview()

    def _regenerate_preview(self):
        """Regenerate the PDF preview."""
        try:
            template_name = self.template_combo.currentData()
            include_summary = self.include_summary_cb.isChecked()
            summary_text = self.summary_text_edit.toPlainText().strip() if include_summary else None

            # Generate PDF bytes
            self.current_pdf_bytes = self.pdf_generator.generate_pdf(
                tailored_resume_id=self.tailored_resume_id,
                template_name=template_name,
                include_summary=include_summary,
                summary_text=summary_text if summary_text else None
            )

            # Update preview info
            pdf_size_kb = len(self.current_pdf_bytes) / 1024
            self.preview_info_label.setText(
                f"✓ PDF generated successfully\n\n"
                f"Template: {template_name.upper()}\n"
                f"File size: {pdf_size_kb:.1f} KB\n"
                f"Summary: {'Included' if include_summary else 'Not included'}"
            )

            # Clean up old temp file
            if self.temp_pdf_path and os.path.exists(self.temp_pdf_path):
                try:
                    os.remove(self.temp_pdf_path)
                except Exception:
                    pass  # Ignore cleanup errors

            self.temp_pdf_path = None

        except ResumePDFGeneratorError as e:
            self.current_pdf_bytes = None
            self.preview_info_label.setText(f"❌ Error generating PDF:\n\n{str(e)}")
        except Exception as e:
            self.current_pdf_bytes = None
            self.preview_info_label.setText(f"❌ Unexpected error:\n\n{str(e)}")

    def _preview_in_viewer(self):
        """Open the PDF in an external viewer for preview."""
        if not self.current_pdf_bytes:
            QMessageBox.warning(
                self,
                "No PDF Generated",
                "Please wait for the PDF to be generated before previewing."
            )
            return

        try:
            # Create temp file
            if not self.temp_pdf_path:
                temp_dir = tempfile.gettempdir()
                temp_file = tempfile.NamedTemporaryFile(
                    mode='wb',
                    suffix='.pdf',
                    prefix='resume_preview_',
                    dir=temp_dir,
                    delete=False
                )
                temp_file.write(self.current_pdf_bytes)
                temp_file.close()
                self.temp_pdf_path = temp_file.name

            # Open in default PDF viewer
            from PyQt6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.temp_pdf_path))

        except Exception as e:
            QMessageBox.critical(
                self,
                "Preview Failed",
                f"Failed to open PDF preview:\n\n{str(e)}"
            )

    def _export_pdf(self):
        """Export the PDF to a file."""
        if not self.current_pdf_bytes:
            QMessageBox.warning(
                self,
                "No PDF Generated",
                "Please wait for the PDF to be generated before exporting."
            )
            return

        # Generate default filename
        try:
            from adaptive_resume.models.tailored_resume import TailoredResumeModel
            tailored_resume = self.session.query(TailoredResumeModel).get(self.tailored_resume_id)
            if tailored_resume and tailored_resume.profile and tailored_resume.job_posting:
                profile = tailored_resume.profile
                job_posting = tailored_resume.job_posting
                default_filename = (
                    f"{profile.first_name}_{profile.last_name}_Resume_"
                    f"{job_posting.company_name.replace(' ', '_')}.pdf"
                )
            else:
                default_filename = "Resume.pdf"
        except Exception:
            default_filename = "Resume.pdf"

        # Open file save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Resume as PDF",
            default_filename,
            "PDF Files (*.pdf);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Save PDF to file
            output_path = self.pdf_generator.save_pdf(
                tailored_resume_id=self.tailored_resume_id,
                output_path=file_path,
                template_name=self.template_combo.currentData(),
                include_summary=self.include_summary_cb.isChecked(),
                summary_text=self.summary_text_edit.toPlainText().strip() or None
            )

            QMessageBox.information(
                self,
                "Export Successful",
                f"Resume PDF exported successfully to:\n\n{output_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export PDF:\n\n{str(e)}"
            )

    def closeEvent(self, event):
        """Clean up temp file on close."""
        if self.temp_pdf_path and os.path.exists(self.temp_pdf_path):
            try:
                os.remove(self.temp_pdf_path)
            except Exception:
                pass  # Ignore cleanup errors
        super().closeEvent(event)
