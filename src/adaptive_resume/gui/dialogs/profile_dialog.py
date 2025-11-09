"""Dialog for creating or editing profile information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLineEdit,
        QTextEdit,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc


@dataclass
class ProfileDialogResult:
    """Return payload describing profile data from the dialog."""

    first_name: str
    last_name: str
    email: str
    phone: str
    city: str
    state: str
    linkedin_url: str
    portfolio_url: str
    professional_summary: str


class ProfileDialog(QDialog):
    """Simple dialog to gather profile information."""

    def __init__(self, parent: Optional[QWidget] = None, profile: Optional[dict] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Profile")
        self._build_form()
        if profile:
            self._load_profile(profile)

    def _build_form(self) -> None:
        layout = QFormLayout(self)

        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.city = QLineEdit()
        self.state = QLineEdit()
        self.linkedin_url = QLineEdit()
        self.portfolio_url = QLineEdit()
        self.summary = QTextEdit()
        self.summary.setMaximumHeight(120)

        layout.addRow("First Name", self.first_name)
        layout.addRow("Last Name", self.last_name)
        layout.addRow("Email", self.email)
        layout.addRow("Phone", self.phone)
        layout.addRow("City", self.city)
        layout.addRow("State", self.state)
        layout.addRow("LinkedIn", self.linkedin_url)
        layout.addRow("Portfolio", self.portfolio_url)
        layout.addRow("Summary", self.summary)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def _load_profile(self, profile: dict) -> None:
        self.first_name.setText(profile.get("first_name", ""))
        self.last_name.setText(profile.get("last_name", ""))
        self.email.setText(profile.get("email", ""))
        self.phone.setText(profile.get("phone", ""))
        self.city.setText(profile.get("city", ""))
        self.state.setText(profile.get("state", ""))
        self.linkedin_url.setText(profile.get("linkedin_url", ""))
        self.portfolio_url.setText(profile.get("portfolio_url", ""))
        self.summary.setPlainText(profile.get("professional_summary", ""))

    def get_result(self) -> ProfileDialogResult:
        """Return the captured profile data."""
        return ProfileDialogResult(
            first_name=self.first_name.text().strip(),
            last_name=self.last_name.text().strip(),
            email=self.email.text().strip(),
            phone=self.phone.text().strip(),
            city=self.city.text().strip(),
            state=self.state.text().strip(),
            linkedin_url=self.linkedin_url.text().strip(),
            portfolio_url=self.portfolio_url.text().strip(),
            professional_summary=self.summary.toPlainText().strip(),
        )
