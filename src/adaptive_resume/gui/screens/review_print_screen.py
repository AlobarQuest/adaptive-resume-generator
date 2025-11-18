"""Review and print documents screen."""

from __future__ import annotations

from typing import Optional, List
import json

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QScrollArea,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QMessageBox,
        QDialog,
    )
    from PyQt6.QtCore import Qt
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from adaptive_resume.gui.database_manager import DatabaseManager
from adaptive_resume.models.tailored_resume import TailoredResumeModel
from adaptive_resume.models.base import DEFAULT_PROFILE_ID


class ReviewPrintScreen(BaseScreen):
    """Screen for reviewing and printing documents."""

    def __init__(
        self,
        parent: Optional[QWidget] = None
    ) -> None:
        self.session = DatabaseManager.get_session()
        self.selected_resume: Optional[TailoredResumeModel] = None
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the review/print screen UI."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("Review & Print Resumes")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._load_resumes)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Description
        description = QLabel(
            "Select a tailored resume to preview and export as PDF."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #ccc; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(description)

        # Resumes table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Company", "Job Title", "Date Created", "# Accomplishments", "Actions"
        ])

        # Configure table
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(4, 200)

        layout.addWidget(self.table)

        # Summary label
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

        # Load resumes
        self._load_resumes()

    def _load_resumes(self):
        """Load all tailored resumes from database."""
        try:
            resumes = self.session.query(TailoredResumeModel).filter_by(
                profile_id=DEFAULT_PROFILE_ID
            ).order_by(TailoredResumeModel.created_at.desc()).all()

            self.table.setRowCount(0)

            for row, resume in enumerate(resumes):
                self.table.insertRow(row)

                # Company (from job posting if available)
                company = resume.job_posting.company_name if resume.job_posting else "Unknown Company"
                self.table.setItem(row, 0, QTableWidgetItem(company))

                # Job title (from job posting if available)
                job_title = resume.job_posting.job_title if resume.job_posting else "Unknown Position"
                self.table.setItem(row, 1, QTableWidgetItem(job_title))

                # Date created
                date_str = resume.created_at.strftime("%Y-%m-%d %H:%M") if resume.created_at else ""
                self.table.setItem(row, 2, QTableWidgetItem(date_str))

                # Number of accomplishments
                accomplishments = json.loads(resume.selected_accomplishments_json) if resume.selected_accomplishments_json else []
                self.table.setItem(row, 3, QTableWidgetItem(str(len(accomplishments))))

                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                actions_layout.setSpacing(4)

                # View/Generate PDF button
                pdf_btn = QPushButton("📄 Generate PDF")
                pdf_btn.setMinimumHeight(30)
                pdf_btn.setMaximumHeight(35)
                pdf_btn.setStyleSheet("QPushButton { padding: 4px 8px; }")
                pdf_btn.clicked.connect(lambda checked, r=resume: self._generate_pdf(r))
                actions_layout.addWidget(pdf_btn)

                # Delete button
                delete_btn = QPushButton("🗑️")
                delete_btn.setToolTip("Delete this resume")
                delete_btn.setMinimumWidth(40)
                delete_btn.setMinimumHeight(30)
                delete_btn.setMaximumHeight(35)
                delete_btn.setStyleSheet("QPushButton { padding: 4px 8px; }")
                delete_btn.clicked.connect(lambda checked, r=resume: self._delete_resume(r))
                actions_layout.addWidget(delete_btn)

                self.table.setCellWidget(row, 4, actions_widget)

                # Set row height
                self.table.setRowHeight(row, 45)

                # Store resume ID in first column
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, resume.id)

            self.summary_label.setText(f"Total tailored resumes: {len(resumes)}")

            if len(resumes) == 0:
                QMessageBox.information(
                    self,
                    "No Resumes Found",
                    "You haven't generated any tailored resumes yet.\n\n"
                    "To create a tailored resume:\n"
                    "1. Go to 'Upload Job Posting'\n"
                    "2. Upload or paste a job posting\n"
                    "3. Click 'Process' to analyze and generate your tailored resume"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Resumes",
                f"Failed to load tailored resumes:\n{str(e)}"
            )

    def _generate_pdf(self, resume: TailoredResumeModel):
        """Generate PDF for the selected resume."""
        try:
            from adaptive_resume.gui.dialogs.resume_pdf_preview_dialog import ResumePDFPreviewDialog
            from adaptive_resume.services.resume_generator import TailoredResume
            from adaptive_resume.services.matching_engine import ScoredAccomplishment

            # Convert TailoredResumeModel to TailoredResume dataclass
            accomplishments_data = json.loads(resume.selected_accomplishments_json) if resume.selected_accomplishments_json else []

            # Reconstruct ScoredAccomplishment objects
            scored_accomplishments = []
            for acc_data in accomplishments_data:
                scored_acc = ScoredAccomplishment(
                    bullet_id=acc_data.get('bullet_id'),
                    job_id=acc_data.get('job_id'),
                    text=acc_data.get('text', ''),
                    skill_match_score=acc_data.get('skill_match_score', 0.0),
                    semantic_score=acc_data.get('semantic_score', 0.0),
                    recency_score=acc_data.get('recency_score', 0.0),
                    metrics_score=acc_data.get('metrics_score', 0.0),
                    total_score=acc_data.get('total_score', 0.0),
                    matched_skills=acc_data.get('matched_skills', []),
                    relevance_explanation=acc_data.get('relevance_explanation', '')
                )
                scored_accomplishments.append(scored_acc)

            # Create TailoredResume dataclass
            tailored_resume = TailoredResume(
                profile_id=resume.profile_id,
                job_posting_id=resume.job_posting_id,
                selected_accomplishments=scored_accomplishments,
                skill_coverage=json.loads(resume.skill_coverage_json) if resume.skill_coverage_json else {},
                coverage_percentage=resume.coverage_percentage or 0.0,
                gaps=json.loads(resume.gaps_json) if resume.gaps_json else [],
                recommendations=json.loads(resume.recommendations_json) if resume.recommendations_json else [],
                created_at=resume.created_at,
                job_title=resume.job_posting.job_title if resume.job_posting else "Unknown Position",
                company_name=resume.job_posting.company_name if resume.job_posting else "Unknown Company",
                id=resume.id
            )

            # Open PDF preview dialog
            dialog = ResumePDFPreviewDialog(tailored_resume, parent=self)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(
                self,
                "PDF Generation Error",
                f"Failed to generate PDF:\n{str(e)}"
            )

    def _delete_resume(self, resume: TailoredResumeModel):
        """Delete a tailored resume."""
        company = resume.job_posting.company_name if resume.job_posting else "Unknown Company"
        job_title = resume.job_posting.job_title if resume.job_posting else "Unknown Position"

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the tailored resume for:\n\n"
            f"{company} - {job_title}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(resume)
                self.session.commit()
                self._load_resumes()

                QMessageBox.information(
                    self,
                    "Resume Deleted",
                    "The tailored resume has been deleted successfully."
                )

            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(
                    self,
                    "Delete Error",
                    f"Failed to delete resume:\n{str(e)}"
                )

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        self._load_resumes()


__all__ = ["ReviewPrintScreen"]
