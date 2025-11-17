"""Navigation menu widget for the Adaptive Resume Generator."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QPushButton,
        QLabel,
        QFrame,
    )
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc


class NavigationMenu(QWidget):
    """Fixed left-side navigation menu."""
    
    # Signals for navigation
    screen_changed = pyqtSignal(str)  # Emits screen name
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_screen = "dashboard"
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the navigation menu UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # App logo/title
        title_label = QLabel("Adaptive Resume")
        title_label.setObjectName("navTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setMinimumHeight(60)
        layout.addWidget(title_label)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setObjectName("navSeparator")
        layout.addWidget(separator1)
        
        # Main navigation buttons
        self.buttons = {}

        nav_items = [
            ("dashboard", "📊 Dashboard"),
            ("profile", "👤 Profile Management"),
            ("companies", "🏢 Companies and Roles"),
            ("education", "🎓 Manage Education"),
            ("skills", "🎯 Manage Skills"),
            ("upload", "📄 Upload Job Posting"),
            ("applications", "📝 Track Applications"),
            ("review", "📋 Review and Print"),
        ]
        
        for screen_id, label_text in nav_items:
            btn = QPushButton(label_text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setMinimumHeight(50)
            btn.clicked.connect(lambda checked, s=screen_id: self._on_button_clicked(s))
            self.buttons[screen_id] = btn
            layout.addWidget(btn)
        
        # Set dashboard as default
        self.buttons["dashboard"].setChecked(True)
        
        # Spacer to push settings to bottom
        layout.addStretch()
        
        # Separator before settings
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setObjectName("navSeparator")
        layout.addWidget(separator2)
        
        # Settings button at bottom
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setObjectName("navButton")
        settings_btn.setMinimumHeight(50)
        settings_btn.clicked.connect(lambda: self.screen_changed.emit("settings"))
        layout.addWidget(settings_btn)
        
        # Fixed width for navigation
        self.setFixedWidth(200)
        self.setObjectName("navigationMenu")
    
    def _on_button_clicked(self, screen_id: str) -> None:
        """Handle navigation button click."""
        # Uncheck all buttons except the clicked one
        for btn_id, btn in self.buttons.items():
            btn.setChecked(btn_id == screen_id)
        
        self._current_screen = screen_id
        self.screen_changed.emit(screen_id)
    
    def set_current_screen(self, screen_id: str) -> None:
        """Set the current screen programmatically."""
        if screen_id in self.buttons:
            self._on_button_clicked(screen_id)
    
    def get_current_screen(self) -> str:
        """Get the current screen ID."""
        return self._current_screen


__all__ = ["NavigationMenu"]
