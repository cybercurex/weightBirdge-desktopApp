# ui/dialogs/settings_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton, 
                            QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.components.styled_components import RoundedButton

class SettingsDialog(QDialog):
    settings_updated = pyqtSignal(int, str, dict)  # row, service_name, settings dict

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Service Settings")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Form layout
        form = QFormLayout()
        form.setSpacing(15)

        # Serial Port
        self.port_combo = QComboBox()
        self.port_combo.addItems(["COM1", "COM2", "COM3", "COM4"])
        form.addRow("Serial Port:", self.port_combo)

        # Baud Rate
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        form.addRow("Baud Rate:", self.baud_combo)

        # API Port
        self.api_port_edit = QLineEdit()
        form.addRow("API Port:", self.api_port_edit)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = RoundedButton("Save")
        self.cancel_btn = RoundedButton("Cancel")

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        # Connect signals
        self.save_btn.clicked.connect(self.emit_settings_updated)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Load current settings
        self.load_settings()

    def emit_settings_updated(self):
        settings = self.get_settings()
        # row and service_name are not available here, so emit with placeholders
        self.settings_updated.emit(-1, "Service", settings)
    
    def load_settings(self):
        self.port_combo.setCurrentText(self.config.get('default_com_port', 'COM3'))
        self.baud_combo.setCurrentText(str(self.config.get('default_baudrate', '9600')))
        self.api_port_edit.setText(str(self.config.get('flask_port', '5000')))

    def get_settings(self):
        return {
            'default_com_port': self.port_combo.currentText(),
            'default_baudrate': int(self.baud_combo.currentText()),
            'flask_port': int(self.api_port_edit.text())
        }