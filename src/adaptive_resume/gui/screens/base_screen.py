"""Base screen classes for the Adaptive Resume Generator."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc


class BaseScreen(QWidget):
    """Base class for all main screens."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the screen UI. Override in subclasses."""
        layout = QVBoxLayout(self)
        label = QLabel("Base Screen")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
    
    def on_screen_shown(self) -> None:
        """Called when this screen becomes visible. Override in subclasses."""
        pass
    
    def on_screen_hidden(self) -> None:
        """Called when this screen is hidden. Override in subclasses."""
        pass


__all__ = ["BaseScreen"]
