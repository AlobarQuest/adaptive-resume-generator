"""Bullet Point Enhancement Dialog.

This dialog provides a user interface for enhancing resume bullet points using
either rule-based templates or AI-powered suggestions. It integrates with both
the BulletEnhancer and AIEnhancementService to provide multiple enhancement options.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QRadioButton, QButtonGroup, QLineEdit,
    QFormLayout, QGroupBox, QTabWidget, QWidget, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, QCoreApplication
from typing import Optional
from adaptive_resume.services.bullet_enhancer import BulletEnhancer
from adaptive_resume.services.ai_enhancement_service import AIEnhancementService
from adaptive_resume.config.settings import Settings


class BulletEnhancementDialog(QDialog):
    """Dialog for enhancing bullet points using templates or AI.
    
    This dialog provides two enhancement methods:
    1. Template-based: User selects a category and fills in guided prompts
    2. AI-powered: Claude generates 3 professional variations (requires API key)
    
    Attributes:
        original_text: The original bullet point text to enhance
        enhanced_text: The final enhanced text after user accepts
        enhancer: BulletEnhancer instance for template-based enhancement
        ai_service: AIEnhancementService instance for AI enhancement
        settings: Settings instance for checking AI availability
    """
    
    def __init__(self, original_text: str, parent=None):
        """Initialize the enhancement dialog.
        
        Args:
            original_text: The bullet point text to enhance
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.original_text = original_text
        self.enhanced_text = None
        self.settings = Settings()
        
        self.enhancer = BulletEnhancer()
        self.ai_service = AIEnhancementService()
        
        self.setWindowTitle("Enhance Bullet Point")
        self.setModal(True)
        self.setMinimumWidth(800)
        self.setMinimumHeight(700)
        
        self._create_ui()
        self._analyze_original()
    
    def _create_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Enhance Your Bullet Point")
        header.setObjectName("headerLabel")
        layout.addWidget(header)
        
        # Original bullet display
        original_group = QGroupBox("Original Bullet")
        original_layout = QVBoxLayout()
        self.original_label = QLabel(self.original_text)
        self.original_label.setWordWrap(True)
        self.original_label.setStyleSheet(
            "padding: 12px; "
            "background: #2a3f5f; "
            "border-radius: 4px; "
            "color: #e0e0e0; "
            "font-size: 12px;"
        )
        original_layout.addWidget(self.original_label)
        original_group.setLayout(original_layout)
        layout.addWidget(original_group)
        
        # Tab widget for rule-based vs AI
        self.tabs = QTabWidget()
        
        # Rule-based tab
        rule_widget = self._create_rule_based_tab()
        self.tabs.addTab(rule_widget, "📝 Template-Based")
        
        # AI tab (if enabled)
        if self.ai_service.is_available:
            ai_widget = self._create_ai_tab()
            self.tabs.addTab(ai_widget, "🤖 AI-Powered")
        else:
            # Show placeholder if AI not enabled
            placeholder_widget = self._create_ai_placeholder()
            self.tabs.addTab(placeholder_widget, "🤖 AI-Powered (Disabled)")
        
        layout.addWidget(self.tabs)
        
        # Preview section
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(100)
        self.preview_text.setPlaceholderText("Your enhanced bullet will appear here...")
        self.preview_text.textChanged.connect(self._on_preview_changed)
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply Enhancement")
        self.apply_btn.clicked.connect(self._on_apply)
        self.apply_btn.setEnabled(False)
        self.apply_btn.setDefault(True)
        button_layout.addWidget(self.apply_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_rule_based_tab(self) -> QWidget:
        """Create the rule-based enhancement tab.
        
        Returns:
            Widget containing template selection and guided prompts
        """
        # Create scroll area for the tab content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        instructions = QLabel(
            "Choose a template category that best matches your bullet point. "
            "Then fill in the guided prompts to generate a professional version."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #ccc; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Category selection
        category_group = QGroupBox("Select Template Category")
        category_layout = QVBoxLayout()
        
        self.category_buttons = QButtonGroup()
        for idx, (key, template) in enumerate(self.enhancer.TEMPLATES.items()):
            rb = QRadioButton(f"{template.category}")
            rb.setProperty('category', key)
            self.category_buttons.addButton(rb, idx)
            category_layout.addWidget(rb)
            
            # Add example
            example_label = QLabel(f"   Example: {template.example}")
            example_label.setWordWrap(True)
            example_label.setStyleSheet(
                "color: #888; "
                "font-size: 10px; "
                "margin-left: 20px; "
                "margin-bottom: 8px;"
            )
            category_layout.addWidget(example_label)
        
        self.category_buttons.buttonClicked.connect(self._on_category_selected)
        
        category_group.setLayout(category_layout)
        layout.addWidget(category_group)
        
        # Guided prompts section
        self.prompts_group = QGroupBox("Fill in the Details")
        self.prompts_layout = QFormLayout()
        self.prompt_inputs = {}
        self.prompts_group.setLayout(self.prompts_layout)
        self.prompts_group.setVisible(False)
        layout.addWidget(self.prompts_group)
        
        # Generate button
        generate_btn = QPushButton("📝 Generate Preview")
        generate_btn.clicked.connect(self._generate_rule_based)
        generate_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        layout.addWidget(generate_btn)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def _create_ai_tab(self) -> QWidget:
        """Create the AI enhancement tab.
        
        Returns:
            Widget containing AI generation controls and suggestions display
        """
        # Create scroll area for the tab content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info
        info = QLabel(
            "AI will analyze your bullet and provide 3 professionally-enhanced "
            "versions following resume writing best practices. Each version "
            "emphasizes different aspects of your achievement."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #ccc; margin-bottom: 15px;")
        layout.addWidget(info)
        
        # Generate button
        generate_ai_btn = QPushButton("🤖 Generate AI Suggestions")
        generate_ai_btn.clicked.connect(self._generate_ai_suggestions)
        generate_ai_btn.setStyleSheet(
            "padding: 10px; "
            "font-weight: bold; "
            "background-color: #4a90e2; "
            "color: white;"
        )
        layout.addWidget(generate_ai_btn)
        
        # Suggestions area
        self.suggestions_group = QGroupBox("AI Suggestions")
        self.suggestions_layout = QVBoxLayout()
        self.suggestion_buttons = QButtonGroup()
        self.suggestions_group.setLayout(self.suggestions_layout)
        self.suggestions_group.setVisible(False)
        layout.addWidget(self.suggestions_group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def _create_ai_placeholder(self) -> QWidget:
        """Create placeholder for disabled AI tab.
        
        Returns:
            Widget explaining how to enable AI enhancement
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon = QLabel("🔒")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel("AI Enhancement Not Enabled")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        message = QLabel(
            "To use AI-powered bullet enhancement, you need to:\n\n"
            "1. Get an Anthropic API key from console.anthropic.com\n"
            "2. Go to Settings > Preferences\n"
            "3. Enable AI Enhancement and enter your API key\n\n"
            "You'll still have full access to template-based enhancement!"
        )
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("color: #ccc; padding: 20px;")
        layout.addWidget(message)
        
        settings_btn = QPushButton("Open Settings")
        settings_btn.clicked.connect(self._open_settings)
        settings_btn.setMaximumWidth(150)
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        
        return widget
    
    def _analyze_original(self):
        """Analyze the original bullet and pre-select category."""
        category, confidence = self.enhancer.analyze_bullet(self.original_text)
        
        # Pre-select the suggested category
        for button in self.category_buttons.buttons():
            if button.property('category') == category:
                button.setChecked(True)
                self._on_category_selected(button)
                break
    
    def _on_category_selected(self, button):
        """Handle category selection.
        
        Args:
            button: The radio button that was clicked
        """
        category = button.property('category')
        template = self.enhancer.get_template(category)
        
        # Clear previous prompts
        while self.prompts_layout.count():
            child = self.prompts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.prompt_inputs.clear()
        
        # Create input fields for prompts
        for key, prompt_text in template.prompts.items():
            label = QLabel(prompt_text)
            label.setWordWrap(True)
            input_field = QLineEdit()
            input_field.setPlaceholderText("Enter details...")
            self.prompt_inputs[key] = input_field
            self.prompts_layout.addRow(label, input_field)
        
        self.prompts_group.setVisible(True)
        
        # Try to pre-fill from original
        extracted = self.enhancer.extract_existing_info(self.original_text)
        if 'action_verb' in extracted:
            # Try to find a matching input field
            for key in ['action', 'led', 'built', 'identified', 'streamlined']:
                if key in self.prompt_inputs:
                    self.prompt_inputs[key].setText(extracted['action_verb'])
                    break
    
    def _generate_rule_based(self):
        """Generate enhanced bullet from template."""
        # Get selected category
        selected_button = self.category_buttons.checkedButton()
        if not selected_button:
            QMessageBox.warning(
                self,
                "No Category Selected",
                "Please select a template category first."
            )
            return
        
        category = selected_button.property('category')
        
        # Collect responses
        responses = {}
        has_content = False
        for key, input_field in self.prompt_inputs.items():
            text = input_field.text().strip()
            responses[key] = text
            if text:
                has_content = True
        
        if not has_content:
            QMessageBox.warning(
                self,
                "No Details Provided",
                "Please fill in at least one detail field."
            )
            return
        
        # Generate enhanced bullet
        enhanced = self.enhancer.generate_enhanced_bullet(category, responses)
        
        # Update preview
        self.preview_text.setPlainText(enhanced)
        self.enhanced_text = enhanced
    
    def _generate_ai_suggestions(self):
        """Generate AI-powered suggestions."""
        # Clear previous suggestions
        while self.suggestions_layout.count():
            child = self.suggestions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Show loading
        loading_label = QLabel("🔄 Generating AI suggestions...")
        loading_label.setStyleSheet("font-size: 14px; color: #4a90e2; padding: 10px;")
        self.suggestions_layout.addWidget(loading_label)
        self.suggestions_group.setVisible(True)
        
        # Process events to show loading
        QCoreApplication.processEvents()
        
        # Get AI suggestions
        suggestions = self.ai_service.enhance_bullet(self.original_text)
        
        # Remove loading label
        loading_label.deleteLater()
        
        if not suggestions:
            error_label = QLabel(
                "❌ Could not generate suggestions.\n\n"
                "This could be due to:\n"
                "• Invalid API key\n"
                "• Network connectivity issues\n"
                "• API rate limits\n\n"
                "Please check your Settings and try again."
            )
            error_label.setWordWrap(True)
            error_label.setStyleSheet("color: #ff4444; padding: 10px;")
            self.suggestions_layout.addWidget(error_label)
            return
        
        # Display suggestions
        for idx, suggestion in enumerate(suggestions):
            rb = QRadioButton()
            rb.setProperty('text', suggestion['text'])
            self.suggestion_buttons.addButton(rb, idx)
            
            suggestion_widget = QWidget()
            suggestion_layout = QVBoxLayout(suggestion_widget)
            suggestion_layout.setContentsMargins(0, 0, 0, 10)
            
            # Header with focus
            header = QLabel(f"<b>Option {idx + 1}:</b> {suggestion['focus']}")
            header.setStyleSheet("color: #4a90e2; font-size: 11px;")
            suggestion_layout.addWidget(header)
            
            # Text
            text_label = QLabel(suggestion['text'])
            text_label.setWordWrap(True)
            text_label.setStyleSheet(
                "padding: 10px; "
                "background: #2a3f5f; "
                "border-radius: 4px; "
                "color: #e0e0e0; "
                "font-size: 12px;"
            )
            suggestion_layout.addWidget(text_label)
            
            # Placeholders if any
            if suggestion.get('placeholders'):
                placeholders_text = "⚠️ You may need to fill in: " + ", ".join(suggestion['placeholders'])
                placeholders_label = QLabel(placeholders_text)
                placeholders_label.setWordWrap(True)
                placeholders_label.setStyleSheet("color: orange; font-size: 10px; padding: 5px;")
                suggestion_layout.addWidget(placeholders_label)
            
            # Add radio button and content
            row_layout = QHBoxLayout()
            row_layout.addWidget(rb)
            row_layout.addWidget(suggestion_widget)
            row_layout.addStretch()
            
            container = QWidget()
            container.setLayout(row_layout)
            self.suggestions_layout.addWidget(container)
        
        # Connect selection to preview
        self.suggestion_buttons.buttonClicked.connect(self._on_ai_suggestion_selected)
    
    def _on_ai_suggestion_selected(self, button):
        """Handle AI suggestion selection.
        
        Args:
            button: The radio button that was clicked
        """
        text = button.property('text')
        self.preview_text.setPlainText(text)
        self.enhanced_text = text
    
    def _on_preview_changed(self):
        """Handle changes to preview text."""
        # Enable apply button if preview has content
        has_content = bool(self.preview_text.toPlainText().strip())
        self.apply_btn.setEnabled(has_content)
    
    def _on_apply(self):
        """Apply the enhancement."""
        self.enhanced_text = self.preview_text.toPlainText().strip()
        if self.enhanced_text:
            self.accept()
    
    def _open_settings(self):
        """Open settings dialog."""
        from adaptive_resume.gui.dialogs.settings_dialog import SettingsDialog
        dialog = SettingsDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload AI service to check if it's now enabled
            self.ai_service = AIEnhancementService()
            if self.ai_service.is_available:
                QMessageBox.information(
                    self,
                    "AI Enabled",
                    "AI Enhancement is now enabled! Close this dialog and open "
                    "it again to access AI-powered suggestions."
                )
    
    def get_enhanced_text(self) -> Optional[str]:
        """Get the enhanced bullet text.
        
        Returns:
            Enhanced text if accepted, None otherwise
        """
        return self.enhanced_text
