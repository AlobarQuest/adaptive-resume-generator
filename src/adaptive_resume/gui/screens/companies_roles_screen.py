"""Companies and Roles management screen."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QSplitter,
        QPushButton,
        QListWidget,
        QListWidgetItem,
        QFrame,
        QScrollArea,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from ..views import JobsView


class CompaniesRolesScreen(BaseScreen):
    """Screen for managing companies and job roles."""

    # Signals for company management
    edit_company_requested = pyqtSignal()
    delete_company_requested = pyqtSignal()

    # Signals for job management
    add_job_requested = pyqtSignal()
    edit_job_requested = pyqtSignal()
    delete_job_requested = pyqtSignal()
    view_recently_deleted_requested = pyqtSignal()

    def __init__(
        self,
        job_service=None,
        parent: Optional[QWidget] = None
    ) -> None:
        self.job_service = job_service
        self.current_profile_id: Optional[int] = None
        self.selected_company: Optional[str] = None
        self.all_jobs = []
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the companies/roles screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header
        header = QLabel("Companies and Roles")
        header.setObjectName("screenTitle")
        layout.addWidget(header)

        # Main content with horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Companies list
        left_panel = self._create_companies_panel()
        splitter.addWidget(left_panel)

        # Right panel - Roles and highlights
        right_panel = self._create_roles_panel()
        splitter.addWidget(right_panel)

        # Set initial sizes (30% / 70%)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        layout.addWidget(splitter)

    def _create_companies_panel(self) -> QWidget:
        """Create the left panel for companies."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Panel title
        title = QLabel("Companies")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Company action buttons
        btn_layout = QHBoxLayout()

        edit_company_btn = QPushButton("✏️ Edit")
        edit_company_btn.clicked.connect(self.edit_company_requested.emit)
        btn_layout.addWidget(edit_company_btn)

        delete_company_btn = QPushButton("🗑️ Delete")
        delete_company_btn.clicked.connect(self.delete_company_requested.emit)
        btn_layout.addWidget(delete_company_btn)

        layout.addLayout(btn_layout)

        # Companies list
        self.companies_list = QListWidget()
        self.companies_list.itemClicked.connect(self._on_company_selected)
        layout.addWidget(self.companies_list)

        return panel

    def _create_roles_panel(self) -> QWidget:
        """Create the right panel for roles and highlights."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Roles section
        roles_header_layout = QHBoxLayout()

        roles_title = QLabel("Roles")
        roles_title.setObjectName("sectionTitle")
        roles_header_layout.addWidget(roles_title)

        roles_header_layout.addStretch()

        # Add/Edit/Delete job buttons
        add_job_btn = QPushButton("➕ Add Role")
        add_job_btn.clicked.connect(self.add_job_requested.emit)
        roles_header_layout.addWidget(add_job_btn)

        edit_job_btn = QPushButton("✏️ Edit Role")
        edit_job_btn.clicked.connect(self.edit_job_requested.emit)
        roles_header_layout.addWidget(edit_job_btn)

        delete_job_btn = QPushButton("🗑️ Delete Role")
        delete_job_btn.clicked.connect(self.delete_job_requested.emit)
        delete_job_btn.setToolTip("Delete the selected role")
        roles_header_layout.addWidget(delete_job_btn)

        # View recently deleted button
        view_deleted_btn = QPushButton("♻️ Recently Deleted")
        view_deleted_btn.clicked.connect(self.view_recently_deleted_requested.emit)
        view_deleted_btn.setToolTip("View and restore recently deleted roles and accomplishments")
        roles_header_layout.addWidget(view_deleted_btn)

        layout.addLayout(roles_header_layout)

        # Jobs view for filtered roles
        self.jobs_view = JobsView()
        layout.addWidget(self.jobs_view)

        return panel

    def _on_company_selected(self, item: QListWidgetItem) -> None:
        """Handle company selection."""
        self.selected_company = item.text().split('\n')[0]  # Get company name (first line)
        self._filter_and_display_roles()

    def _filter_and_display_roles(self) -> None:
        """Filter roles by selected company and display them."""
        if not self.selected_company:
            self.jobs_view.set_jobs([])
            return

        # Filter jobs by selected company
        filtered_jobs = [
            job for job in self.all_jobs
            if job.company_name == self.selected_company
        ]

        # Sort by start_date descending (newest first)
        filtered_jobs.sort(key=lambda j: j.start_date if j.start_date else '', reverse=True)

        self.jobs_view.set_jobs(filtered_jobs)

    def set_profile(self, profile_id: int) -> None:
        """Set the current profile and load data."""
        self.current_profile_id = profile_id
        self._load_companies()

    def _load_companies(self) -> None:
        """Load and display all companies."""
        if not self.current_profile_id or not self.job_service:
            self.companies_list.clear()
            self.jobs_view.set_jobs([])
            return

        # Get all jobs for the profile
        self.all_jobs = self.job_service.get_jobs_for_profile(self.current_profile_id)

        # Extract unique companies with their locations and role counts
        companies_dict = {}
        for job in self.all_jobs:
            company_name = job.company_name
            if company_name not in companies_dict:
                companies_dict[company_name] = {
                    'location': job.location or '',
                    'count': 0
                }
            companies_dict[company_name]['count'] += 1

        # Sort companies alphabetically
        sorted_companies = sorted(companies_dict.items())

        # Populate the companies list
        self.companies_list.clear()
        for company_name, info in sorted_companies:
            location = info['location']
            count = info['count']

            # Create multi-line display
            display_text = f"{company_name}\n"
            if location:
                display_text += f"{location}\n"
            display_text += f"{count} role(s)"

            item = QListWidgetItem(display_text)
            self.companies_list.addItem(item)

        # Select first company if available
        if self.companies_list.count() > 0:
            self.companies_list.setCurrentRow(0)
            first_company = sorted_companies[0][0]
            self.selected_company = first_company
            self._filter_and_display_roles()

    def get_jobs_view(self) -> JobsView:
        """Get the jobs view for connecting signals."""
        return self.jobs_view

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        if self.current_profile_id:
            self._load_companies()


__all__ = ["CompaniesRolesScreen"]
