"""Cover Letter Editor Dialog.

This dialog provides a user interface for generating, editing, and exporting
AI-powered cover letters tailored to specific job postings.
"""

from __future__ import annotations

from typing import Optional
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QComboBox,
        QGroupBox,
        QMessageBox,
        QFileDialog,
        QCheckBox,
        QProgressDialog,
    )
    from PyQt6.QtCore import Qt, QCoreApplication
    from PyQt6.QtGui import QFont, QTextCursor
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.services.cover_letter_generation_service import CoverLetterGenerationService
from adaptive_resume.models.cover_letter import CoverLetter
from adaptive_resume.models.profile import Profile
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.models.tailored_resume import TailoredResumeModel
from adaptive_resume.gui.database_manager import DatabaseManager
from adaptive_resume.config.settings import Settings


class CoverLetterEditorDialog(QDialog):
    """Dialog for generating, editing, and exporting cover letters.

    Features:
    - AI-powered cover letter generation
    - Rich text editing
    - Template selection
    - Tone and length controls
    - Section-by-section regeneration
    - Export to multiple formats (PDF, DOCX, TXT, HTML)
    - Preview mode

    Attributes:
        profile: User profile
        job_posting: Optional job posting for tailoring
        tailored_resume: Optional tailored resume for consistency
        cover_letter: Generated CoverLetter model instance
        service: CoverLetterGenerationService instance
        settings: Settings instance for AI configuration
    """

    def __init__(
        self,
        profile: Profile,
        job_posting: Optional[JobPosting] = None,
        tailored_resume: Optional[TailoredResumeModel] = None,
        cover_letter: Optional[CoverLetter] = None,
        parent: Optional[QDialog] = None
    ):
        """Initialize cover letter editor dialog.

        Args:
            profile: User profile
            job_posting: Optional job posting to tailor to
            tailored_resume: Optional tailored resume for consistency
            cover_letter: Optional existing cover letter to edit
            parent: Parent widget
        """
        super().__init__(parent)
        self.profile = profile
        self.job_posting = job_posting
        self.tailored_resume = tailored_resume
        self.cover_letter = cover_letter
        self.session = DatabaseManager.get_session()
        self.service = CoverLetterGenerationService(self.session)
        self.settings = Settings()

        # Track if content has been generated/modified
        self.is_generated = cover_letter is not None
        self.is_modified = False

        self.setWindowTitle("Cover Letter Editor")
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)

        self._build_ui()

        # Load existing cover letter or set defaults
        if cover_letter:
            self._load_existing_cover_letter()
        else:
            self._set_defaults()

    def _build_ui(self):
        """Build the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Cover Letter Editor")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(header)

        # Subtitle with job info if available
        subtitle_text = "Generate and customize your professional cover letter"
        if self.job_posting:
            subtitle_text = f"Cover letter for {self.job_posting.job_title} at {self.job_posting.company_name}"
        subtitle = QLabel(subtitle_text)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        # Template and Options Section
        options_group = self._build_options_section()
        layout.addWidget(options_group)

        # Editor Section
        editor_group = self._build_editor_section()
        layout.addWidget(editor_group)

        # Section Controls
        section_controls = self._build_section_controls()
        layout.addWidget(section_controls)

        # Buttons
        button_layout = self._build_button_section()
        layout.addLayout(button_layout)

    def _build_options_section(self) -> QGroupBox:
        """Build the template and options section.

        Returns:
            QGroupBox containing template selector and options
        """
        group = QGroupBox("Generation Options")
        layout = QVBoxLayout()

        # Template selector
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.addItem("Classic Professional", "professional")
        self.template_combo.addItem("Modern/Enthusiastic", "enthusiastic")
        self.template_combo.addItem("Technical/Results-Driven", "technical")
        self.template_combo.addItem("Career Change", "career_change")
        self.template_combo.addItem("Referral-Based", "referral")
        self.template_combo.addItem("Cold Application", "cold_application")
        self.template_combo.addItem("Follow-up After Networking", "networking_followup")
        template_layout.addWidget(self.template_combo)
        template_layout.addStretch()
        layout.addLayout(template_layout)

        # Tone and Length
        controls_layout = QHBoxLayout()

        # Tone selector
        controls_layout.addWidget(QLabel("Tone:"))
        self.tone_combo = QComboBox()
        self.tone_combo.addItem("Formal", "formal")
        self.tone_combo.addItem("Professional", "professional")
        self.tone_combo.addItem("Conversational", "conversational")
        self.tone_combo.addItem("Enthusiastic", "enthusiastic")
        controls_layout.addWidget(self.tone_combo)

        controls_layout.addSpacing(20)

        # Length selector
        controls_layout.addWidget(QLabel("Length:"))
        self.length_combo = QComboBox()
        self.length_combo.addItem("Short (150-250 words)", "short")
        self.length_combo.addItem("Medium (250-400 words)", "medium")
        self.length_combo.addItem("Long (400-500 words)", "long")
        controls_layout.addWidget(self.length_combo)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Focus areas (checkboxes)
        focus_layout = QHBoxLayout()
        focus_layout.addWidget(QLabel("Focus Areas:"))
        self.focus_leadership = QCheckBox("Leadership")
        self.focus_technical = QCheckBox("Technical")
        self.focus_results = QCheckBox("Results")
        self.focus_creativity = QCheckBox("Creativity")
        self.focus_communication = QCheckBox("Communication")
        self.focus_collaboration = QCheckBox("Collaboration")

        focus_layout.addWidget(self.focus_leadership)
        focus_layout.addWidget(self.focus_technical)
        focus_layout.addWidget(self.focus_results)
        focus_layout.addWidget(self.focus_creativity)
        focus_layout.addWidget(self.focus_communication)
        focus_layout.addWidget(self.focus_collaboration)
        focus_layout.addStretch()
        layout.addLayout(focus_layout)

        # Generate button
        generate_layout = QHBoxLayout()
        generate_layout.addStretch()
        self.generate_btn = QPushButton("🤖 Generate Cover Letter")
        self.generate_btn.clicked.connect(self._on_generate)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a3f5f;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a5f7f;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """)
        if not self.service.is_available:
            self.generate_btn.setEnabled(False)
            self.generate_btn.setToolTip("AI generation requires an Anthropic API key in Settings")
        generate_layout.addWidget(self.generate_btn)
        layout.addLayout(generate_layout)

        group.setLayout(layout)
        return group

    def _build_editor_section(self) -> QGroupBox:
        """Build the text editor section.

        Returns:
            QGroupBox containing the text editor
        """
        group = QGroupBox("Cover Letter Content")
        layout = QVBoxLayout()

        # Info bar showing word count
        info_layout = QHBoxLayout()
        self.word_count_label = QLabel("Word count: 0")
        self.word_count_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(self.word_count_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Text editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Click 'Generate Cover Letter' to create an AI-powered cover letter, "
            "or start typing your own content here..."
        )
        self.editor.textChanged.connect(self._on_text_changed)

        # Set font
        font = QFont("Courier New", 11)
        self.editor.setFont(font)

        layout.addWidget(self.editor)

        group.setLayout(layout)
        return group

    def _build_section_controls(self) -> QGroupBox:
        """Build section-specific regeneration controls.

        Returns:
            QGroupBox containing section controls
        """
        group = QGroupBox("Section Controls")
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Regenerate:"))

        self.regen_opening_btn = QPushButton("Opening")
        self.regen_opening_btn.clicked.connect(lambda: self._on_regenerate_section("opening"))
        self.regen_opening_btn.setEnabled(False)
        layout.addWidget(self.regen_opening_btn)

        self.regen_body_btn = QPushButton("Body")
        self.regen_body_btn.clicked.connect(lambda: self._on_regenerate_section("body"))
        self.regen_body_btn.setEnabled(False)
        layout.addWidget(self.regen_body_btn)

        self.regen_closing_btn = QPushButton("Closing")
        self.regen_closing_btn.clicked.connect(lambda: self._on_regenerate_section("closing"))
        self.regen_closing_btn.setEnabled(False)
        layout.addWidget(self.regen_closing_btn)

        layout.addStretch()

        # AI availability notice
        if not self.service.is_available:
            notice = QLabel("(Requires API key)")
            notice.setStyleSheet("color: #999; font-size: 10px;")
            layout.addWidget(notice)

        group.setLayout(layout)
        return group

    def _build_button_section(self) -> QHBoxLayout:
        """Build the bottom button section.

        Returns:
            QHBoxLayout containing action buttons
        """
        layout = QHBoxLayout()

        # Export buttons
        self.export_txt_btn = QPushButton("Export as Text")
        self.export_txt_btn.clicked.connect(lambda: self._on_export("txt"))
        self.export_txt_btn.setEnabled(False)
        layout.addWidget(self.export_txt_btn)

        self.export_html_btn = QPushButton("Export as HTML")
        self.export_html_btn.clicked.connect(lambda: self._on_export("html"))
        self.export_html_btn.setEnabled(False)
        layout.addWidget(self.export_html_btn)

        self.export_pdf_btn = QPushButton("Export as PDF")
        self.export_pdf_btn.clicked.connect(lambda: self._on_export("pdf"))
        self.export_pdf_btn.setEnabled(False)
        layout.addWidget(self.export_pdf_btn)

        layout.addStretch()

        # Save and close buttons
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        self.save_btn.setDefault(True)
        layout.addWidget(self.save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(cancel_btn)

        return layout

    def _set_defaults(self):
        """Set default values for new cover letter."""
        # Set default template based on job posting if available
        default_template = "professional"
        if self.job_posting:
            # Could add logic here to suggest template based on job posting
            pass

        # Set combo boxes to defaults
        for i in range(self.template_combo.count()):
            if self.template_combo.itemData(i) == default_template:
                self.template_combo.setCurrentIndex(i)
                break

        self.tone_combo.setCurrentIndex(1)  # Professional
        self.length_combo.setCurrentIndex(1)  # Medium

    def _load_existing_cover_letter(self):
        """Load an existing cover letter for editing."""
        if not self.cover_letter:
            return

        # Set editor content
        self.editor.setPlainText(self.cover_letter.content)

        # Set template combo
        for i in range(self.template_combo.count()):
            if self.template_combo.itemData(i) == self.cover_letter.template_id:
                self.template_combo.setCurrentIndex(i)
                break

        # Set tone combo
        if self.cover_letter.tone:
            for i in range(self.tone_combo.count()):
                if self.tone_combo.itemData(i) == self.cover_letter.tone:
                    self.tone_combo.setCurrentIndex(i)
                    break

        # Set length combo
        if self.cover_letter.length:
            for i in range(self.length_combo.count()):
                if self.length_combo.itemData(i) == self.cover_letter.length:
                    self.length_combo.setCurrentIndex(i)
                    break

        # Set focus areas
        if self.cover_letter.focus_areas:
            if "leadership" in self.cover_letter.focus_areas:
                self.focus_leadership.setChecked(True)
            if "technical" in self.cover_letter.focus_areas:
                self.focus_technical.setChecked(True)
            if "results" in self.cover_letter.focus_areas:
                self.focus_results.setChecked(True)
            if "creativity" in self.cover_letter.focus_areas:
                self.focus_creativity.setChecked(True)
            if "communication" in self.cover_letter.focus_areas:
                self.focus_communication.setChecked(True)
            if "collaboration" in self.cover_letter.focus_areas:
                self.focus_collaboration.setChecked(True)

        # Enable regeneration buttons
        if self.service.is_available:
            self.regen_opening_btn.setEnabled(True)
            self.regen_body_btn.setEnabled(True)
            self.regen_closing_btn.setEnabled(True)

        # Enable export buttons
        self._update_button_states()

    def _get_focus_areas(self) -> list[str]:
        """Get selected focus areas.

        Returns:
            List of selected focus area strings
        """
        areas = []
        if self.focus_leadership.isChecked():
            areas.append("leadership")
        if self.focus_technical.isChecked():
            areas.append("technical")
        if self.focus_results.isChecked():
            areas.append("results")
        if self.focus_creativity.isChecked():
            areas.append("creativity")
        if self.focus_communication.isChecked():
            areas.append("communication")
        if self.focus_collaboration.isChecked():
            areas.append("collaboration")
        return areas

    def _on_text_changed(self):
        """Handle text editor changes."""
        self.is_modified = True
        self._update_word_count()
        self._update_button_states()

    def _update_word_count(self):
        """Update the word count label."""
        text = self.editor.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        self.word_count_label.setText(f"Word count: {word_count}")

    def _update_button_states(self):
        """Update enabled state of buttons based on content."""
        has_content = bool(self.editor.toPlainText().strip())
        self.save_btn.setEnabled(has_content and self.is_modified)
        self.export_txt_btn.setEnabled(has_content)
        self.export_html_btn.setEnabled(has_content)
        self.export_pdf_btn.setEnabled(has_content)

    def _on_generate(self):
        """Generate cover letter using AI."""
        if not self.service.is_available:
            QMessageBox.warning(
                self,
                "AI Not Available",
                "AI generation requires an Anthropic API key. "
                "Please configure your API key in Settings."
            )
            return

        # Show confirmation if content exists
        if self.editor.toPlainText().strip():
            reply = QMessageBox.question(
                self,
                "Confirm Generation",
                "This will replace the current content. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Show progress dialog
        progress = QProgressDialog("Generating cover letter...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        QCoreApplication.processEvents()

        try:
            # Get settings
            template_id = self.template_combo.currentData()
            tone = self.tone_combo.currentData()
            length = self.length_combo.currentData()
            focus_areas = self._get_focus_areas()

            # Generate cover letter
            self.cover_letter = self.service.generate_cover_letter(
                profile=self.profile,
                job_posting=self.job_posting,
                tailored_resume=self.tailored_resume,
                template_id=template_id,
                tone=tone,
                length=length,
                focus_areas=focus_areas
            )

            # Update editor
            self.editor.setPlainText(self.cover_letter.content)
            self.is_generated = True
            self.is_modified = True

            # Enable regeneration buttons
            self.regen_opening_btn.setEnabled(True)
            self.regen_body_btn.setEnabled(True)
            self.regen_closing_btn.setEnabled(True)

            progress.close()

            QMessageBox.information(
                self,
                "Success",
                "Cover letter generated successfully!"
            )

        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Generation Error",
                f"Failed to generate cover letter:\n{str(e)}"
            )

    def _on_regenerate_section(self, section: str):
        """Regenerate a specific section.

        Args:
            section: Section to regenerate ("opening", "body", or "closing")
        """
        if not self.cover_letter:
            QMessageBox.warning(
                self,
                "No Cover Letter",
                "Please generate a cover letter first before regenerating sections."
            )
            return

        # Show progress
        progress = QProgressDialog(f"Regenerating {section}...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        QCoreApplication.processEvents()

        try:
            # Regenerate section
            new_section_text = self.service.regenerate_section(
                cover_letter=self.cover_letter,
                section=section
            )

            progress.close()

            # Show preview and ask for confirmation
            reply = QMessageBox.question(
                self,
                f"Replace {section.title()}?",
                f"New {section}:\n\n{new_section_text[:200]}...\n\nReplace the current {section}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Update cover letter model
                if section == "opening":
                    self.cover_letter.opening_paragraph = new_section_text
                elif section == "closing":
                    self.cover_letter.closing_paragraph = new_section_text
                else:  # body
                    # Parse as paragraphs if possible
                    paragraphs = new_section_text.split("\n\n")
                    self.cover_letter.body_paragraphs = paragraphs

                # Reassemble and update editor
                content = self.service._assemble_cover_letter(
                    self.cover_letter.opening_paragraph or "",
                    self.cover_letter.body_paragraphs or [],
                    self.cover_letter.closing_paragraph or ""
                )
                self.cover_letter.content = content
                self.editor.setPlainText(content)
                self.is_modified = True

        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Regeneration Error",
                f"Failed to regenerate {section}:\n{str(e)}"
            )

    def _on_export(self, format_type: str):
        """Export cover letter to file.

        Args:
            format_type: Export format ("txt", "html", or "pdf")
        """
        content = self.editor.toPlainText()
        if not content.strip():
            QMessageBox.warning(
                self,
                "No Content",
                "Please generate or enter cover letter content before exporting."
            )
            return

        # Determine file extension and filter
        if format_type == "txt":
            ext = "txt"
            filter_str = "Text Files (*.txt)"
        elif format_type == "html":
            ext = "html"
            filter_str = "HTML Files (*.html)"
        elif format_type == "pdf":
            ext = "pdf"
            filter_str = "PDF Files (*.pdf)"
        else:
            return

        # Get filename from user
        default_filename = "cover_letter"
        if self.job_posting and self.job_posting.company_name:
            default_filename = f"cover_letter_{self.job_posting.company_name.replace(' ', '_')}"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Cover Letter as {ext.upper()}",
            str(Path.home() / f"{default_filename}.{ext}"),
            filter_str
        )

        if not filename:
            return

        try:
            if format_type == "txt":
                self._export_txt(filename, content)
            elif format_type == "html":
                self._export_html(filename, content)
            elif format_type == "pdf":
                self._export_pdf(filename, content)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Cover letter exported to:\n{filename}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export cover letter:\n{str(e)}"
            )

    def _export_txt(self, filename: str, content: str):
        """Export as plain text file.

        Args:
            filename: Output filename
            content: Cover letter content
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

    def _export_html(self, filename: str, content: str):
        """Export as HTML file.

        Args:
            filename: Output filename
            content: Cover letter content
        """
        # Convert plain text to HTML with proper formatting
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Cover Letter</title>
    <style>
        body {{
            font-family: 'Calibri', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            max-width: 8.5in;
            margin: 1in auto;
            padding: 0 0.5in;
        }}
        p {{
            margin-bottom: 1em;
        }}
    </style>
</head>
<body>
"""
        # Split into paragraphs and wrap each in <p> tags
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                html += f"    <p>{para.strip()}</p>\n"

        html += """</body>
</html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

    def _export_pdf(self, filename: str, content: str):
        """Export as PDF file.

        Args:
            filename: Output filename
            content: Cover letter content
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY

            # Create PDF document
            doc = SimpleDocTemplate(
                filename,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )

            # Container for the 'Flowable' objects
            story = []

            # Get default styles
            styles = getSampleStyleSheet()

            # Create custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor='#1a1a1a',
                spaceAfter=12,
                alignment=TA_LEFT
            )

            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=11,
                leading=14,
                textColor='#333333',
                alignment=TA_JUSTIFY,
                spaceAfter=12
            )

            # Split content into paragraphs
            paragraphs = content.strip().split('\n\n')

            for i, para_text in enumerate(paragraphs):
                if not para_text.strip():
                    continue

                # First paragraph could be title/heading if it's short and not too long
                if i == 0 and len(para_text) < 100 and '\n' not in para_text:
                    p = Paragraph(para_text.strip(), title_style)
                else:
                    # Replace single newlines with <br/> tags for ReportLab
                    formatted_text = para_text.replace('\n', '<br/>')
                    p = Paragraph(formatted_text, body_style)

                story.append(p)
                story.append(Spacer(1, 0.1*inch))

            # Build PDF
            doc.build(story)

        except ImportError:
            raise Exception("ReportLab is required for PDF export. Please install it with: pip install reportlab")
        except Exception as e:
            raise Exception(f"Failed to generate PDF: {str(e)}")

    def _on_save(self):
        """Save cover letter to database."""
        content = self.editor.toPlainText()
        if not content.strip():
            QMessageBox.warning(
                self,
                "No Content",
                "Please enter cover letter content before saving."
            )
            return

        try:
            # Update existing or create new cover letter
            if not self.cover_letter:
                # Create new cover letter record
                self.cover_letter = CoverLetter(
                    profile_id=self.profile.id,
                    job_posting_id=self.job_posting.id if self.job_posting else None,
                    tailored_resume_id=self.tailored_resume.id if self.tailored_resume else None,
                    content=content,
                    template_id=self.template_combo.currentData(),
                    tone=self.tone_combo.currentData(),
                    length=self.length_combo.currentData(),
                    focus_areas=self._get_focus_areas(),
                    ai_generated=self.is_generated,
                    user_edited=self.is_modified,
                    company_name=self.job_posting.company_name if self.job_posting else None,
                    job_title=self.job_posting.job_title if self.job_posting else None,
                    word_count=len(content.split())
                )
                self.session.add(self.cover_letter)
            else:
                # Update existing
                self.cover_letter.content = content
                self.cover_letter.user_edited = True
                self.cover_letter.word_count = len(content.split())

            self.session.commit()
            self.is_modified = False
            self._update_button_states()

            QMessageBox.information(
                self,
                "Saved",
                "Cover letter saved successfully!"
            )

            self.accept()

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save cover letter:\n{str(e)}"
            )

    def _on_cancel(self):
        """Handle cancel button click."""
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Discard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.reject()

    def get_cover_letter(self) -> Optional[CoverLetter]:
        """Get the saved cover letter.

        Returns:
            CoverLetter instance if saved, None otherwise
        """
        return self.cover_letter
