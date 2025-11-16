"""
Skill Chip Widget - Display a skill as a removable, colored chip.

Shows skills as compact badges with category-based colors, remove buttons,
and optional proficiency indicators.
"""

from typing import Optional, Dict

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QLabel,
        QPushButton,
        QHBoxLayout,
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QSize
    from PyQt6.QtGui import QPalette, QColor
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc


# Color mapping for different skill categories
CATEGORY_COLORS: Dict[str, str] = {
    "Programming Languages": "#3B82F6",  # Blue
    "Frameworks & Libraries": "#8B5CF6",  # Purple
    "Databases & Data Storage": "#10B981",  # Green
    "Cloud Platforms": "#F59E0B",  # Orange
    "DevOps & Infrastructure": "#EF4444",  # Red
    "Tools & Software": "#6366F1",  # Indigo
    "Testing & QA": "#14B8A6",  # Teal
    "Data Science & ML": "#8B5CF6",  # Purple
    "Design & UX": "#EC4899",  # Pink
    "Soft Skills": "#06B6D4",  # Cyan
    "Domain Knowledge": "#84CC16",  # Lime
    "Security & Compliance": "#DC2626",  # Dark Red
    "Operating Systems": "#64748B",  # Slate
    "Methodologies": "#059669",  # Emerald
    "default": "#6B7280",  # Gray
}


class SkillChipWidget(QWidget):
    """
    Chip widget for displaying a selected skill.

    Features:
    - Category-based color coding
    - Remove button (X)
    - Optional proficiency indicator
    - Click to edit
    - Compact, badge-like appearance

    Signals:
        remove_requested: Emitted when user clicks remove button
        edit_requested: Emitted when user clicks on the chip
    """

    # Signals
    remove_requested = pyqtSignal()  # Request to remove this chip
    edit_requested = pyqtSignal()  # Request to edit this skill

    def __init__(
        self,
        skill_name: str,
        category: Optional[str] = None,
        proficiency_level: Optional[str] = None,
        years_experience: Optional[float] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the skill chip.

        Args:
            skill_name: Name of the skill
            category: Skill category for color coding
            proficiency_level: Optional proficiency level to display
            years_experience: Optional years of experience
            parent: Parent widget
        """
        super().__init__(parent)

        self.skill_name = skill_name
        self.category = category or "default"
        self.proficiency_level = proficiency_level
        self.years_experience = years_experience

        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self) -> None:
        """Set up the chip UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(4)

        # Skill name label
        self.skill_label = QLabel(self._format_skill_text())
        self.skill_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.skill_label)

        # Remove button
        self.remove_btn = QPushButton("×")  # Unicode multiply sign
        self.remove_btn.setFixedSize(QSize(16, 16))
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
            }
        """)
        self.remove_btn.clicked.connect(self.remove_requested.emit)
        layout.addWidget(self.remove_btn)

        # Make the chip clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _format_skill_text(self) -> str:
        """Format the skill text with optional proficiency info."""
        text = self.skill_name

        # Add proficiency badge if available
        if self.proficiency_level:
            level_abbrev = self._get_proficiency_abbreviation(self.proficiency_level)
            text += f" ({level_abbrev})"

        # Add years if available
        if self.years_experience and self.years_experience > 0:
            years = int(self.years_experience) if self.years_experience >= 1 else self.years_experience
            text += f" · {years}y"

        return text

    def _get_proficiency_abbreviation(self, level: str) -> str:
        """Get abbreviated proficiency level."""
        abbrev_map = {
            "Beginner": "Beg",
            "Intermediate": "Int",
            "Advanced": "Adv",
            "Expert": "Exp",
        }
        return abbrev_map.get(level, level)

    def _apply_styling(self) -> None:
        """Apply category-based color styling."""
        # Get color for category
        color = CATEGORY_COLORS.get(self.category, CATEGORY_COLORS["default"])

        # Apply rounded chip style with category color
        self.setStyleSheet(f"""
            SkillChipWidget {{
                background-color: {color};
                border-radius: 12px;
                color: white;
                font-size: 13px;
                font-weight: 500;
            }}
            SkillChipWidget:hover {{
                background-color: {self._darken_color(color)};
            }}
        """)

        # Set fixed height for consistent appearance
        self.setFixedHeight(24)

    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color by a factor (for hover effect)."""
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Darken
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)

        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def mousePressEvent(self, event) -> None:
        """Handle click on chip (not on remove button)."""
        # Check if click was on remove button
        if self.remove_btn.geometry().contains(event.pos()):
            return  # Let button handle it

        # Emit edit request
        self.edit_requested.emit()

    def update_proficiency(self, proficiency_level: Optional[str], years: Optional[float]) -> None:
        """
        Update proficiency information.

        Args:
            proficiency_level: New proficiency level
            years: New years of experience
        """
        self.proficiency_level = proficiency_level
        self.years_experience = years
        self.skill_label.setText(self._format_skill_text())

    def set_category(self, category: str) -> None:
        """
        Update the category and re-apply styling.

        Args:
            category: New category name
        """
        self.category = category
        self._apply_styling()

    def sizeHint(self) -> QSize:
        """Return recommended size for the chip."""
        # Calculate width based on text length
        text_width = self.skill_label.fontMetrics().horizontalAdvance(
            self.skill_label.text()
        )
        return QSize(text_width + 40, 24)  # Add padding for margins and button


class SkillChipContainer(QWidget):
    """
    Container widget for displaying multiple skill chips in a flow layout.

    Displays skills as chips that wrap to multiple lines as needed.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the chip container.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.chips: list[SkillChipWidget] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the container UI."""
        from PyQt6.QtWidgets import QHBoxLayout

        # Use flow layout (wrapping horizontal layout)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(6)
        self.layout.addStretch()

    def add_chip(
        self,
        skill_name: str,
        category: Optional[str] = None,
        proficiency_level: Optional[str] = None,
        years_experience: Optional[float] = None,
    ) -> SkillChipWidget:
        """
        Add a skill chip to the container.

        Args:
            skill_name: Name of the skill
            category: Skill category
            proficiency_level: Optional proficiency level
            years_experience: Optional years of experience

        Returns:
            The created SkillChipWidget
        """
        chip = SkillChipWidget(
            skill_name=skill_name,
            category=category,
            proficiency_level=proficiency_level,
            years_experience=years_experience,
        )

        # Insert before stretch
        self.layout.insertWidget(len(self.chips), chip)
        self.chips.append(chip)

        return chip

    def remove_chip(self, chip: SkillChipWidget) -> None:
        """
        Remove a chip from the container.

        Args:
            chip: Chip widget to remove
        """
        if chip in self.chips:
            self.chips.remove(chip)
            self.layout.removeWidget(chip)
            chip.deleteLater()

    def clear(self) -> None:
        """Remove all chips from the container."""
        for chip in list(self.chips):  # Copy list to avoid modification during iteration
            self.remove_chip(chip)

    def get_chips(self) -> list[SkillChipWidget]:
        """Get list of all chips in the container."""
        return self.chips.copy()
