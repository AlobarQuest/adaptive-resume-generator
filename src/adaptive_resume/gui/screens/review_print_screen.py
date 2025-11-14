"""Review and print documents screen (Phase 5 placeholder)."""

from __future__ import annotations

from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QScrollArea,
    )
    from PyQt6.QtCore import Qt
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from .base_screen import BaseScreen


class ReviewPrintScreen(BaseScreen):
    """Screen for reviewing and printing documents."""

    def __init__(
        self,
        parent: Optional[QWidget] = None
    ) -> None:
        self.current_profile_id: Optional[int] = None
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Setup the review/print screen UI."""
        # Main layout for the screen
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header = QLabel("Review & Print")
        header.setObjectName("screenTitle")
        layout.addWidget(header)

        # Description
        description = QLabel(
            "Preview your tailored resume and export it as a PDF or print directly."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #ccc; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(description)

        # Preview area placeholder
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        preview_frame.setMinimumHeight(500)

        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.setSpacing(15)

        preview_icon = QLabel("📄")
        preview_icon.setStyleSheet("font-size: 64px; color: #999;")
        preview_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_icon)

        preview_title = QLabel("Document Preview")
        preview_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        preview_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_title)

        preview_text = QLabel("Your tailored resume will appear here")
        preview_text.setStyleSheet("color: #999; font-size: 14px;")
        preview_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_text)

        layout.addWidget(preview_frame)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        template_btn = QPushButton("📋 Select Template")
        template_btn.setEnabled(False)
        template_btn.setMinimumHeight(45)
        template_btn.setStyleSheet("padding: 10px 20px; font-size: 12px;")
        button_layout.addWidget(template_btn)

        export_btn = QPushButton("📥 Export PDF")
        export_btn.setEnabled(False)
        export_btn.setMinimumHeight(45)
        export_btn.setStyleSheet("padding: 10px 20px; font-size: 12px;")
        button_layout.addWidget(export_btn)

        print_btn = QPushButton("🖨️ Print")
        print_btn.setEnabled(False)
        print_btn.setMinimumHeight(45)
        print_btn.setStyleSheet("padding: 10px 20px; font-size: 12px;")
        button_layout.addWidget(print_btn)

        layout.addLayout(button_layout)

        # Coming soon message
        coming_soon_frame = QFrame()
        coming_soon_frame.setStyleSheet(
            "background-color: #2a3f5f; "
            "border: 2px solid #4a90e2; "
            "border-radius: 8px; "
            "padding: 20px;"
        )
        coming_soon_layout = QVBoxLayout(coming_soon_frame)

        coming_soon_icon = QLabel("🚧")
        coming_soon_icon.setStyleSheet("font-size: 24px;")
        coming_soon_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon_layout.addWidget(coming_soon_icon)

        coming_soon_title = QLabel("Coming in Phase 5")
        coming_soon_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a90e2;")
        coming_soon_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon_layout.addWidget(coming_soon_title)

        coming_soon_text = QLabel(
            "This feature will allow you to:\n"
            "• Select from professional resume templates\n"
            "• Preview your tailored resume in real-time\n"
            "• Export as PDF with proper formatting\n"
            "• Print directly to your printer"
        )
        coming_soon_text.setWordWrap(True)
        coming_soon_text.setStyleSheet("color: #ccc; font-size: 12px;")
        coming_soon_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon_layout.addWidget(coming_soon_text)

        layout.addWidget(coming_soon_frame)

        layout.addStretch()

        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)

        # Add scroll area to main layout
        main_layout.addWidget(scroll)

    def set_profile(self, profile_id: int) -> None:
        """Set the current profile."""
        self.current_profile_id = profile_id


__all__ = ["ReviewPrintScreen"]
