"""Settings dialog for application preferences."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QLabel, QCheckBox, QGroupBox, QHBoxLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt
from adaptive_resume.config.settings import Settings


class SettingsDialog(QDialog):
    """Dialog for managing application settings."""
    
    def __init__(self, parent=None):
        """
        Initialize settings dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings = Settings()
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        self._create_ui()
        self._load_settings()
    
    def _create_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)
        
        # AI Enhancement Section
        ai_group = QGroupBox("AI Enhancement (Optional)")
        ai_layout = QVBoxLayout()
        
        # Info text
        info_label = QLabel(
            "Enable AI-powered bullet point enhancement using Claude.\n"
            "You'll need your own Anthropic API key.\n"
            "Get one at: https://console.anthropic.com/"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #ccc; padding: 10px;")
        ai_layout.addWidget(info_label)
        
        # API Key input (moved above checkbox)
        form = QFormLayout()
        form.setSpacing(15)
        
        api_key_label = QLabel("Anthropic API Key:")
        api_key_label.setStyleSheet("font-weight: bold;")
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-ant-api03-...")
        self.api_key_input.setMinimumWidth(400)
        
        form.addRow(api_key_label, self.api_key_input)
        ai_layout.addLayout(form)
        
        # Test connection button
        test_btn = QPushButton("Test Connection")
        test_btn.setMaximumWidth(150)
        test_btn.clicked.connect(self._test_api_key)
        ai_layout.addWidget(test_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        ai_layout.addWidget(self.status_label)
        
        # Enable checkbox (moved below API key input)
        self.ai_enabled_cb = QCheckBox("Enable AI Enhancement")
        self.ai_enabled_cb.setStyleSheet("font-weight: bold; margin-top: 15px;")
        ai_layout.addWidget(self.ai_enabled_cb)
        
        enable_note = QLabel(
            "Note: Your API key is saved whether or not AI enhancement is enabled.\n"
            "You can enable/disable this feature at any time without re-entering your key."
        )
        enable_note.setWordWrap(True)
        enable_note.setStyleSheet("color: #888; font-size: 11px; margin-left: 20px;")
        ai_layout.addWidget(enable_note)
        
        # Security note
        security_note = QLabel(
            "🔒 Your API key is encrypted and stored securely on your computer.\n"
            "It is never transmitted except to Anthropic's API when you use AI enhancement."
        )
        security_note.setWordWrap(True)
        security_note.setStyleSheet("color: #888; font-size: 11px; padding: 10px; background: #1a2332; border-radius: 4px; margin-top: 10px;")
        ai_layout.addWidget(security_note)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        clear_btn = QPushButton("Clear API Key")
        clear_btn.clicked.connect(self._clear_api_key)
        button_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _load_settings(self):
        """Load current settings into UI."""
        # Load the enable checkbox state
        self.ai_enabled_cb.setChecked(self.settings.ai_enabled)
        
        # Load API key (if exists, show masked)
        api_key = self.settings.get_api_key()
        if api_key:
            self.api_key_input.setText("••••••••••••••••")
            self.api_key_input.setPlaceholderText("(API key is set)")
    
    def _test_api_key(self):
        """Test the API key connection."""
        api_key = self.api_key_input.text().strip()
        
        # If showing masked text, get actual key from storage
        if api_key == "••••••••••••••••":
            api_key = self.settings.get_api_key()
        
        if not api_key or len(api_key) < 10:
            self.status_label.setText("⚠️ Please enter an API key to test")
            self.status_label.setStyleSheet("color: orange;")
            return
        
        self.status_label.setText("🔄 Testing connection...")
        self.status_label.setStyleSheet("color: #4a90e2;")
        
        # Process events to show loading message
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        # Test with actual API call
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=api_key)
            
            # Make a minimal API call to test
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            
            if response.content:
                self.status_label.setText("✅ Connection successful! API key is valid.")
                self.status_label.setStyleSheet("color: #4ade80;")
            else:
                self.status_label.setText("❌ Connection failed. Invalid response.")
                self.status_label.setStyleSheet("color: #ff4444;")
                
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                self.status_label.setText("❌ Invalid API key. Please check and try again.")
            else:
                self.status_label.setText(f"❌ Connection failed: {error_msg[:100]}")
            self.status_label.setStyleSheet("color: #ff4444;")
    
    def _clear_api_key(self):
        """Clear the stored API key."""
        reply = QMessageBox.question(
            self,
            "Clear API Key",
            "Are you sure you want to remove your API key?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.clear_api_key()
            self.api_key_input.clear()
            self.api_key_input.setPlaceholderText("sk-ant-api03-...")
            self.status_label.setText("✅ API key cleared.")
            self.status_label.setStyleSheet("color: #4ade80;")
    
    def _on_save(self):
        """Save settings."""
        api_key = self.api_key_input.text().strip()
        
        try:
            # Save API key if provided (independent of checkbox)
            if api_key and api_key != "••••••••••••••••":
                # User entered a new key
                if len(api_key) >= 10:
                    print(f"[DEBUG] Saving new API key (length: {len(api_key)})")
                    self.settings.set_api_key(api_key)
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid API Key",
                        "API key must be at least 10 characters long."
                    )
                    return
            # If masked text (••••••), key is already saved, do nothing
            
            # Save the enable/disable state (independent of API key)
            self.settings.set('ai_enhancement_enabled', self.ai_enabled_cb.isChecked())
            self.settings.save()
            
            # Show success message
            msg = "Your settings have been saved successfully.\n\n"
            if self.settings.get_api_key():
                msg += "✓ API key is stored (encrypted)\n"
            if self.ai_enabled_cb.isChecked():
                msg += "✓ AI enhancement is enabled"
            else:
                msg += "✓ AI enhancement is disabled"
            
            QMessageBox.information(
                self,
                "Settings Saved",
                msg
            )
            self.accept()
            
        except Exception as e:
            print(f"[ERROR] Failed to save settings: {e}")
            import traceback
            traceback.print_exc()
            
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save settings:\n{str(e)}"
            )
