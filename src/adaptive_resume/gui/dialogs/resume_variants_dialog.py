"""Dialog for managing resume variants for a job posting."""

from __future__ import annotations

from typing import Optional, List
import json

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QGroupBox,
        QComboBox,
        QTextEdit,
        QMessageBox,
        QHeaderView,
        QAbstractItemView,
        QInputDialog,
        QWidget,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QIcon
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyQt6 is required to use the GUI components") from exc

from adaptive_resume.services import ResumeVariantService, VariantComparison
from adaptive_resume.models.tailored_resume import TailoredResumeModel
from adaptive_resume.gui.database_manager import DatabaseManager


# Predefined variant strategies
VARIANT_STRATEGIES = {
    "Conservative": {
        "description": "Fewer bullets, proven accomplishments only, traditional focus",
        "notes": "Conservative approach with only the strongest, most relevant accomplishments."
    },
    "Comprehensive": {
        "description": "All relevant experience, detailed descriptions",
        "notes": "Comprehensive variant including all relevant accomplishments and details."
    },
    "Technical": {
        "description": "Focus on technical skills, metrics, and tools",
        "notes": "Technical-focused variant emphasizing skills, technologies, and quantifiable results."
    },
    "Leadership": {
        "description": "Emphasize people management and strategic thinking",
        "notes": "Leadership-oriented variant highlighting management and strategic accomplishments."
    },
    "Results-Driven": {
        "description": "Focus on measurable outcomes and impact",
        "notes": "Results-focused variant showcasing quantifiable achievements and business impact."
    },
    "Custom": {
        "description": "Create your own custom variant",
        "notes": ""
    }
}


