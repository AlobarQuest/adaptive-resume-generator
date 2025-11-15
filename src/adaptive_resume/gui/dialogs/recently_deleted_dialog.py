"""Dialog for viewing and restoring recently deleted items."""

from __future__ import annotations

from typing import Optional, List
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QTabWidget,
        QWidget,
    )
    from PyQt6.QtCore import Qt
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc


class RecentlyDeletedDialog(QDialog):
    """Dialog for viewing and restoring recently deleted jobs and bullet points."""

    def __init__(self, job_service, profile_id: int, parent=None) -> None:
        super().__init__(parent)
        self.job_service = job_service
        self.profile_id = profile_id
        self.setWindowTitle("Recently Deleted Items")
        self.setMinimumSize(700, 500)
        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Recently Deleted Items (Last 30 Days)")
        header.setObjectName("dialogTitle")
        layout.addWidget(header)

        # Info label
        info_label = QLabel(
            "Items deleted more than 30 days ago are permanently removed. "
            "Select items below to restore or permanently delete them."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Tab widget for jobs and bullets
        self.tab_widget = QTabWidget()

        # Jobs tab
        self.jobs_tab = QWidget()
        jobs_layout = QVBoxLayout(self.jobs_tab)

        self.jobs_list = QListWidget()
        self.jobs_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        jobs_layout.addWidget(self.jobs_list)

        # Jobs buttons
        jobs_btn_layout = QHBoxLayout()
        self.restore_job_btn = QPushButton("♻️ Restore Selected Job(s)")
        self.restore_job_btn.clicked.connect(self._restore_selected_jobs)
        jobs_btn_layout.addWidget(self.restore_job_btn)

        self.delete_job_btn = QPushButton("🗑️ Permanently Delete Selected Job(s)")
        self.delete_job_btn.clicked.connect(self._permanently_delete_selected_jobs)
        jobs_btn_layout.addWidget(self.delete_job_btn)

        jobs_layout.addLayout(jobs_btn_layout)
        self.tab_widget.addTab(self.jobs_tab, "Deleted Roles")

        # Bullets tab
        self.bullets_tab = QWidget()
        bullets_layout = QVBoxLayout(self.bullets_tab)

        self.bullets_list = QListWidget()
        self.bullets_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        bullets_layout.addWidget(self.bullets_list)

        # Bullets buttons
        bullets_btn_layout = QHBoxLayout()
        self.restore_bullet_btn = QPushButton("♻️ Restore Selected Accomplishment(s)")
        self.restore_bullet_btn.clicked.connect(self._restore_selected_bullets)
        bullets_btn_layout.addWidget(self.restore_bullet_btn)

        self.delete_bullet_btn = QPushButton("🗑️ Permanently Delete Selected Accomplishment(s)")
        self.delete_bullet_btn.clicked.connect(self._permanently_delete_selected_bullets)
        bullets_btn_layout.addWidget(self.delete_bullet_btn)

        bullets_layout.addLayout(bullets_btn_layout)
        self.tab_widget.addTab(self.bullets_tab, "Deleted Accomplishments")

        layout.addWidget(self.tab_widget)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)

        layout.addLayout(bottom_layout)

    def _load_data(self) -> None:
        """Load recently deleted items."""
        self._load_jobs()
        self._load_bullets()

    def _load_jobs(self) -> None:
        """Load recently deleted jobs."""
        self.jobs_list.clear()

        jobs = self.job_service.get_recently_deleted_jobs(self.profile_id, days=30)

        if not jobs:
            item = QListWidgetItem("No recently deleted roles")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.jobs_list.addItem(item)
            self.restore_job_btn.setEnabled(False)
            self.delete_job_btn.setEnabled(False)
        else:
            for job in jobs:
                deleted_date = self._format_datetime(job.deleted_at)
                text = f"{job.job_title} at {job.company_name} (Deleted: {deleted_date})"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, job.id)
                self.jobs_list.addItem(item)
            self.restore_job_btn.setEnabled(True)
            self.delete_job_btn.setEnabled(True)

        # Update tab title with count
        job_count = len(jobs) if jobs else 0
        self.tab_widget.setTabText(0, f"Deleted Roles ({job_count})")

    def _load_bullets(self) -> None:
        """Load recently deleted bullet points."""
        self.bullets_list.clear()

        bullets = self.job_service.get_recently_deleted_bullets(self.profile_id, days=30)

        if not bullets:
            item = QListWidgetItem("No recently deleted accomplishments")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.bullets_list.addItem(item)
            self.restore_bullet_btn.setEnabled(False)
            self.delete_bullet_btn.setEnabled(False)
        else:
            for bullet in bullets:
                deleted_date = self._format_datetime(bullet.deleted_at)
                # Show preview of content (first 100 chars)
                preview = bullet.content[:100] + "..." if len(bullet.content) > 100 else bullet.content
                # Get job info if available
                job_info = ""
                if bullet.job:
                    job_info = f" [{bullet.job.job_title} at {bullet.job.company_name}]"
                text = f"{preview}{job_info} (Deleted: {deleted_date})"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, bullet.id)
                self.bullets_list.addItem(item)
            self.restore_bullet_btn.setEnabled(True)
            self.delete_bullet_btn.setEnabled(True)

        # Update tab title with count
        bullet_count = len(bullets) if bullets else 0
        self.tab_widget.setTabText(1, f"Deleted Accomplishments ({bullet_count})")

    def _format_datetime(self, dt: Optional[datetime]) -> str:
        """Format datetime for display."""
        if not dt:
            return "Unknown"
        # Show relative time if recent
        from datetime import datetime, timedelta
        now = datetime.now()
        diff = now - dt

        if diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} min{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return dt.strftime("%b %d, %Y at %I:%M %p")

    def _restore_selected_jobs(self) -> None:
        """Restore selected jobs."""
        selected_items = self.jobs_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select at least one role to restore.")
            return

        # Confirm
        count = len(selected_items)
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Are you sure you want to restore {count} role{'s' if count > 1 else ''}?\n\n"
            "All accomplishments for the restored role(s) will also be restored.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Restore jobs
        restored_count = 0
        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            try:
                self.job_service.restore_job(job_id)
                restored_count += 1
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Restore Failed",
                    f"Failed to restore role: {str(e)}"
                )

        # Reload and show success message
        if restored_count > 0:
            QMessageBox.information(
                self,
                "Restore Successful",
                f"Successfully restored {restored_count} role{'s' if restored_count > 1 else ''}."
            )
            self._load_data()

    def _restore_selected_bullets(self) -> None:
        """Restore selected bullet points."""
        selected_items = self.bullets_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select at least one accomplishment to restore.")
            return

        # Confirm
        count = len(selected_items)
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Are you sure you want to restore {count} accomplishment{'s' if count > 1 else ''}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Restore bullets
        restored_count = 0
        for item in selected_items:
            bullet_id = item.data(Qt.ItemDataRole.UserRole)
            try:
                self.job_service.restore_bullet_point(bullet_id)
                restored_count += 1
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Restore Failed",
                    f"Failed to restore accomplishment: {str(e)}"
                )

        # Reload and show success message
        if restored_count > 0:
            QMessageBox.information(
                self,
                "Restore Successful",
                f"Successfully restored {restored_count} accomplishment{'s' if restored_count > 1 else ''}."
            )
            self._load_data()

    def _permanently_delete_selected_jobs(self) -> None:
        """Permanently delete selected jobs."""
        selected_items = self.jobs_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select at least one role to permanently delete.")
            return

        # Confirm with strong warning
        count = len(selected_items)
        reply = QMessageBox.warning(
            self,
            "Confirm Permanent Deletion",
            f"⚠️ WARNING: This will PERMANENTLY delete {count} role{'s' if count > 1 else ''} "
            "and all associated accomplishments.\n\n"
            "This action CANNOT be undone!\n\n"
            "Are you absolutely sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Permanently delete jobs
        deleted_count = 0
        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            try:
                self.job_service.permanently_delete_job(job_id)
                deleted_count += 1
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Deletion Failed",
                    f"Failed to permanently delete role: {str(e)}"
                )

        # Reload and show success message
        if deleted_count > 0:
            QMessageBox.information(
                self,
                "Deletion Complete",
                f"Permanently deleted {deleted_count} role{'s' if deleted_count > 1 else ''}."
            )
            self._load_data()

    def _permanently_delete_selected_bullets(self) -> None:
        """Permanently delete selected bullet points."""
        selected_items = self.bullets_list.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select at least one accomplishment to permanently delete."
            )
            return

        # Confirm with strong warning
        count = len(selected_items)
        reply = QMessageBox.warning(
            self,
            "Confirm Permanent Deletion",
            f"⚠️ WARNING: This will PERMANENTLY delete {count} accomplishment{'s' if count > 1 else ''}.\n\n"
            "This action CANNOT be undone!\n\n"
            "Are you absolutely sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Permanently delete bullets
        deleted_count = 0
        for item in selected_items:
            bullet_id = item.data(Qt.ItemDataRole.UserRole)
            try:
                self.job_service.permanently_delete_bullet_point(bullet_id)
                deleted_count += 1
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Deletion Failed",
                    f"Failed to permanently delete accomplishment: {str(e)}"
                )

        # Reload and show success message
        if deleted_count > 0:
            QMessageBox.information(
                self,
                "Deletion Complete",
                f"Permanently deleted {deleted_count} accomplishment{'s' if deleted_count > 1 else ''}."
            )
            self._load_data()


__all__ = ["RecentlyDeletedDialog"]
