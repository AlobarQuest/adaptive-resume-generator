"""Tailoring results screen to display job matching analysis."""

from __future__ import annotations

from typing import Optional
import logging

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QScrollArea,
        QGroupBox,
        QGridLayout,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from adaptive_resume.services import TailoredResume, ResumeGenerator
from adaptive_resume.gui.dialogs import CoverLetterEditorDialog, ResumeVariantsDialog
from adaptive_resume.gui.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class TailoringResultsScreen(BaseScreen):
    """Screen to display job posting analysis results."""

    # Signals
    generate_pdf_requested = pyqtSignal()
    generate_cover_letter_requested = pyqtSignal()
    start_over_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.tailored_resume: Optional[TailoredResume] = None
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the results screen UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(20)

        # Placeholder message (shown when no results)
        self.placeholder_label = QLabel("No results to display.\nUpload a job posting to get started.")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet(
            "color: #666; font-size: 16px; padding: 100px;"
        )
        self.content_layout.addWidget(self.placeholder_label)

        # Set content to scroll area
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)

    def display_results(self, tailored_resume: TailoredResume):
        """Display the tailoring results."""
        self.tailored_resume = tailored_resume

        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Header section
        self._add_header_section()

        # Match score section
        self._add_match_score_section()

        # Requirements comparison
        self._add_requirements_section()

        # Selected accomplishments
        self._add_accomplishments_section()

        # Gap analysis
        self._add_gap_analysis_section()

        # Recommendations
        self._add_recommendations_section()

        # Action buttons
        self._add_action_buttons()

        self.content_layout.addStretch()

    def _add_header_section(self):
        """Add header with job title and company."""
        header_frame = QFrame()
        header_frame.setObjectName("settingsCard")
        header_layout = QVBoxLayout(header_frame)

        # Job title
        if self.tailored_resume.job_title:
            title_label = QLabel(self.tailored_resume.job_title)
            title_font = QFont()
            title_font.setPointSize(20)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #4a90e2;")
            header_layout.addWidget(title_label)

        # Company name
        if self.tailored_resume.company_name:
            company_label = QLabel(self.tailored_resume.company_name)
            company_font = QFont()
            company_font.setPointSize(14)
            company_label.setFont(company_font)
            company_label.setStyleSheet("color: #ccc;")
            header_layout.addWidget(company_label)

        self.content_layout.addWidget(header_frame)

    def _add_match_score_section(self):
        """Add overall match score section."""
        generator = ResumeGenerator()
        match_score = generator.calculate_match_score(self.tailored_resume)

        score_frame = QFrame()
        score_frame.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 #1a3a5a, stop:{match_score} #2a6a4a, stop:{match_score} #3a2a2a, stop:1 #2a2a2a); "
            "border-radius: 12px; padding: 20px;"
        )
        score_layout = QHBoxLayout(score_frame)

        # Match percentage
        percentage = int(match_score * 100)
        score_label = QLabel(f"{percentage}%")
        score_font = QFont()
        score_font.setPointSize(48)
        score_font.setBold(True)
        score_label.setFont(score_font)

        # Color based on score
        if percentage >= 80:
            color = "#4ade80"  # Green
            indicator = "✓"
        elif percentage >= 60:
            color = "#fbbf24"  # Yellow
            indicator = "~"
        else:
            color = "#f87171"  # Red
            indicator = "!"

        score_label.setStyleSheet(f"color: {color};")
        score_layout.addWidget(score_label)

        # Match text
        match_text_layout = QVBoxLayout()
        match_label = QLabel("Overall Match")
        match_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        match_text_layout.addWidget(match_label)

        if percentage >= 80:
            desc = "Strong match! Your experience aligns well."
        elif percentage >= 60:
            desc = "Good match with some gaps to address."
        else:
            desc = "Some key skills missing. Review recommendations."

        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: #ccc; font-size: 14px;")
        desc_label.setWordWrap(True)
        match_text_layout.addWidget(desc_label)

        score_layout.addLayout(match_text_layout)
        score_layout.addStretch()

        # Indicator
        indicator_label = QLabel(indicator)
        indicator_font = QFont()
        indicator_font.setPointSize(36)
        indicator_label.setFont(indicator_font)
        indicator_label.setStyleSheet(f"color: {color};")
        score_layout.addWidget(indicator_label)

        self.content_layout.addWidget(score_frame)

    def _add_requirements_section(self):
        """Add requirements comparison section."""
        group = QGroupBox("Requirements Comparison")
        group.setObjectName("settingsCard")
        layout = QVBoxLayout(group)

        # Coverage percentage
        coverage_pct = int(self.tailored_resume.coverage_percentage * 100)
        coverage_label = QLabel(f"Skill Coverage: {coverage_pct}%")
        coverage_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(coverage_label)

        # Skills grid
        grid = QGridLayout()
        grid.setSpacing(10)

        row = 0
        for skill, covered in sorted(self.tailored_resume.skill_coverage.items()):
            # Icon
            icon = "✓" if covered else "✗"
            color = "#4ade80" if covered else "#f87171"

            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
            grid.addWidget(icon_label, row, 0)

            # Skill name
            skill_label = QLabel(skill)
            skill_label.setStyleSheet("font-size: 14px;")
            grid.addWidget(skill_label, row, 1)

            # Status
            status = "Covered" if covered else "Missing"
            status_label = QLabel(status)
            status_label.setStyleSheet(f"color: {color}; font-size: 12px;")
            grid.addWidget(status_label, row, 2)

            row += 1

        layout.addLayout(grid)
        self.content_layout.addWidget(group)

    def _add_accomplishments_section(self):
        """Add selected accomplishments section."""
        group = QGroupBox(f"Selected Accomplishments ({len(self.tailored_resume.selected_accomplishments)})")
        group.setObjectName("settingsCard")
        layout = QVBoxLayout(group)

        for item in self.tailored_resume.selected_accomplishments[:10]:  # Show top 10
            bullet_frame = QFrame()
            bullet_frame.setStyleSheet(
                "background-color: #2a2a3a; border-left: 3px solid #4a90e2; "
                "padding: 10px; margin-bottom: 5px; border-radius: 4px;"
            )
            bullet_layout = QVBoxLayout(bullet_frame)

            # Bullet text
            text_label = QLabel(f"• {item.bullet_text}")
            text_label.setWordWrap(True)
            text_label.setStyleSheet("font-size: 13px; color: #e0e0e0;")
            bullet_layout.addWidget(text_label)

            # Metadata
            meta_layout = QHBoxLayout()

            # Score
            score_pct = int(item.final_score * 100)
            score_label = QLabel(f"Score: {score_pct}%")
            score_label.setStyleSheet("font-size: 11px; color: #4a90e2;")
            meta_layout.addWidget(score_label)

            # Company and job title
            if item.company_name:
                job_label = QLabel(f"{item.company_name} • {item.job_title}")
                job_label.setStyleSheet("font-size: 11px; color: #999;")
                meta_layout.addWidget(job_label)

            meta_layout.addStretch()

            # Matched skills
            if item.matched_skills:
                skills_text = ", ".join(item.matched_skills[:3])
                if len(item.matched_skills) > 3:
                    skills_text += f" +{len(item.matched_skills) - 3}"
                skills_label = QLabel(f"🎯 {skills_text}")
                skills_label.setStyleSheet("font-size: 11px; color: #4ade80;")
                meta_layout.addWidget(skills_label)

            bullet_layout.addLayout(meta_layout)

            layout.addWidget(bullet_frame)

        self.content_layout.addWidget(group)

    def _add_gap_analysis_section(self):
        """Add gap analysis section."""
        if not self.tailored_resume.gaps:
            return

        group = QGroupBox(f"Missing Skills ({len(self.tailored_resume.gaps)})")
        group.setObjectName("settingsCard")
        layout = QVBoxLayout(group)

        gaps_label = QLabel(
            "The following skills were not found in your selected accomplishments:"
        )
        gaps_label.setStyleSheet("color: #ccc; font-size: 13px; margin-bottom: 10px;")
        gaps_label.setWordWrap(True)
        layout.addWidget(gaps_label)

        # Display gaps
        gaps_text = ", ".join(self.tailored_resume.gaps)
        gaps_display = QLabel(gaps_text)
        gaps_display.setWordWrap(True)
        gaps_display.setStyleSheet(
            "color: #f87171; font-size: 14px; font-weight: bold; "
            "background-color: #3a2a2a; padding: 10px; border-radius: 4px;"
        )
        layout.addWidget(gaps_display)

        self.content_layout.addWidget(group)

    def _add_recommendations_section(self):
        """Add recommendations section."""
        if not self.tailored_resume.recommendations:
            return

        group = QGroupBox("Recommendations")
        group.setObjectName("settingsCard")
        layout = QVBoxLayout(group)

        for rec in self.tailored_resume.recommendations:
            rec_frame = QFrame()
            rec_frame.setStyleSheet(
                "background-color: #2a3a4a; padding: 12px; "
                "margin-bottom: 8px; border-radius: 4px;"
            )
            rec_layout = QHBoxLayout(rec_frame)

            rec_label = QLabel(rec)
            rec_label.setWordWrap(True)
            rec_label.setStyleSheet("font-size: 13px; color: #e0e0e0;")
            rec_layout.addWidget(rec_label)

            layout.addWidget(rec_frame)

        self.content_layout.addWidget(group)

    def _add_action_buttons(self):
        """Add action buttons."""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(15)

        # Generate PDF button
        pdf_btn = QPushButton("📄 Generate PDF Resume")
        pdf_btn.setObjectName("primaryButton")
        pdf_btn.setMinimumHeight(50)
        pdf_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        pdf_btn.clicked.connect(self.generate_pdf_requested.emit)
        button_layout.addWidget(pdf_btn)

        # Generate Cover Letter button
        cover_letter_btn = QPushButton("✉️ Generate Cover Letter")
        cover_letter_btn.setObjectName("primaryButton")
        cover_letter_btn.setMinimumHeight(50)
        cover_letter_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        cover_letter_btn.clicked.connect(self._on_generate_cover_letter)
        button_layout.addWidget(cover_letter_btn)

        # Manage Variants button
        variants_btn = QPushButton("📋 Manage Variants")
        variants_btn.setMinimumHeight(50)
        variants_btn.setStyleSheet("font-size: 14px; padding: 10px 20px;")
        variants_btn.clicked.connect(self._on_manage_variants)
        button_layout.addWidget(variants_btn)

        # Start over button
        start_over_btn = QPushButton("🔄 Analyze Another Job")
        start_over_btn.setMinimumHeight(50)
        start_over_btn.setStyleSheet("font-size: 14px; padding: 10px 20px;")
        start_over_btn.clicked.connect(self.start_over_requested.emit)
        button_layout.addWidget(start_over_btn)

        self.content_layout.addWidget(button_frame)

    def _on_generate_cover_letter(self):
        """Handle generate cover letter button click."""
        try:
            # Get the session and required data
            session = DatabaseManager.get_session()

            # Get profile - assume first profile for now
            from adaptive_resume.models.profile import Profile
            profile = session.query(Profile).first()

            if not profile:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "No Profile",
                    "Please create a profile first before generating a cover letter."
                )
                return

            # Get job posting from tailored resume
            job_posting = None
            tailored_resume_model = None

            if self.tailored_resume and self.tailored_resume.job_posting_id:
                from adaptive_resume.models.job_posting import JobPosting
                from adaptive_resume.models.tailored_resume import TailoredResumeModel

                job_posting = session.query(JobPosting).filter_by(
                    id=self.tailored_resume.job_posting_id
                ).first()

                # Get the TailoredResumeModel from database if we have an ID
                if hasattr(self.tailored_resume, 'id') and self.tailored_resume.id:
                    tailored_resume_model = session.query(TailoredResumeModel).filter_by(
                        id=self.tailored_resume.id
                    ).first()

            # Open cover letter editor dialog
            dialog = CoverLetterEditorDialog(
                profile=profile,
                job_posting=job_posting,
                tailored_resume=tailored_resume_model,
                parent=self
            )

            if dialog.exec():
                # Cover letter was saved successfully
                logger.info("Cover letter generated and saved")

        except Exception as e:
            logger.error(f"Error generating cover letter: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate cover letter:\n{str(e)}"
            )

    def _on_manage_variants(self):
        """Handle manage variants button click."""
        try:
            if not self.tailored_resume or not self.tailored_resume.job_posting_id:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "No Job Posting",
                    "Unable to find job posting information for variant management."
                )
                return

            # Get current tailored resume ID
            current_variant_id = None
            if hasattr(self.tailored_resume, 'id') and self.tailored_resume.id:
                current_variant_id = self.tailored_resume.id

            # Open variants dialog
            dialog = ResumeVariantsDialog(
                job_posting_id=self.tailored_resume.job_posting_id,
                current_variant_id=current_variant_id,
                parent=self
            )

            dialog.exec()

            # Could optionally reload/refresh results if a different variant was selected
            logger.info("Variants dialog closed")

        except Exception as e:
            logger.error(f"Error managing variants: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open variants manager:\n{str(e)}"
            )


__all__ = ["TailoringResultsScreen"]