class ResumeVariantsDialog(QDialog):
    """Dialog for managing multiple resume variants for a job posting.

    Features:
    - List all variants for a job posting
    - Create new variants (predefined strategies or custom)
    - Edit variant details (name, notes)
    - Mark variants as primary
    - Delete variants
    - Compare variants side-by-side
    - View performance metrics
    """

    variant_created = pyqtSignal(int)  # Emits new variant ID
    variant_updated = pyqtSignal(int)  # Emits updated variant ID
    variant_deleted = pyqtSignal(int)  # Emits deleted variant ID

    def __init__(
        self,
        job_posting_id: int,
        current_variant_id: Optional[int] = None,
        parent: Optional[QWidget] = None
    ):
        """Initialize the variants dialog.

        Args:
            job_posting_id: ID of the job posting
            current_variant_id: ID of the currently active variant (if any)
            parent: Parent widget
        """
        super().__init__(parent)
        self.job_posting_id = job_posting_id
        self.current_variant_id = current_variant_id
        self.session = DatabaseManager.get_session()
        self.variant_service = ResumeVariantService(self.session)

        self.variants: List[TailoredResumeModel] = []
        self.selected_variant_id: Optional[int] = None

        self.setWindowTitle("Resume Variants")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)

        self._build_ui()
        self._load_variants()

    def _build_ui(self):
        """Build the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Resume Variants")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "Manage multiple versions of your tailored resume for this job posting. "
            "Create variants to test different approaches and track which works best."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        # Variants table
        variants_group = self._build_variants_section()
        layout.addWidget(variants_group)

        # Actions section
        actions_group = self._build_actions_section()
        layout.addWidget(actions_group)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _build_variants_section(self) -> QGroupBox:
        """Build the variants table section."""
        group = QGroupBox("Existing Variants")
        layout = QVBoxLayout()

        # Variants table
        self.variants_table = QTableWidget()
        self.variants_table.setColumnCount(6)
        self.variants_table.setHorizontalHeaderLabels([
            "Variant", "Created", "Match Score", "Coverage", "Primary", "Notes"
        ])

        # Configure table
        self.variants_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.variants_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.variants_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.variants_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.variants_table.itemSelectionChanged.connect(self._on_variant_selected)

        layout.addWidget(self.variants_table)

        group.setLayout(layout)
        return group

    def _build_actions_section(self) -> QGroupBox:
        """Build the actions section."""
        group = QGroupBox("Actions")
        layout = QVBoxLayout()

        # Create variant section
        create_layout = QHBoxLayout()

        create_label = QLabel("Create New Variant:")
        create_label.setStyleSheet("font-weight: bold;")
        create_layout.addWidget(create_label)

        self.strategy_combo = QComboBox()
        self.strategy_combo.setMinimumWidth(250)

        for strategy_name, strategy_info in VARIANT_STRATEGIES.items():
            self.strategy_combo.addItem(
                f"{strategy_name} - {strategy_info['description']}",
                strategy_name
            )

        create_layout.addWidget(self.strategy_combo)

        create_button = QPushButton("Create Variant")
        create_button.setStyleSheet("font-weight: bold; padding: 6px 12px;")
        create_button.clicked.connect(self._create_variant)
        create_layout.addWidget(create_button)

        create_layout.addStretch()
        layout.addLayout(create_layout)

        # Variant management buttons
        management_layout = QHBoxLayout()

        self.edit_button = QPushButton("Edit Notes")
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self._edit_variant_notes)
        management_layout.addWidget(self.edit_button)

        self.rename_button = QPushButton("Rename")
        self.rename_button.setEnabled(False)
        self.rename_button.clicked.connect(self._rename_variant)
        management_layout.addWidget(self.rename_button)

        self.primary_button = QPushButton("Mark as Primary")
        self.primary_button.setEnabled(False)
        self.primary_button.clicked.connect(self._mark_as_primary)
        management_layout.addWidget(self.primary_button)

        self.compare_button = QPushButton("Compare Variants")
        self.compare_button.setEnabled(False)
        self.compare_button.clicked.connect(self._compare_variants)
        management_layout.addWidget(self.compare_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._delete_variant)
        management_layout.addWidget(self.delete_button)

        management_layout.addStretch()
        layout.addLayout(management_layout)

        group.setLayout(layout)
        return group

    def _load_variants(self):
        """Load variants from the database."""
        self.variants = self.variant_service.list_variants(self.job_posting_id)
        self._populate_table()

        # Enable compare button if 2+ variants
        self.compare_button.setEnabled(len(self.variants) >= 2)

    def _populate_table(self):
        """Populate the variants table."""
        self.variants_table.setRowCount(len(self.variants))

        for row, variant in enumerate(self.variants):
            # Variant name
            name = variant.variant_name or f"Variant {variant.variant_number}"
            name_item = QTableWidgetItem(name)
            if variant.is_primary:
                name_item.setIcon(QIcon.fromTheme("starred"))
            self.variants_table.setItem(row, 0, name_item)

            # Created date
            created_str = variant.created_at.strftime("%Y-%m-%d %H:%M") if variant.created_at else "N/A"
            self.variants_table.setItem(row, 1, QTableWidgetItem(created_str))

            # Match score
            match_score = variant.formatted_match_score
            self.variants_table.setItem(row, 2, QTableWidgetItem(match_score))

            # Coverage
            coverage = variant.formatted_coverage
            self.variants_table.setItem(row, 3, QTableWidgetItem(coverage))

            # Primary indicator
            primary_text = "✓ Yes" if variant.is_primary else "No"
            primary_item = QTableWidgetItem(primary_text)
            if variant.is_primary:
                primary_item.setForeground(Qt.GlobalColor.darkGreen)
            self.variants_table.setItem(row, 4, primary_item)

            # Notes preview
            notes_preview = variant.notes[:50] + "..." if variant.notes and len(variant.notes) > 50 else (variant.notes or "")
            self.variants_table.setItem(row, 5, QTableWidgetItem(notes_preview))

            # Store variant ID in row data
            self.variants_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, variant.id)

    def _on_variant_selected(self):
        """Handle variant selection."""
        selected_rows = self.variants_table.selectedItems()

        if selected_rows:
            row = selected_rows[0].row()
            variant_id = self.variants_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.selected_variant_id = variant_id

            # Get the selected variant
            selected_variant = next((v for v in self.variants if v.id == variant_id), None)

            # Enable/disable buttons
            self.edit_button.setEnabled(True)
            self.rename_button.setEnabled(True)
            self.delete_button.setEnabled(len(self.variants) > 1)  # Can't delete last variant
            self.primary_button.setEnabled(selected_variant and not selected_variant.is_primary)
        else:
            self.selected_variant_id = None
            self.edit_button.setEnabled(False)
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.primary_button.setEnabled(False)

    def _create_variant(self):
        """Create a new variant."""
        strategy = self.strategy_combo.currentData()

        if not self.variants:
            QMessageBox.warning(
                self,
                "No Base Variant",
                "Cannot create variants - no base resume found for this job posting."
            )
            return

        # Get base variant (use primary or first variant)
        base_variant = next((v for v in self.variants if v.is_primary), self.variants[0])

        # Get variant name
        if strategy == "Custom":
            variant_name, ok = QInputDialog.getText(
                self,
                "Custom Variant Name",
                "Enter a name for your custom variant:"
            )
            if not ok or not variant_name.strip():
                return
            variant_name = variant_name.strip()
        else:
            # Check if strategy already exists
            existing = next((v for v in self.variants if v.variant_name == strategy), None)
            if existing:
                QMessageBox.warning(
                    self,
                    "Variant Exists",
                    f"A '{strategy}' variant already exists. Choose a different strategy or rename the existing variant."
                )
                return
            variant_name = strategy

        # Get strategy notes
        strategy_info = VARIANT_STRATEGIES.get(strategy, {})
        notes = strategy_info.get("notes", "")

        try:
            # Create the variant
            new_variant = self.variant_service.create_variant(
                base_resume_id=base_variant.id,
                variant_name=variant_name,
                notes=notes
            )

            QMessageBox.information(
                self,
                "Variant Created",
                f"Variant '{variant_name}' created successfully!\n\n"
                "You can now customize this variant's accomplishments and "
                "generate a PDF with different settings."
            )

            self._load_variants()
            self.variant_created.emit(new_variant.id)

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create variant: {e}")

    def _edit_variant_notes(self):
        """Edit the selected variant's notes."""
        if not self.selected_variant_id:
            return

        variant = next((v for v in self.variants if v.id == self.selected_variant_id), None)
        if not variant:
            return

        # Create notes editor dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Variant Notes")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(300)

        layout = QVBoxLayout(dialog)

        label = QLabel(f"Notes for: {variant.variant_name or f'Variant {variant.variant_number}'}")
        label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(label)

        notes_edit = QTextEdit()
        notes_edit.setPlainText(variant.notes or "")
        layout.addWidget(notes_edit)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_button = QPushButton("Save")
        save_button.clicked.connect(dialog.accept)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_notes = notes_edit.toPlainText()
            try:
                self.variant_service.update_variant(
                    variant_id=self.selected_variant_id,
                    notes=new_notes
                )
                self._load_variants()
                self.variant_updated.emit(self.selected_variant_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update notes: {e}")

    def _rename_variant(self):
        """Rename the selected variant."""
        if not self.selected_variant_id:
            return

        variant = next((v for v in self.variants if v.id == self.selected_variant_id), None)
        if not variant:
            return

        current_name = variant.variant_name or f"Variant {variant.variant_number}"

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Variant",
            "Enter new name:",
            text=current_name
        )

        if ok and new_name.strip():
            new_name = new_name.strip()

            # Check for duplicate
            if any(v.variant_name == new_name and v.id != self.selected_variant_id for v in self.variants):
                QMessageBox.warning(
                    self,
                    "Duplicate Name",
                    f"A variant named '{new_name}' already exists."
                )
                return

            try:
                self.variant_service.update_variant(
                    variant_id=self.selected_variant_id,
                    variant_name=new_name
                )
                self._load_variants()
                self.variant_updated.emit(self.selected_variant_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename variant: {e}")

    def _mark_as_primary(self):
        """Mark the selected variant as primary."""
        if not self.selected_variant_id:
            return

        variant = next((v for v in self.variants if v.id == self.selected_variant_id), None)
        if not variant:
            return

        try:
            self.variant_service.mark_as_primary(self.selected_variant_id)
            self._load_variants()
            self.variant_updated.emit(self.selected_variant_id)

            QMessageBox.information(
                self,
                "Primary Variant Updated",
                f"'{variant.variant_name or f'Variant {variant.variant_number}'}' is now the primary variant."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to mark as primary: {e}")

    def _compare_variants(self):
        """Show variant comparison."""
        if len(self.variants) < 2:
            QMessageBox.information(
                self,
                "Not Enough Variants",
                "You need at least 2 variants to compare."
            )
            return

        # For now, compare the first 2 or 3 variants
        # TODO: Add variant selector dialog
        variant_ids = [v.id for v in self.variants[:min(3, len(self.variants))]]

        try:
            comparison = self.variant_service.compare_variants(variant_ids)
            self._show_comparison_dialog(comparison)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to compare variants: {e}")

    def _show_comparison_dialog(self, comparison: VariantComparison):
        """Show the comparison results in a dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Variant Comparison")
        dialog.setMinimumWidth(700)
        dialog.setMinimumHeight(500)

        layout = QVBoxLayout(dialog)

        title = QLabel("Variant Comparison")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Create comparison text
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        comparison_text = self._format_comparison(comparison)
        text_edit.setPlainText(comparison_text)

        layout.addWidget(text_edit)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        dialog.exec()

    def _format_comparison(self, comparison: VariantComparison) -> str:
        """Format comparison data as text."""
        lines = []

        lines.append("=" * 80)
        lines.append("RESUME VARIANT COMPARISON")
        lines.append("=" * 80)
        lines.append("")

        # Variant summary
        lines.append("VARIANTS COMPARED:")
        for info in comparison.metadata["variants_info"]:
            primary_marker = " [PRIMARY]" if info["is_primary"] else ""
            lines.append(f"  • {info['name']} (#{info['variant_number']}){primary_marker}")
            lines.append(f"    Match Score: {info['match_score']}, Coverage: {(info['coverage_percentage'] or 0) * 100:.1f}%")
        lines.append("")

        # Accomplishment comparison
        lines.append("-" * 80)
        lines.append("ACCOMPLISHMENT COMPARISON:")
        lines.append("-" * 80)

        acc_diff = comparison.accomplishment_diffs
        lines.append(f"Common accomplishments across all variants: {len(acc_diff['common_accomplishments'])}")
        lines.append(f"Total unique accomplishments: {acc_diff['total_unique_accomplishments']}")
        lines.append("")

        for var_diff in acc_diff["by_variant"]:
            lines.append(f"{var_diff['variant_name']}:")
            lines.append(f"  Total accomplishments: {var_diff['total_accomplishments']}")
            lines.append(f"  Unique to this variant: {var_diff['unique_count']}")
        lines.append("")

        # Skill coverage comparison
        lines.append("-" * 80)
        lines.append("SKILL COVERAGE COMPARISON:")
        lines.append("-" * 80)

        for var_skill in comparison.skill_diffs["by_variant"]:
            lines.append(f"{var_skill['variant_name']}:")
            lines.append(f"  Coverage: {(var_skill['coverage_percentage'] or 0) * 100:.1f}%")
            lines.append(f"  Covered skills: {len(var_skill['covered_skills'])}")
            lines.append(f"  Missing skills: {len(var_skill['missing_skills'])}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _delete_variant(self):
        """Delete the selected variant."""
        if not self.selected_variant_id:
            return

        if len(self.variants) <= 1:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "Cannot delete the only variant for this job posting."
            )
            return

        variant = next((v for v in self.variants if v.id == self.selected_variant_id), None)
        if not variant:
            return

        variant_name = variant.variant_name or f"Variant {variant.variant_number}"

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{variant_name}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.variant_service.delete_variant(self.selected_variant_id)
                deleted_id = self.selected_variant_id
                self._load_variants()
                self.variant_deleted.emit(deleted_id)

                QMessageBox.information(
                    self,
                    "Variant Deleted",
                    f"'{variant_name}' has been deleted."
                )
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete variant: {e}")

    def get_selected_variant_id(self) -> Optional[int]:
        """Get the ID of the currently selected variant.

        Returns:
            Variant ID or None if no selection
        """
        return self.selected_variant_id
