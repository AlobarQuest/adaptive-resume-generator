"""Applications tracking screen with Kanban and list views.

This screen provides comprehensive job application tracking with two main views:
- Kanban board: Drag-and-drop cards organized by status
- List view: Sortable table with filtering and search

Features:
- Status pipeline visualization
- Interview tracking
- Follow-up management
- Analytics dashboard
- Quick actions (view, edit, delete)
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import date, timedelta

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QComboBox,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QScrollArea,
        QFrame,
        QGridLayout,
        QSplitter,
        QMessageBox,
        QMenu,
        QDateEdit,
        QDialog,
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QDate
    from PyQt6.QtGui import QAction
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen
from adaptive_resume.gui.database_manager import DatabaseManager
from adaptive_resume.services.application_tracking_service import ApplicationTrackingService
from adaptive_resume.models.job_application import JobApplication
from adaptive_resume.models.base import DEFAULT_PROFILE_ID


class ApplicationCard(QFrame):
    """Card widget for displaying application in Kanban view."""

    clicked = pyqtSignal(int)  # Emits application_id
    status_changed = pyqtSignal(int, str)  # Emits application_id, new_status

    def __init__(self, application: JobApplication, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.application = application

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("""
            ApplicationCard {
                background: #2a3a4a;
                border: 1px solid #3a4a5a;
                border-radius: 6px;
                padding: 10px;
                margin: 5px;
            }
            ApplicationCard:hover {
                background: #3a4a5a;
                border: 1px solid #4a5a6a;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        """Build the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Company and position
        company_label = QLabel(f"<b>{self.application.company_name}</b>")
        company_label.setStyleSheet("font-size: 13px; color: #e0e0e0;")
        layout.addWidget(company_label)

        position_label = QLabel(self.application.position_title)
        position_label.setStyleSheet("font-size: 11px; color: #b0b0b0;")
        position_label.setWordWrap(True)
        layout.addWidget(position_label)

        # Priority and dates
        info_layout = QHBoxLayout()

        # Priority badge
        if self.application.priority:
            priority_color = {
                'high': '#ff6666',
                'medium': '#ffaa66',
                'low': '#66ff66'
            }.get(self.application.priority, '#888')

            priority_label = QLabel(f"● {self.application.priority.title()}")
            priority_label.setStyleSheet(f"color: {priority_color}; font-size: 10px;")
            info_layout.addWidget(priority_label)

        info_layout.addStretch()

        # Days since application
        if self.application.days_since_application is not None:
            days_label = QLabel(f"{self.application.days_since_application}d")
            days_label.setStyleSheet("font-size: 10px; color: #888;")
            info_layout.addWidget(days_label)

        layout.addLayout(info_layout)

        # Interview count if any
        if self.application.interview_count and self.application.interview_count > 0:
            interview_label = QLabel(f"📅 {self.application.interview_count} interview(s)")
            interview_label.setStyleSheet("font-size: 10px; color: #88aaff;")
            layout.addWidget(interview_label)

        # Follow-up indicator
        if self.application.needs_follow_up:
            followup_label = QLabel("⚠️ Follow-up due")
            followup_label.setStyleSheet("font-size: 10px; color: #ffaa66; font-weight: bold;")
            layout.addWidget(followup_label)

        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to open detail."""
        self.clicked.emit(self.application.id)


class KanbanColumn(QFrame):
    """Column in Kanban board for a specific status."""

    def __init__(self, status: str, status_label: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.status = status
        self.status_label = status_label
        self.cards: List[ApplicationCard] = []

        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            KanbanColumn {
                background: #1a2332;
                border: 1px solid #2a3342;
                border-radius: 6px;
                padding: 5px;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        """Build column UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"<b>{self.status_label}</b>")
        header.setStyleSheet("font-size: 13px; padding: 10px; color: #e0e0e0;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Card count
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("font-size: 11px; color: #888; padding: 0 10px 10px 10px;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)

    def add_card(self, card: ApplicationCard):
        """Add a card to this column."""
        self.cards.append(card)
        self.cards_layout.insertWidget(len(self.cards) - 1, card)
        self.count_label.setText(str(len(self.cards)))

    def clear_cards(self):
        """Remove all cards."""
        for card in self.cards:
            card.setParent(None)
            card.deleteLater()

        self.cards.clear()
        self.count_label.setText("0")


class ApplicationsScreen(BaseScreen):
    """Main applications tracking screen.

    Features:
    - Kanban board view with status columns
    - List view with sortable table
    - Search and filtering
    - Analytics dashboard
    - Quick actions
    """

    application_selected = pyqtSignal(int)  # Emits application_id
    refresh_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        self.session = DatabaseManager.get_session()
        self.service = ApplicationTrackingService(self.session)
        super().__init__(parent)
        self.load_applications()

    def _setup_ui(self):
        """Build the screen UI."""
        layout = QVBoxLayout(self)

        # Header with title and actions
        header = self._build_header()
        layout.addWidget(header)

        # Filters and search
        filters = self._build_filters()
        layout.addWidget(filters)

        # View tabs (Kanban vs List)
        self.view_tabs = QTabWidget()

        # Kanban view
        self.kanban_view = self._build_kanban_view()
        self.view_tabs.addTab(self.kanban_view, "📊 Kanban Board")

        # List view
        self.list_view = self._build_list_view()
        self.view_tabs.addTab(self.list_view, "📋 List View")

        # Analytics view
        self.analytics_view = self._build_analytics_view()
        self.view_tabs.addTab(self.analytics_view, "📈 Analytics")

        layout.addWidget(self.view_tabs)

    def _build_header(self) -> QWidget:
        """Build header with title and actions."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Title
        title = QLabel("Job Applications")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_applications)
        layout.addWidget(refresh_btn)

        # Add application button
        add_btn = QPushButton("+ New Application")
        add_btn.setObjectName("primaryButton")
        add_btn.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        add_btn.clicked.connect(self._add_application)
        layout.addWidget(add_btn)

        return widget

    def _build_filters(self) -> QWidget:
        """Build filter controls."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search company or position...")
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input, 2)

        # Status filter
        status_label = QLabel("Status:")
        layout.addWidget(status_label)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", None)
        for status in JobApplication.VALID_STATUSES:
            self.status_filter.addItem(status.replace('_', ' ').title(), status)
        self.status_filter.currentIndexChanged.connect(self.load_applications)
        layout.addWidget(self.status_filter)

        # Priority filter
        priority_label = QLabel("Priority:")
        layout.addWidget(priority_label)

        self.priority_filter = QComboBox()
        self.priority_filter.addItem("All Priorities", None)
        for priority in JobApplication.VALID_PRIORITIES:
            self.priority_filter.addItem(priority.title(), priority)
        self.priority_filter.currentIndexChanged.connect(self.load_applications)
        layout.addWidget(self.priority_filter)

        # Active only checkbox
        from PyQt6.QtWidgets import QCheckBox
        self.active_only_check = QCheckBox("Active Only")
        self.active_only_check.setChecked(True)
        self.active_only_check.stateChanged.connect(self.load_applications)
        layout.addWidget(self.active_only_check)

        return widget

    def _build_kanban_view(self) -> QWidget:
        """Build Kanban board view."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Create column for each status
        self.kanban_columns: Dict[str, KanbanColumn] = {}

        for status in JobApplication.VALID_STATUSES:
            status_label = status.replace('_', ' ').title()
            column = KanbanColumn(status, status_label)
            self.kanban_columns[status] = column
            layout.addWidget(column)

        return widget

    def _build_list_view(self) -> QWidget:
        """Build list/table view."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Company", "Position", "Status", "Priority",
            "Applied", "Days", "Interviews", "Actions"
        ])

        # Configure table
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Double-click to view
        self.table.doubleClicked.connect(self._on_table_double_click)

        layout.addWidget(self.table)

        return widget

    def _build_analytics_view(self) -> QWidget:
        """Build analytics dashboard."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Stats grid
        stats_grid = QGridLayout()

        self.stats_labels = {}

        # Define stats to display
        stats = [
            ("total", "Total Applications", 0, 0),
            ("active", "Active", 0, 1),
            ("offers", "Offers", 0, 2),
            ("accepted", "Accepted", 0, 3),
            ("offer_rate", "Offer Rate", 1, 0),
            ("acceptance_rate", "Acceptance Rate", 1, 1),
            ("avg_response", "Avg Response Time", 1, 2),
            ("avg_interviews", "Avg Interviews", 1, 3),
        ]

        for key, label, row, col in stats:
            stat_widget = QFrame()
            stat_widget.setFrameStyle(QFrame.Shape.StyledPanel)
            stat_widget.setStyleSheet("padding: 15px; background: #2a3a4a; border-radius: 6px;")

            stat_layout = QVBoxLayout(stat_widget)

            title_label = QLabel(label)
            title_label.setStyleSheet("font-size: 11px; color: #888;")
            stat_layout.addWidget(title_label)

            value_label = QLabel("0")
            value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #e0e0e0;")
            stat_layout.addWidget(value_label)

            self.stats_labels[key] = value_label
            stats_grid.addWidget(stat_widget, row, col)

        layout.addLayout(stats_grid)

        # Conversion funnel
        funnel_group = QFrame()
        funnel_group.setFrameStyle(QFrame.Shape.StyledPanel)
        funnel_group.setStyleSheet("padding: 15px; background: #2a3a4a; border-radius: 6px; margin-top: 20px;")

        funnel_layout = QVBoxLayout(funnel_group)

        funnel_title = QLabel("<b>Conversion Funnel</b>")
        funnel_title.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        funnel_layout.addWidget(funnel_title)

        self.funnel_labels: Dict[str, QLabel] = {}
        for status in JobApplication.VALID_STATUSES:
            status_label = status.replace('_', ' ').title()
            label = QLabel(f"{status_label}: 0")
            label.setStyleSheet("font-size: 12px; padding: 5px;")
            funnel_layout.addWidget(label)
            self.funnel_labels[status] = label

        layout.addWidget(funnel_group)

        layout.addStretch()

        return widget

    def load_applications(self):
        """Load and display applications."""
        # Get filter values
        status = self.status_filter.currentData()
        priority = self.priority_filter.currentData()
        active_only = self.active_only_check.isChecked()

        # Query applications
        applications = self.service.list_applications(
            profile_id=DEFAULT_PROFILE_ID,
            status=status,
            priority=priority,
            active_only=active_only,
            order_by='updated_at',
            order_direction='desc'
        )

        # Update Kanban view
        self._update_kanban_view(applications)

        # Update list view
        self._update_list_view(applications)

        # Update analytics
        self._update_analytics()

    def _update_kanban_view(self, applications: List[JobApplication]):
        """Update Kanban board with applications."""
        # Clear all columns
        for column in self.kanban_columns.values():
            column.clear_cards()

        # Add cards to appropriate columns
        for app in applications:
            if app.status in self.kanban_columns:
                card = ApplicationCard(app)
                card.clicked.connect(self._view_application_detail)
                self.kanban_columns[app.status].add_card(card)

    def _update_list_view(self, applications: List[JobApplication]):
        """Update list table with applications."""
        self.table.setRowCount(0)

        for i, app in enumerate(applications):
            self.table.insertRow(i)

            # Company
            self.table.setItem(i, 0, QTableWidgetItem(app.company_name or ""))

            # Position
            self.table.setItem(i, 1, QTableWidgetItem(app.position_title or ""))

            # Status
            status_item = QTableWidgetItem(app.status.replace('_', ' ').title())
            self.table.setItem(i, 2, status_item)

            # Priority
            priority = app.priority or "medium"
            priority_item = QTableWidgetItem(priority.title())
            priority_item.setForeground(self._get_priority_color(priority))
            self.table.setItem(i, 3, priority_item)

            # Applied date
            applied_date = app.application_date.strftime("%Y-%m-%d") if app.application_date else "-"
            self.table.setItem(i, 4, QTableWidgetItem(applied_date))

            # Days since application
            days = str(app.days_since_application) if app.days_since_application is not None else "-"
            self.table.setItem(i, 5, QTableWidgetItem(days))

            # Interviews
            interviews = str(app.interview_count or 0)
            self.table.setItem(i, 6, QTableWidgetItem(interviews))

            # Actions button
            actions_btn = QPushButton("⋮")
            actions_btn.setMaximumWidth(30)
            actions_btn.clicked.connect(lambda checked, app_id=app.id: self._show_actions_menu(app_id))
            self.table.setCellWidget(i, 7, actions_btn)

            # Store application ID in row
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, app.id)

    def _update_analytics(self):
        """Update analytics dashboard."""
        stats = self.service.get_statistics(profile_id=DEFAULT_PROFILE_ID)

        # Update stat labels
        self.stats_labels['total'].setText(str(stats['total_applications']))
        self.stats_labels['active'].setText(str(stats['active_applications']))
        self.stats_labels['offers'].setText(str(stats['offers_received']))
        self.stats_labels['accepted'].setText(str(stats['offers_accepted']))
        self.stats_labels['offer_rate'].setText(f"{stats['offer_rate']:.1f}%")
        self.stats_labels['acceptance_rate'].setText(f"{stats['acceptance_rate']:.1f}%")

        avg_response = stats.get('avg_response_time_days')
        self.stats_labels['avg_response'].setText(
            f"{avg_response:.1f}d" if avg_response else "N/A"
        )

        self.stats_labels['avg_interviews'].setText(
            f"{stats['avg_interviews_per_app']:.1f}"
        )

        # Update funnel
        funnel = self.service.get_conversion_funnel(profile_id=DEFAULT_PROFILE_ID)
        for status, label in self.funnel_labels.items():
            count = funnel.get(status, 0)
            status_label = status.replace('_', ' ').title()
            label.setText(f"{status_label}: {count}")

    def _get_priority_color(self, priority: str):
        """Get color for priority."""
        from PyQt6.QtGui import QColor
        colors = {
            'high': QColor(255, 102, 102),
            'medium': QColor(255, 170, 102),
            'low': QColor(102, 255, 102)
        }
        return colors.get(priority, QColor(136, 136, 136))

    def _on_search_changed(self):
        """Handle search text change."""
        # TODO: Implement search filtering
        pass

    def _on_table_double_click(self, index):
        """Handle table row double-click."""
        row = index.row()
        app_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._view_application_detail(app_id)

    def _view_application_detail(self, application_id: int):
        """View application detail."""
        from adaptive_resume.gui.dialogs import ApplicationDetailDialog

        dialog = ApplicationDetailDialog(application_id, parent=self)
        dialog.application_updated.connect(lambda: self.load_applications())

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_applications()

        self.application_selected.emit(application_id)

    def _show_actions_menu(self, application_id: int):
        """Show actions context menu."""
        menu = QMenu(self)

        view_action = QAction("View Details", self)
        view_action.triggered.connect(lambda: self._view_application_detail(application_id))
        menu.addAction(view_action)

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self._edit_application(application_id))
        menu.addAction(edit_action)

        menu.addSeparator()

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_application(application_id))
        menu.addAction(delete_action)

        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))

    def _add_application(self):
        """Add new application."""
        from adaptive_resume.gui.dialogs import AddApplicationDialog

        dialog = AddApplicationDialog(DEFAULT_PROFILE_ID, parent=self)
        dialog.application_created.connect(lambda app_id: self.load_applications())

        dialog.exec()

    def _edit_application(self, application_id: int):
        """Edit application."""
        # Same as view detail - the dialog handles editing
        self._view_application_detail(application_id)

    def _delete_application(self, application_id: int):
        """Delete application."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.service.delete_application(application_id)
            self.load_applications()

    def on_screen_shown(self) -> None:
        """Refresh data when screen is shown."""
        self.load_applications()


__all__ = ['ApplicationsScreen']
