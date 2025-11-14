"""Dialog for managing company information."""

from __future__ import annotations

from typing import Optional, NamedTuple

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QFormLayout,
    )
    from PyQt6.QtCore import Qt
except ImportError as exc:
    raise ImportError("PyQt6 is required to use the GUI components") from exc


class CompanyData(NamedTuple):
    """Company data container."""
    name: str
    location: str


class CompanyDialog(QDialog):
    """Dialog for adding or editing company information."""

    def __init__(
        self,
        parent=None,
        company_name: str = "",
        company_location: str = "",
    ):
        super().__init__(parent)
        self.setWindowTitle("Company Information")
        self.setMinimumWidth(400)

        self._company_name = company_name
        self._company_location = company_location

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Form layout for inputs
        form = QFormLayout()

        # Company name
        self.name_input = QLineEdit()
        self.name_input.setText(self._company_name)
        self.name_input.setPlaceholderText("e.g., Acme Corporation")
        form.addRow("Company Name*:", self.name_input)

        # Location
        self.location_input = QLineEdit()
        self.location_input.setText(self._company_location)
        self.location_input.setPlaceholderText("e.g., San Francisco, CA")
        form.addRow("Location:", self.location_input)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _on_save(self) -> None:
        """Handle save button click."""
        name = self.name_input.text().strip()

        if not name:
            self.name_input.setFocus()
            return

        self.accept()

    def get_result(self) -> CompanyData:
        """Get the company data."""
        return CompanyData(
            name=self.name_input.text().strip(),
            location=self.location_input.text().strip(),
        )


__all__ = ["CompanyDialog", "CompanyData"]
