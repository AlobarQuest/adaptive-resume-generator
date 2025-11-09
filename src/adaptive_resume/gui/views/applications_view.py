"""Placeholder applications view for future expansion."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc


class ApplicationsView(QWidget):
    """Simple view that reserves space for application tracking."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        placeholder = QLabel(
            "Application tracking will appear here once matching is complete."
        )
        placeholder.setWordWrap(True)
        layout.addWidget(placeholder)
