"""Dialog for creating or editing job entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QHBoxLayout,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QTextEdit,
        QWidget,
        QVBoxLayout,
        QMessageBox,
    )
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .bullet_enhancement_dialog import BulletEnhancementDialog


@dataclass
class JobDialogResult:
    """Return payload describing job data from the dialog."""

    company_name: str
    job_title: str
    location: str
    start_date: date
    end_date: Optional[date]
    is_current: bool
    description: str
    bullets: List[str]


class JobDialog(QDialog):
    """Dialog used to gather job information and bullet highlights."""

    def __init__(self, parent: Optional[QWidget] = None, job: Optional[dict] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Job")
        self._build_form()
        if job:
            self._load_job(job)

    def _build_form(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.company_name = QLineEdit()
        self.job_title = QLineEdit()
        self.location = QLineEdit()
        self.start_date = self._date_field()
        self.end_date = self._date_field()
        self.description = QTextEdit()
        self.description.setMaximumHeight(120)

        form.addRow("Company", self.company_name)
        form.addRow("Title", self.job_title)
        form.addRow("Location", self.location)
        form.addRow("Start Date", self.start_date)
        form.addRow("End Date", self.end_date)
        form.addRow("Description", self.description)

        layout.addLayout(form)

        bullets_header = QHBoxLayout()
        self.bullets = QListWidget()
        add_button = QPushButton("Add Accomplishment")
        enhance_button = QPushButton("Enhance Accomplishment")
        remove_button = QPushButton("Remove Accomplishment")
        add_button.clicked.connect(self._add_bullet)
        enhance_button.clicked.connect(self._enhance_bullet)
        remove_button.clicked.connect(self._remove_bullet)

        bullets_header.addWidget(add_button)
        bullets_header.addWidget(enhance_button)
        bullets_header.addWidget(remove_button)

        layout.addLayout(bullets_header)
        layout.addWidget(self.bullets)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _date_field(self) -> QWidget:
        widget = QLineEdit()
        widget.setPlaceholderText("YYYY-MM-DD or leave blank")
        return widget

    def _load_job(self, job: dict) -> None:
        self.company_name.setText(job.get("company_name", ""))
        self.job_title.setText(job.get("job_title", ""))
        self.location.setText(job.get("location", ""))
        if job.get("start_date"):
            self.start_date.setText(job["start_date"].strftime("%Y-%m-%d"))
        if job.get("end_date"):
            self.end_date.setText(job["end_date"].strftime("%Y-%m-%d"))
        self.description.setPlainText(job.get("description", ""))
        for bullet in job.get("bullets", []):
            self.bullets.addItem(QListWidgetItem(bullet))

    def _add_bullet(self) -> None:
        text = QTextEdit()
        text.setPlaceholderText("Enter accomplishment (min 10 characters)")
        text.setFixedHeight(80)
        dialog = QDialog(self)
        dialog.setWindowTitle("New Accomplishment")
        inner_layout = QVBoxLayout(dialog)
        inner_layout.addWidget(text)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        inner_layout.addWidget(button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            content = text.toPlainText().strip()
            if content:
                self.bullets.addItem(QListWidgetItem(content))
        dialog.deleteLater()

    def _remove_bullet(self) -> None:
        row = self.bullets.currentRow()
        if row >= 0:
            item = self.bullets.takeItem(row)
            del item

    def _enhance_bullet(self) -> None:
        """Enhance the selected bullet using templates or AI."""
        row = self.bullets.currentRow()
        if row < 0:
            QMessageBox.information(
                self,
                "No Accomplishment Selected",
                "Please select an accomplishment to enhance."
            )
            return

        # Get current bullet text
        current_item = self.bullets.item(row)
        original_text = current_item.text()

        # Open enhancement dialog
        dialog = BulletEnhancementDialog(original_text, self)
        if dialog.exec() == int(QDialog.DialogCode.Accepted):
            enhanced_text = dialog.get_enhanced_text()
            if enhanced_text:
                # Replace the bullet with enhanced version
                current_item.setText(enhanced_text)

    def _parse_date(self, text: str) -> Optional[date]:
        text = text.strip()
        if not text:
            return None
        try:
            year, month, day = [int(part) for part in text.split("-")]
            return date(year, month, day)
        except ValueError as exc:  # pragma: no cover - validated in dialog
            raise ValueError("Dates must be in YYYY-MM-DD format") from exc

    def get_result(self) -> JobDialogResult:
        """Return the captured job data."""
        start = self._parse_date(self.start_date.text())
        if start is None:
            raise ValueError("Start date is required")

        end = self._parse_date(self.end_date.text())

        return JobDialogResult(
            company_name=self.company_name.text().strip(),
            job_title=self.job_title.text().strip(),
            location=self.location.text().strip(),
            start_date=start,
            end_date=end,
            is_current=end is None,
            description=self.description.toPlainText().strip(),
            bullets=[self.bullets.item(i).text() for i in range(self.bullets.count())],
        )
