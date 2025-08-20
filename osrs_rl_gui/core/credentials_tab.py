"""Credentials management tab component."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import pyqtSignal, Signal
import logging

from .secure_storage import SecureCredentialStore

logger = logging.getLogger(__name__)


class CredentialsTab(QWidget):
    """Widget for managing bot credentials securely."""
    
    # Signal emitted when credentials are updated
    credentials_updated = Signal(str, str)  # username, password
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.secure_store = SecureCredentialStore()
        self.setup_ui()
        self.load_credentials()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Bot Credentials GroupBox
        credentials_group = QGroupBox("Bot Credentials")
        credentials_layout = QFormLayout(credentials_group)
        
        # Username field
        self.username_line_edit = QLineEdit()
        self.username_line_edit.setPlaceholderText("Enter bot username")
        credentials_layout.addRow("Username:", self.username_line_edit)
        
        # Password field
        self.password_line_edit = QLineEdit()
        self.password_line_edit.setPlaceholderText("Enter bot password")
        self.password_line_edit.setEchoMode(QLineEdit.Password)
        credentials_layout.addRow("Password:", self.password_line_edit)
        
        layout.addWidget(credentials_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Credentials")
        self.save_button.clicked.connect(self.save_credentials)
        button_layout.addWidget(self.save_button)
        
        self.clear_button = QPushButton("Clear Credentials")
        self.clear_button.clicked.connect(self.clear_credentials)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        
        # Security notice
        security_label = QLabel(
            "Note: Credentials are now encrypted and stored securely on your system."
        )
        security_label.setWordWrap(True)
        security_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(security_label)
        
        layout.addStretch()
    
    def load_credentials(self):
        """Load stored credentials."""
        try:
            credentials = self.secure_store.retrieve_credentials()
            if credentials:
                username, password = credentials
                self.username_line_edit.setText(username)
                self.password_line_edit.setText(password)
                logger.info("Loaded stored credentials")
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            QMessageBox.warning(
                self,
                "Load Error", 
                f"Failed to load stored credentials: {e}"
            )
    
    def save_credentials(self):
        """Save credentials securely."""
        username = self.username_line_edit.text().strip()
        password = self.password_line_edit.text()
        
        if not username or not password:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter both username and password."
            )
            return
        
        try:
            self.secure_store.store_credentials(username, password)
            QMessageBox.information(
                self,
                "Credentials Saved",
                "Credentials have been encrypted and saved securely."
            )
            
            # Emit signal for other components
            self.credentials_updated.emit(username, password)
            logger.info("Credentials saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save credentials: {e}"
            )
    
    def clear_credentials(self):
        """Clear stored credentials."""
        reply = QMessageBox.question(
            self,
            "Clear Credentials",
            "Are you sure you want to clear stored credentials?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.secure_store.clear_credentials()
                self.username_line_edit.clear()
                self.password_line_edit.clear()
                
                QMessageBox.information(
                    self,
                    "Credentials Cleared", 
                    "Stored credentials have been cleared."
                )
                logger.info("Credentials cleared")
                
            except Exception as e:
                logger.error(f"Failed to clear credentials: {e}")
                QMessageBox.critical(
                    self,
                    "Clear Error",
                    f"Failed to clear credentials: {e}"
                )
    
    def get_credentials(self):
        """Get current credentials from the form."""
        return (
            self.username_line_edit.text().strip(),
            self.password_line_edit.text()
        )