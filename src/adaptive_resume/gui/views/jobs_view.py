"""Job-focused view for the Adaptive Resume GUI."""

from __future__ import annotations

from typing import Iterable, Optional

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QListWidget,
        QListWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
        QLabel,
        QGroupBox,
    )
except ImportError as exc:  # pragma: no cover - handled by pytest.importorskip
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.models import Job, BulletPoint


class JobsView(QWidget):
    """Display jobs and their associated bullet points."""

    job_selected = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._jobs: list[Job] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel("Roles")
        header.setObjectName("jobsViewHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(header)

        self.job_list = QListWidget()
        self.job_list.currentRowChanged.connect(self._on_job_selected)
        layout.addWidget(self.job_list)

        bullets_group = QGroupBox("Highlights")
        bullets_layout = QVBoxLayout(bullets_group)

        self.bullet_list = QListWidget()
        bullets_layout.addWidget(self.bullet_list)

        self.description = QTextEdit()
        self.description.setReadOnly(True)
        bullets_layout.addWidget(self.description)

        layout.addWidget(bullets_group)

    def set_jobs(self, jobs: Iterable[Job]) -> None:
        """Load jobs into the view."""
        self._jobs = list(jobs)
        self.job_list.clear()
        for job in self._jobs:
            title = f"{job.job_title} at {job.company_name}"
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, job.id)
            self.job_list.addItem(item)

        if self._jobs:
            self.job_list.setCurrentRow(0)
        else:
            self.bullet_list.clear()
            self.description.clear()

    def show_job_details(self, job: Optional[Job], bullets: Iterable[BulletPoint]) -> None:
        """Render the details for a job selection."""
        self.bullet_list.clear()
        self.description.clear()

        if not job:
            return

        for bullet in bullets:
            item = QListWidgetItem(bullet.content)
            item.setData(Qt.ItemDataRole.UserRole, bullet.id)
            self.bullet_list.addItem(item)

        description_lines: list[str] = []
        if job.location:
            description_lines.append(job.location)
        if job.description:
            description_lines.append(job.description)
        if job.is_current:
            description_lines.append("Currently employed")
        elif job.end_date:
            description_lines.append(f"Ended: {job.end_date:%b %Y}")

        self.description.setPlainText("\n".join(description_lines))

    def _on_job_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._jobs):
            self.job_selected.emit(-1)
            return

        job = self._jobs[index]
        self.job_selected.emit(job.id)

    def current_job_id(self) -> Optional[int]:
        """Return the currently selected job identifier."""
        current_item = self.job_list.currentItem()
        if current_item is None:
            return None
        return int(current_item.data(Qt.ItemDataRole.UserRole))
