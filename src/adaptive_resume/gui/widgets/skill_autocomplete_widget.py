"""
Skill Autocomplete Widget - Autocomplete input with skill suggestions.

Provides type-ahead suggestions from the skill database with fuzzy matching,
keyboard navigation, and skill previews.
"""

from typing import Optional, List

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QVBoxLayout,
        QLabel,
        QFrame,
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QKeyEvent
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.services.skill_database_service import (
    SkillDatabaseService,
    SkillSuggestion,
)


class SkillAutocompleteWidget(QWidget):
    """
    Autocomplete widget for skill selection with fuzzy search.

    Features:
    - Type-ahead suggestions from skill database
    - Fuzzy matching for typo tolerance
    - Keyboard navigation (Up/Down arrows, Enter, Escape)
    - Skill preview on hover
    - Category filtering
    - Custom skill option

    Signals:
        skill_selected: Emitted when a skill is selected (skill_name, skill_id)
        custom_skill_requested: Emitted when user wants to add custom skill
    """

    # Signals
    skill_selected = pyqtSignal(str, object)  # skill_name, skill_id (or None for custom)
    custom_skill_requested = pyqtSignal(str)  # skill_name for custom skill

    def __init__(
        self,
        skill_service: SkillDatabaseService,
        parent: Optional[QWidget] = None,
        placeholder: str = "Type to search skills...",
        category_filter: Optional[str] = None,
    ) -> None:
        """
        Initialize the autocomplete widget.

        Args:
            skill_service: SkillDatabaseService instance
            parent: Parent widget
            placeholder: Placeholder text for input
            category_filter: Optional category to filter suggestions
        """
        super().__init__(parent)
        self.skill_service = skill_service
        self.category_filter = category_filter
        self._search_delay_ms = 150  # Debounce delay
        self._min_chars = 1  # Minimum characters to trigger search

        self._setup_ui(placeholder)
        self._setup_connections()
        self._setup_timer()

    def _setup_ui(self, placeholder: str) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setClearButtonEnabled(True)
        layout.addWidget(self.input_field)

        # Dropdown container with frame
        self.dropdown_frame = QFrame()
        self.dropdown_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.dropdown_frame.setVisible(False)  # Hidden by default

        dropdown_layout = QVBoxLayout(self.dropdown_frame)
        dropdown_layout.setContentsMargins(0, 0, 0, 0)
        dropdown_layout.setSpacing(0)

        # Suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(200)
        self.suggestions_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        dropdown_layout.addWidget(self.suggestions_list)

        # Skill preview label (shown on hover)
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        self.preview_label.setVisible(False)
        dropdown_layout.addWidget(self.preview_label)

        layout.addWidget(self.dropdown_frame)

    def _setup_connections(self) -> None:
        """Connect signals and slots."""
        self.input_field.textChanged.connect(self._on_text_changed)
        self.input_field.returnPressed.connect(self._on_return_pressed)
        self.suggestions_list.itemClicked.connect(self._on_item_clicked)
        self.suggestions_list.currentRowChanged.connect(self._on_item_hovered)

        # Install event filter for keyboard navigation
        self.input_field.installEventFilter(self)

    def _setup_timer(self) -> None:
        """Set up debounce timer for search."""
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)

    def _on_text_changed(self, text: str) -> None:
        """Handle text change in input field."""
        # Stop any pending search
        self._search_timer.stop()

        if len(text) < self._min_chars:
            self._hide_dropdown()
            return

        # Start debounce timer
        self._search_timer.start(self._search_delay_ms)

    def _perform_search(self) -> None:
        """Perform the actual search with current input text."""
        query = self.input_field.text().strip()

        if len(query) < self._min_chars:
            self._hide_dropdown()
            return

        # Search for skills
        suggestions = self.skill_service.search_skills(
            query,
            limit=10,
            category_filter=self.category_filter
        )

        self._show_suggestions(suggestions)

    def _show_suggestions(self, suggestions: List[SkillSuggestion]) -> None:
        """Display suggestions in dropdown."""
        self.suggestions_list.clear()

        if not suggestions:
            # No matches - offer custom skill option
            self._add_custom_skill_item()
            self._show_dropdown()
            return

        # Add suggestion items
        for suggestion in suggestions:
            self._add_suggestion_item(suggestion)

        # Add "Add custom skill" option at the end
        self._add_custom_skill_item()

        self._show_dropdown()

    def _add_suggestion_item(self, suggestion: SkillSuggestion) -> None:
        """Add a suggestion item to the list."""
        # Format display text
        display_text = suggestion.name

        # Add category badge if showing multiple categories
        if not self.category_filter:
            display_text += f"  [{suggestion.category}]"

        # Add trending indicator
        if suggestion.trending:
            display_text += " 🔥"

        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, suggestion)  # Store suggestion data
        self.suggestions_list.addItem(item)

    def _add_custom_skill_item(self) -> None:
        """Add 'Add custom skill' option."""
        custom_text = f'Add custom skill: "{self.input_field.text()}"'
        item = QListWidgetItem(custom_text)
        item.setData(Qt.ItemDataRole.UserRole, None)  # None indicates custom skill
        item.setForeground(Qt.GlobalColor.gray)
        self.suggestions_list.addItem(item)

    def _show_dropdown(self) -> None:
        """Show the dropdown with suggestions."""
        if self.suggestions_list.count() > 0:
            self.dropdown_frame.setVisible(True)
            self.suggestions_list.setCurrentRow(0)  # Select first item

    def _hide_dropdown(self) -> None:
        """Hide the dropdown."""
        self.dropdown_frame.setVisible(False)
        self.preview_label.setVisible(False)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item selection."""
        suggestion = item.data(Qt.ItemDataRole.UserRole)

        if suggestion is None:
            # Custom skill
            skill_name = self.input_field.text().strip()
            self.custom_skill_requested.emit(skill_name)
            self.skill_selected.emit(skill_name, None)
            # Keep the custom skill name in the input field
        else:
            # Database skill
            # Set input field to selected skill name (don't clear it!)
            self.input_field.setText(suggestion.name)
            self.skill_selected.emit(suggestion.name, suggestion.id)

        # Hide dropdown (but don't clear input - user can see what they selected)
        self._hide_dropdown()

    def _on_item_hovered(self, row: int) -> None:
        """Show skill preview when hovering over item."""
        if row < 0:
            self.preview_label.setVisible(False)
            return

        item = self.suggestions_list.item(row)
        suggestion = item.data(Qt.ItemDataRole.UserRole)

        if suggestion is None:
            # Custom skill - no preview
            self.preview_label.setVisible(False)
            return

        # Show skill details
        preview_text = f"<b>{suggestion.name}</b><br>"
        preview_text += f"<i>{suggestion.description}</i><br>"
        preview_text += f"Difficulty: {suggestion.difficulty_level.title()} | "
        preview_text += f"Category: {suggestion.subcategory}"

        self.preview_label.setText(preview_text)
        self.preview_label.setVisible(True)

    def _on_return_pressed(self) -> None:
        """Handle Enter key in input field."""
        if self.dropdown_frame.isVisible() and self.suggestions_list.count() > 0:
            # Select currently highlighted item
            current_item = self.suggestions_list.currentItem()
            if current_item:
                self._on_item_clicked(current_item)
        else:
            # No dropdown - treat as custom skill
            skill_name = self.input_field.text().strip()
            if skill_name:
                self.custom_skill_requested.emit(skill_name)
                self.skill_selected.emit(skill_name, None)
                # Keep the custom skill name in the input field

    def eventFilter(self, obj, event) -> bool:
        """Handle keyboard events for navigation."""
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            key_event = event

            # Only handle keyboard nav if dropdown is visible
            if not self.dropdown_frame.isVisible():
                return False

            key = key_event.key()

            if key == Qt.Key.Key_Down:
                # Move down in list
                current_row = self.suggestions_list.currentRow()
                if current_row < self.suggestions_list.count() - 1:
                    self.suggestions_list.setCurrentRow(current_row + 1)
                return True

            elif key == Qt.Key.Key_Up:
                # Move up in list
                current_row = self.suggestions_list.currentRow()
                if current_row > 0:
                    self.suggestions_list.setCurrentRow(current_row - 1)
                return True

            elif key == Qt.Key.Key_Escape:
                # Hide dropdown
                self._hide_dropdown()
                return True

        return False

    def set_category_filter(self, category: Optional[str]) -> None:
        """
        Set category filter for suggestions.

        Args:
            category: Category name to filter by, or None for all categories
        """
        self.category_filter = category
        # Refresh suggestions if dropdown is visible
        if self.dropdown_frame.isVisible():
            self._perform_search()

    def clear(self) -> None:
        """Clear the input field and hide dropdown."""
        self.input_field.clear()
        self._hide_dropdown()

    def set_text(self, text: str) -> None:
        """Set input field text."""
        self.input_field.setText(text)

    def text(self) -> str:
        """Get current input field text."""
        return self.input_field.text()

    def focusInEvent(self, event) -> None:
        """Forward focus to input field."""
        self.input_field.setFocus()
        super().focusInEvent(event)
